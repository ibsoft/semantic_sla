from collections import OrderedDict
import json
import logging
import os
import time
from elasticsearch import Elasticsearch
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from .models import db, User
from .utils import search_sla, get_embedding, generate_document_hash, extract_text_with_ocr, extract_text_from_pdf
from . import redis_client
from datetime import timedelta
from .config import Config
import hashlib
import zipfile
from datetime import datetime
from flask import send_file
from elasticsearch import helpers



logger = logging.getLogger()

es = Elasticsearch(Config.ELASTICSEARCH_URL)

api_bp = Blueprint('api', __name__)


@api_bp.route('/register', methods=['POST'])
def register_user():
    logging.info("Register endpoint accessed")
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        logging.warning("Missing username or password in registration request")
        return jsonify({"msg": "Missing username or password"}), 400

    # Check if the user already exists
    user = User.query.filter_by(username=username).first()
    if user:
        logging.warning(
            f"User registration failed: User '{username}' already exists")
        return jsonify({"msg": "User already exists"}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    logging.info(f"User '{username}' registered successfully")
    return jsonify({"msg": "User registered successfully"}), 201


@api_bp.route('/login', methods=['POST'])
def login_user():
    logging.info("Login endpoint accessed")
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        logging.warning(f"Invalid login attempt for username '{username}'")
        return jsonify({"msg": "Invalid credentials"}), 401

    # Generate JWT token
    access_token = create_access_token(
        identity=username, expires_delta=timedelta(seconds=Config.JWT_EXPIRATION))
    logging.info(f"User '{username}' logged in successfully")
    return jsonify(access_token=access_token)

@api_bp.route('/check-sla', methods=['POST'])
@jwt_required()
def check_sla():
    """
    Endpoint to check if the SLA is met based on the provided title and message.
    The response will include information about whether the SLA was violated and if a penalty applies.
    """
    logging.info("SLA Check endpoint accessed")
    user_identity = get_jwt_identity()  # This can be logged for debugging if necessary
    logging.debug(f"User identity: {user_identity}")

    # Retrieve the problem title and message from the user
    data = request.get_json()
    title = data.get("title")
    message = data.get("message")

    # Validate input
    if not title or not message:
        logging.warning("Missing title or message in SLA check request")
        return jsonify({"msg": "Title and message are required"}), 400

    try:
        # Call the search_sla function to search for relevant documents based on title and message
        result, cache_hit, elapsed_time = search_sla(f"{title} {message}", es)

        if "msg" in result:
            logging.error(f"Error in SLA search: {result['msg']}")
            return jsonify(result), 500  # Return error message if there's an issue

        sla_info = result.get("solution", "No SLA found")

        # Ensure correct encoding of the message, handling the Unicode issue
        message_decoded = message.encode('utf-8').decode('unicode_escape')

        # Check if the SLA has been violated based on the message
        sla_violated = "Penalty" if "delay" in message.lower() else "No penalty"

        # Prepare the response
        response_data = {
            "title": title,
            "message": message_decoded,  # Include the decoded message
            "sla_info": sla_info,
            #"sla_violated": sla_violated,
            "cache_hit": cache_hit,
            "elapsed_time": elapsed_time
        }

        return jsonify(response_data), 200

    except Exception as e:
        logging.error(f"Error checking SLA: {str(e)}")
        return jsonify({"msg": f"Error checking SLA: {str(e)}"}), 500




@api_bp.route('/upload-documents', methods=['POST'])
@jwt_required()
def upload_documents():
    """
    Endpoint to upload documents to Elasticsearch with embeddings.
    Supports both plain text and PDF documents.
    """
    try:
        tc_doc_id = request.form.get("tc_doc_id")
        if not tc_doc_id:
            return jsonify({"msg": "TotalCare Doc ID is required."}), 400

        # Check if a document with the same tc_doc_id already exists
        search_body = {"query": {"match": {"tc_doc_id": tc_doc_id}}}
        response = es.search(index="pdf_documents", body=search_body)

        if response["hits"]["hits"]:
            return jsonify({"msg": f"Document with tc_doc_id {tc_doc_id} already exists."}), 409

        files = request.files.getlist("files")
        if not files:
            return jsonify({"msg": "No files uploaded."}), 400

        for file in files:
            if not file.filename.endswith(".pdf"):
                return jsonify({"msg": f"Unsupported file type: {file.filename}"}), 400

            file_path = f"/tmp/{file.filename}"
            file.save(file_path)

            text = extract_text_from_pdf(file_path)
            if not text:
                return jsonify({"msg": f"Failed to extract text from {file.filename}"}), 500

            embedding = get_embedding(text)
            if not embedding:
                return jsonify({"msg": f"Failed to generate embedding for {file.filename}"}), 500

            document = {
                "tc_doc_id": tc_doc_id,
                "title": file.filename,
                "content": text,
                "hash": generate_document_hash({"title": file.filename, "content": text}),
                "timestamp": datetime.now().isoformat(),
                "embedding": embedding
            }

            es.index(index="pdf_documents", document=document)

        return jsonify({"msg": "Documents uploaded and indexed successfully."}), 201

    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        return jsonify({"msg": f"Error uploading documents: {str(e)}"}), 500



@api_bp.route('/delete-document', methods=['DELETE'])
@jwt_required()
def delete_document():
    """
    Endpoint to delete a document from Elasticsearch by TotalCare Document ID (tc_doc_id).
    """
    try:
        # Get the TotalCare Document ID from the request
        tc_doc_id = request.args.get("tc_doc_id")
        if not tc_doc_id:
            return jsonify({"msg": "TotalCare Doc ID is required."}), 400

        # Search for the document by tc_doc_id
        search_body = {"query": {"match": {"tc_doc_id": tc_doc_id}}}
        response = es.search(index="pdf_documents", body=search_body)

        if not response['hits']['hits']:
            return jsonify({"msg": f"No document found with tc_doc_id: {tc_doc_id}"}), 404

        # Delete the document(s)
        for hit in response['hits']['hits']:
            es.delete(index="pdf_documents", id=hit['_id'])

        return jsonify({"msg": f"Document with tc_doc_id {tc_doc_id} deleted successfully."}), 200

    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return jsonify({"msg": f"Error deleting document: {str(e)}"}), 500


@api_bp.route('/update-document', methods=['PUT'])
@jwt_required()
def update_document():
    """
    Endpoint to update a document in Elasticsearch by TotalCare Document ID (tc_doc_id).
    """
    try:
        tc_doc_id = request.form.get("tc_doc_id")
        if not tc_doc_id:
            return jsonify({"msg": "TotalCare Doc ID is required."}), 400

        files = request.files.getlist("files")
        if not files or len(files) != 1:
            return jsonify({"msg": "Exactly one file must be uploaded for updating."}), 400

        file = files[0]
        if not file.filename.endswith(".pdf"):
            return jsonify({"msg": f"Unsupported file type: {file.filename}"}), 400

        file_path = f"/tmp/{file.filename}"
        file.save(file_path)

        text = extract_text_from_pdf(file_path)
        if not text:
            return jsonify({"msg": f"Failed to extract text from {file.filename}"}), 500

        embedding = get_embedding(text)
        if not embedding:
            return jsonify({"msg": f"Failed to generate embedding for {file.filename}"}), 500

        search_body = {"query": {"match": {"tc_doc_id": tc_doc_id}}}
        response = es.search(index="pdf_documents", body=search_body)

        if not response['hits']['hits']:
            return jsonify({"msg": f"No document found with tc_doc_id: {tc_doc_id}"}), 404

        for hit in response['hits']['hits']:
            es.update(index="pdf_documents", id=hit['_id'], body={
                "doc": {
                    "title": file.filename,
                    "content": text,
                    "hash": generate_document_hash({"title": file.filename, "content": text}),
                    "timestamp": datetime.now().isoformat(),
                    "embedding": embedding
                }
            })

        return jsonify({"msg": f"Document with tc_doc_id {tc_doc_id} updated successfully."}), 200

    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        return jsonify({"msg": f"Error updating document: {str(e)}"}), 500


@api_bp.route('/backup-index', methods=['GET'])
@jwt_required()
def backup_index():
    """
    Backup Elasticsearch index and provide a downloadable ZIP file.
    """
    logging.info("Memory endpoint accessed")
    index_name = request.args.get("index", "default_index")  # Optional query param
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Define temporary directories and file names
    tmp_dir = "/tmp"
    backup_filename = f"backup_{index_name}_{timestamp}.json"
    zip_filename = f"{backup_filename}.zip"
    
    # Paths for the temporary backup and zip files
    backup_file_path = os.path.join(tmp_dir, backup_filename)
    zip_file_path = os.path.join(tmp_dir, zip_filename)

    try:
        # Query Elasticsearch for the index data
        query = {"query": {"match_all": {}}}
        results = helpers.scan(es, index=index_name, query=query)

        # Save the results to a JSON file in the tmp folder
        with open(backup_file_path, "w") as backup_file:
            for doc in results:
                backup_file.write(json.dumps(doc) + "\n")

        # Create a ZIP file for the JSON backup in the tmp folder
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(backup_file_path, arcname=backup_filename)

        # Serve the ZIP file as a downloadable response
        return send_file(zip_file_path, as_attachment=True, download_name=zip_filename)

    except Exception as e:
        logging.error(f"Error backing up index '{index_name}': {str(e)}")
        return jsonify({"msg": f"Error backing up index: {str(e)}"}), 500

    finally:
        # Clean up the temporary files after sending the response
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
