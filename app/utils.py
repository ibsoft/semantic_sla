import hashlib
import time
import openai
import requests
import logging
import json
from .config import Config
from . import redis_client
from elasticsearch import Elasticsearch
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
import hashlib
import requests
from docx import Document
import pandas as pd

openai.api_key = Config.OPENAI_API_KEY

logger = logging.getLogger()

logger.info("Application started and logging configured with Redis.")



def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file, with OCR fallback if necessary.
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


def extract_text_with_ocr(pdf_path):
    """
    Extract text from PDF using OCR as a fallback with support for Greek and English.
    """
    try:
        pages = convert_from_path(pdf_path, dpi=300)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page, lang="ell+eng")
        return text.strip()
    except Exception as e:
        print(f"Failed to extract text using OCR from {pdf_path}: {e}")
        return None


def generate_document_hash(doc):
    """
    Generate a hash for deduplication based on document title and content.
    """
    hash_source = f"{doc['title']}{doc['content']}"
    return hashlib.sha256(hash_source.encode()).hexdigest()



def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return " ".join(paragraph.text for paragraph in doc.paragraphs)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        return None

def extract_text_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error extracting text from TXT: {str(e)}")
        return None

def extract_text_from_xlsx(file_path):
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        return "\n".join(df.apply(lambda row: " ".join(row.astype(str)), axis=1))
    except Exception as e:
        logger.error(f"Error extracting text from XLSX: {str(e)}")
        return None


def search_sla(query, es):
    start_time = time.time()
    logger.debug(f"Searching text: {query}")

    # Generate embedding for the query using semantic model (Ollama API or OpenAI embeddings)
    embedding = get_embedding(query)
    
    if not embedding:
        logger.warning("Failed to generate query embedding")
        raise ValueError("Failed to generate query embedding")
    else:
        logger.info("Created embedding for input query. Success!")

    # Skip Redis cache lookup if USE_REDIS is False
    result = {}

    if Config.USE_REDIS:
        cache_key = f"Search:{query}"
        cached_result = redis_client.get(cache_key)

        if cached_result:
            logger.info("Cache hit, returning cached result")
            result = json.loads(cached_result)
            elapsed_time = round(time.time() - start_time, 2)
            return result, True, elapsed_time

    # If no cache or USE_REDIS is False, proceed with the search
    search_query = {
        "query": {
            "bool": {
                "should": [
                    {"multi_match": {
                        "query": query,
                        "fields": ["title", "content"],
                        "fuzziness": "AUTO"
                    }},
                    {"knn": {
                        "field": "embedding",  # The query_vector is compared to the document embeddings in the embedding field to calculate similarity.
                        "query_vector": embedding,
                        "k": 5,
                        "num_candidates": 10
                    }}
                ],
                "minimum_should_match": 1
            }
        }
    }

    try:
        # Perform Elasticsearch search
        response = es.search(index="pdf_documents", body=search_query)

        # Process the search response
        documents = []
        highest_score_document = None
        highest_score = float('-inf')

        for hit in response['hits']['hits']:
            score = hit.get('_score', float('-inf'))
            title = hit['_source'].get('title', 'No Title Available')
            
            # Log each document's score and title
            logger.info(f"Document Title: {title}, Score: {score}")           

            # Track the document with the highest score
            if score > highest_score:
                highest_score = score
                highest_score_document = hit['_source']

            documents.append(hit['_source'])

        # If no results are found
        if not highest_score_document:
            logger.warning("No results found in Elasticsearch")
            return {"msg": "No results found"}, False, round(time.time() - start_time, 2)

        # Log the highest scoring document
        logger.debug(f"Highest score document: {highest_score_document}")
        logger.info(f"Highest score document title: {highest_score_document.get('title', 'No Title Available')}")
        logger.info(f"Highest score document score: {highest_score}")


        # Get the SLA solution 
        solution = find_sla(query, [highest_score_document])
        
        result = {"solution": solution}

        # Cache the result if required
        if Config.USE_REDIS:
            result = {"solution": solution}
            redis_client.set(cache_key, json.dumps(result))

    except Exception as e:
        # Handle errors and log them
        logger.error(f"Error during Elasticsearch query: {e}")
        return {"msg": "Error during Elasticsearch query"}, False, round(time.time() - start_time, 2)

    elapsed_time = round(time.time() - start_time, 2)
    logger.info(f"Search completed in {elapsed_time} seconds")
    
    return result, False, elapsed_time


def find_sla(query, documents):
    # Modify context to include both title and content embeddings for solution finding
    context = [
        {
            "Title": doc["title"],
            "Context": doc["content"]

        }
        for doc in documents
        
    ]

    # Create a prompt for OpenAI's model to find a solution for the user query based on title and content
    prompt = f"""
    Ενεργείς ως ειδικός βοηθός που παρακολουθεί τις συμβάσεις συνεργατών. Ο στόχος σου είναι να εντοπίσεις και να συνοψίσεις όλες τις SLA (Service Level Agreements) που σχετίζονται με τον συνεργάτη που περιγράφεται στο παρακάτω περιεχόμενο. Συγκεκριμένα:

    1. Εντόπισε όλα τα SLA που αναφέρονται (χρόνοι απόκρισης, επίπεδα εξυπηρέτησης, γεωγραφικές περιοχές, εξαιρέσεις κ.λπ.).
    2. Δημιούργησε μια σύντομη περίληψη που περιλαμβάνει τα βασικά σημεία όλων των SLA που ισχύουν για τον συγκεκριμένο συνεργάτη.

    Χρησιμοποίησε το παρακάτω περιεχόμενο για την ανάλυση:
    {json.dumps(context, ensure_ascii=False)}

    Ερώτημα Χρήστη: {query}

    Απάντησε με:
    **Σύνοψη SLA**: [Περίληψη όλων των SLA με τα βασικά σημεία, διατυπωμένα με συνοπτικό τρόπο για τον συγκεκριμένο συνεργάτη].
"""




    try:
        # Assuming `Config.MODEL` contains the correct OpenAI model name
        model = Config.MODEL
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": "Είσαι ένας βοηθός που παρακολουθεί τις συμβάσεις με τους συνεργάτες μας."},
                      {"role": "user", "content": prompt}]
        )

        # Log the response details
        usage_info = response.get('usage', {})
        logger.info(f"Response from OpenAI received for query: {query}")
        logger.info(
            f"Total tokens used: {usage_info.get('total_tokens', 'N/A')}")
        logger.info(f"Prompt tokens: {usage_info.get('prompt_tokens', 'N/A')}")
        logger.info(
            f"Completion tokens: {usage_info.get('completion_tokens', 'N/A')}")
        logger.debug(
            f"Response content: {response['choices'][0]['message']['content']}")

        # OPEN AI solution
        sla = response['choices'][0]['message']['content']
        logger.info(f"Solution found: {sla}")
    except Exception as e:
        logger.error(f"Error in OpenAI solution search: {e}")
        sla = "No feasible solution found"

    return sla




def get_embedding(text):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {"model": Config.OLLAMA_MODEL, "prompt": text}
    try:
        response = requests.post(
            Config.OLLAMA_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        logger.info(f"Successfully fetched embedding for text: {text}")
        return response.json().get("embedding", None)
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None
    
    
