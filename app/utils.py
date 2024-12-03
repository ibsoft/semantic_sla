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
    return hashlib.md5(hash_source.encode()).hexdigest()


import time
import json
import logging

def search_sla(query, es):
    start_time = time.time()
    logger.debug(f"Searching text: {query}")

    # Generate embedding for the query using semantic model (Ollama API or OpenAI embeddings)
    embedding = get_embedding(query)
    if not embedding:
        logger.warning("Failed to generate query embedding")
        raise ValueError("Failed to generate query embedding")

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
                        "field": "embedding",  # Assuming your documents store embeddings in the 'embedding' field
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


        # Get the SLA solution (you may want to adjust this to match your logic)
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
            "Context": doc["content"],
            "Embedding": doc["embedding"]  # Add the embedding of the document for semantic search
        }
        for doc in documents
        
    ]

    # Create a prompt for OpenAI's model to find a solution for the user query based on title and content
    prompt = f"""
    Ενεργείς ως ειδικός βοηθός που παρακολουθεί τις συμβάσεις συνεργατών. Ο στόχος σου είναι να εντοπίσεις SLA (Service Level Agreements) μέσα στο παρεχόμενο περιεχόμενο. Συγκεκριμένα:
    
    1. Ψάξε να βρεις πληροφορίες που αφορούν χρόνους απόκρισης των συνεργατών για την επίλυση προβλημάτων.
    2. Αν οι χρόνοι απόκρισης εξαρτώνται από την τοποθεσία ή άλλες παραμέτρους, δες αν υπάρχει σχετική αναφορά στον τίτλο ή στο μήνυμα του χρήστη.


    Χρησιμοποίησε το παρακάτω περιεχόμενο για να βρεις το SLA:
    {json.dumps(context, ensure_ascii=False)}

    Ερώτημα Χρήστη: {query}

    Απάντησε με:
    **SLA**: [Παρέχετε το SLA σύμφωνα με το συμβόλαιο που έχεις στη βάση δεδομένων]".
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

        # Parse the OpenAI response to extract the solution
        sla = parse_solution_response(
            response['choices'][0]['message']['content'])
        logger.info(f"Solution found: {sla}")
    except Exception as e:
        logger.error(f"Error in OpenAI solution search: {e}")
        sla = "No feasible solution found"

    return sla



def parse_solution_response(response_text):
    try:
        # Extract the SLA from the response text
        lines = response_text.split("\n")
        
        # Logging the response text for debugging purposes
        logger.debug(f"Response text:\n{response_text}")
        
        # Attempt to extract SLA from the response
        sla = next((line.split(":")[1].strip() for line in lines if line.startswith("**SLA**")), None)
        
        if sla is None:
            logger.warning("SLA not found in the response")
            return "Δεν βρέθηκε εφικτό SLA για τη λύση"
        
        return sla
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        return "Δεν βρέθηκε εφικτό SLA για τη λύση"



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
    
    
