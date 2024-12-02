import argparse
import hashlib
import openai
import json
from elasticsearch import Elasticsearch
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import numpy as np

# Elasticsearch setup
es = Elasticsearch(["http://localhost:9200"])

# OpenAI API setup
openai.api_key = "your_api_key"  # Replace with your OpenAI API key
OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"  # The OpenAI model for embeddings

def get_embedding(text):
    """
    Fetch embedding for the given text using OpenAI's text-embedding-ada-002 model.
    """
    try:
        response = openai.Embedding.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=text
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def generate_document_hash(doc):
    """
    Generate a hash for the document to avoid duplicates.
    """
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
                "embedding": {"type": "dense_vector", "dims": 1536},  # 1536 for ada-002
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


def chunk_text(text, max_length=8192):
    """
    Chunk the text into smaller parts to avoid exceeding the model's token limit.
    """
    # Split the text into smaller chunks of the specified max length
    chunks = []
    while len(text) > max_length:
        # Find the last space within the max_length limit
        chunk = text[:max_length]
        last_space = chunk.rfind(" ")
        if last_space != -1:
            chunks.append(text[:last_space])
            text = text[last_space:].strip()
        else:
            # If no space is found, just split the text as is
            chunks.append(text[:max_length])
            text = text[max_length:].strip()
    if text:
        chunks.append(text)
    return chunks


def combine_embeddings(embeddings):
    """
    Combine multiple embeddings into a single vector (average or concatenation).
    Here, we average the embeddings to create a single vector.
    """
    if not embeddings:
        return None

    # Average the embeddings
    avg_embedding = np.mean(embeddings, axis=0)
    return avg_embedding.tolist()  # Convert back to list for Elasticsearch compatibility


def index_pdf_file(pdf_path):
    """
    Index a PDF file into Elasticsearch with its embedding.
    """
    # Extract text from the PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"Skipping {pdf_path} due to failed text extraction.")
        return

    # Split the text into chunks to fit within the token limit
    text_chunks = chunk_text(text)
    
    # Generate embeddings for each chunk and combine them
    embeddings = []
    for chunk in text_chunks:
        embedding = get_embedding(chunk)
        if embedding:
            embeddings.append(embedding)
        else:
            print(f"Skipping chunk due to failed embedding.")

    # Combine the embeddings (average them)
    combined_embedding = combine_embeddings(embeddings)

    # If no embeddings were generated, skip indexing
    if not combined_embedding:
        print(f"Skipping {pdf_path} due to failed embeddings.")
        return

    # Prepare document for indexing
    document = {
        "title": pdf_path,
        "content": text,
        "hash": generate_document_hash({"title": pdf_path, "content": text}),
        "category": "general",  # You can adjust this dynamically based on the document
        "embedding": combined_embedding,
        "custom_fields": {},  # You can add more custom fields here if needed
    }

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
