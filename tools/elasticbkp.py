from elasticsearch import Elasticsearch, helpers
import json
from datetime import datetime

# Elasticsearch configuration
ES_HOST = 'http://localhost:9200'  # Elasticsearch URL
INDEX_NAME = 'sla_on_contracts'            # Name of the index to backup/restore

# Generate a timestamped backup filename
def get_backup_filename():
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'backup_{INDEX_NAME}_{current_time}.json'

# Connect to Elasticsearch
es = Elasticsearch(ES_HOST)

def backup_index():
    """Backup the index data to a file."""
    backup_file = get_backup_filename()
    try:
        # Fetch all documents from the index
        query = {"query": {"match_all": {}}}
        results = helpers.scan(es, index=INDEX_NAME, query=query)

        # Save to a JSON file
        with open(backup_file, 'w') as f:
            for doc in results:
                f.write(json.dumps(doc) + '\n')

        print(f"Backup completed successfully! Data saved to {backup_file}")
    except Exception as e:
        print(f"Error during backup: {e}")

def restore_index():
    """Restore the index data from the backup file."""
    backup_file = input("Enter the backup filename to restore from: ")
    try:
        # Delete the index if it exists
        if es.indices.exists(index=INDEX_NAME):
            es.indices.delete(index=INDEX_NAME)
            print(f"Index '{INDEX_NAME}' deleted.")

        # Create a new index
        es.indices.create(index=INDEX_NAME)
        print(f"Index '{INDEX_NAME}' created.")

        # Load data from the backup file
        with open(backup_file, 'r') as f:
            actions = [
                {
                    "_op_type": "index",
                    "_index": INDEX_NAME,
                    "_id": json.loads(line)["_id"],
                    "_source": json.loads(line)["_source"],
                }
                for line in f
            ]

        # Bulk insert data into the index
        helpers.bulk(es, actions)
        print(f"Restore completed successfully! Data restored to '{INDEX_NAME}'")
    except Exception as e:
        print(f"Error during restore: {e}")

def main():
    print("Elasticsearch Backup and Restore Script")
    print("1. Backup")
    print("2. Restore")
    choice = input("Enter your choice (1/2): ")

    if choice == '1':
        backup_index()
    elif choice == '2':
        restore_index()
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
