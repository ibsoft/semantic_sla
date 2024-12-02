import argparse
import hashlib
import requests
import json
from elasticsearch import Elasticsearch
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

# Elasticsearch setup
es = Elasticsearch(["http://localhost:9200"])

# Ollama API setup
OLLAMA_API_URL = "http://localhost:11434/api/embeddings"
OLLAMA_MODEL = "paraphrase-multilingual"


def get_embedding(text):
    """
    Fetch embedding for the given text using Ollama API.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"model": OLLAMA_MODEL, "prompt": text}
    try:
        response = requests.post(
            OLLAMA_API_URL, headers=headers, json=payload, timeout=30
        )
        response.raise_for_status()
        response_json = response.json()
        return response_json.get("embedding", None)
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except (json.decoder.JSONDecodeError, KeyError):
        print("Error decoding JSON response or missing 'embedding' key.")
        return None

# Generate a hash for deduplication
def generate_document_hash(doc):
    hash_source = f"{doc['title']}{doc['content']}"
    return hashlib.md5(hash_source.encode()).hexdigest()


def create_index():
    """
    Create an Elasticsearch index with mappings for dense vector and custom fields.
    """
    index_mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"},
                "hash": {"type": "text"},
                "category": {"type": "keyword"},
                "embedding": {"type": "dense_vector", "dims": 768},
                "custom_fields": {"type": "object"},
            }
        }
    }
    # Delete index if it exists
    es.options(ignore_status=[400, 404]).indices.delete(index="pdf_documents")
    es.options(ignore_status=[400]).indices.create(index="pdf_documents", body=index_mapping)


def extract_text_with_ocr(pdf_path):
    """
    Extract text from PDF using OCR as a fallback with support for Greek and English.
    """
    try:
        pages = convert_from_path(pdf_path, dpi=300)
        text = ""
        for page in pages:
            # OCR with both Greek (ell) and English (eng) language support
            text += pytesseract.image_to_string(page, lang="ell+eng")
        return text.strip()
    except Exception as e:
        print(f"Failed to extract text using OCR from {pdf_path}: {e}")
        return None


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file, with OCR fallback.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text
        if not text.strip():
            print(f"No selectable text found in {pdf_path}. Falling back to OCR.")
            return extract_text_with_ocr(pdf_path)
        return text.strip()
    except Exception as e:
        print(f"Failed to extract text from {pdf_path}: {e}")
        return None


def index_pdf_file(pdf_path):
    """
    Index a PDF file into Elasticsearch with its embedding.
    """
    # Extract text from the PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"Skipping {pdf_path} due to failed text extraction.")
        return

    # Generate embedding for the extracted text
    embedding = get_embedding(text)
    if not embedding or len(embedding) != 768:
        print(f"Skipping {pdf_path} due to invalid embedding.")
        return

    # Prepare document for indexing
    document = {
        "title": pdf_path,
        "content": text,
        "category": "general",  # You can adjust this dynamically based on the document
        "embedding": embedding,
        "custom_fields": {},  # You can add more custom fields here if needed
    }

    # Generate the hash from the document's title and content
    document["hash"] = generate_document_hash(document)  # Pass the document object here

    try:
        es.index(index="pdf_documents", document=document)
        print(f"PDF file {pdf_path} indexed successfully.")
    except Exception as e:
        print(f"Failed to index PDF file {pdf_path}: {e}")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Index a PDF file into Elasticsearch.")
    parser.add_argument("-f", "--file", required=True, help="Path to the PDF file to index.")
    args = parser.parse_args()

    # Validate the file path
    pdf_file_path = args.file
    if not pdf_file_path.endswith(".pdf"):
        print("The file must be a PDF.")
        exit(1)

    # Create Elasticsearch index
    print("Creating Elasticsearch index...")
    create_index()

    # Index the PDF file
    print("Indexing PDF document...")
    index_pdf_file(pdf_file_path)

    print("PDF document indexing completed!")
