import time
import openai
import requests
import logging
import json
from .config import Config
from . import redis_client
from elasticsearch import Elasticsearch


openai.api_key = Config.OPENAI_API_KEY

logger = logging.getLogger()

logger.info("Application started and logging configured with Redis.")


def get_embedding(text):
    """Fetch embedding for a given text from the AI model."""
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


def search_known_issues(query, es):
    start_time = time.time()
    logger.debug(f"Searching text: {query}")

    # Generate embedding for the query using semantic model (Ollama API or OpenAI embeddings)
    embedding = get_embedding(query)
    if not embedding:
        logger.warning("Failed to generate query embedding")
        raise ValueError("Failed to generate query embedding")

    # Check if the result is in Redis cache
    cache_key = f"Search:{query}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        logger.info("Cache hit, returning cached result")
        result = json.loads(cached_result)
        elapsed_time = round(time.time() - start_time, 2)
        # Ensure 3 values are returned (result, cache hit, time)
        return result, True, elapsed_time

    # Define the search query combining semantic search and vector search
    search_query = {
        "query": {
            "bool": {
                "should": [
                    {"multi_match": {
                        "query": query,
                        "fields": ["title", "issue", "solution"],
                        "fuzziness": "AUTO"
                    }},
                    {"knn": {
                        "field": "embedding",  # Assuming your documents store embeddings in the 'embedding' field
                        "query_vector": embedding,
                        "k": 5,  # Number of top similar results to retrieve
                        "num_candidates": 10  # Number of candidates to consider before applying the vector search
                    }}
                ],
                # At least one condition must match (either semantic or vector search)
                "minimum_should_match": 1
            }
        }
    }

    try:
        # Perform the combined search (semantic + vector)
        response = es.search(index="issues_n_solutions", body=search_query)
        documents = []

        # Process the results from Elasticsearch (only extracting title, issue, and solution)
        for hit in response["hits"]["hits"]:
            doc = hit["_source"]
            documents.append({
                "title": doc.get("title", ""),
                "issue": doc.get("issue", ""),
                "solution": doc.get("solution", ""),
            })
        logger.debug(f"Found {len(documents)} documents for query")
    except Exception as e:
        logger.error(f"Error during Elasticsearch query: {e}")
        # return error message
        return {"msg": "Error during Elasticsearch query"}, 500

    elapsed_time = round(time.time() - start_time, 2)

    # Classify the query based on the retrieved documents
    solution = find_solution(query, documents)

    # Cache the result in Redis for future use
    result = {"solution": solution}

    logger.info(f"Search completed in {elapsed_time} seconds")
    # Return 3 values: result, cache hit, elapsed time
    return result, False, elapsed_time


def find_solution(query, documents):
    # Modify context to include relevant fields for solution finding
    context = [
        {
            "Title": doc["title"],
            "Issue": doc["issue"],
            "Solution": doc["solution"]
        }
        for doc in documents
    ]

    # Create a prompt for OpenAI's model to find a solution for the user query
    prompt = f"""
    The user has described an issue or problem. Based on the context below, help find the best solution from the existing documents:
    
    Use the context below as examples to help identify a solution to the user's query:
    {json.dumps(context, ensure_ascii=False)}

    User Query: {query}

    Respond with:
    **Solution**: [Provide the best possible solution based on the context] else respond with "No feasible solution found".
    
    """

    try:
        # Assuming `Config.MODEL` contains the correct OpenAI model name
        model = Config.MODEL
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": "You are a problem-solving helpdesk assistant. Help find the best solution based on the context."},
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
        solution = parse_solution_response(
            response['choices'][0]['message']['content'])
        logger.info(f"Solution found: {solution}")
    except Exception as e:
        logger.error(f"Error in OpenAI solution search: {e}")
        solution = "No feasible solution found"

    # Return title, issue, and solution (added title and issue)
    # title = documents[0]["title"] if documents else "No title found"
    # issue = documents[0]["issue"] if documents else "No issue found"

    return solution


def parse_solution_response(response_text):
    try:
        # Extract the solution from the response text
        lines = response_text.split("\n")
        solution = next((line.split(":")[1].strip() for line in lines if line.startswith(
            "**Solution**")), "No feasible solution found")
        return solution
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        return "No feasible solution found"


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
    
    
