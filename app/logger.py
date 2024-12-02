import logging
from flask import request
from app.config import Config 

class RequestFormatter(logging.Formatter):
    def format(self, record):
        # Try to get the client's IP address
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr) if request else "SEMANTIC-SLA"
        # Prepend the IP address to the log message
        record.client_ip = client_ip
        return super().format(record)

def setup_logging():
    """
    Configure logging for the application.
    Avoid adding multiple handlers to the root logger.
    """
    logger = logging.getLogger()  # Root logger
    if not logger.handlers:  # Check if handlers are already attached
        logger.setLevel(Config.LOG_LEVEL)
        
        # Create file and stream handlers
        file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
        stream_handler = logging.StreamHandler()
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    # Create and apply the custom formatter
    formatter = RequestFormatter('%(client_ip)s - %(asctime)s - %(levelname)s - %(message)s')

    # Apply the formatter to all handlers
    for handler in logger.handlers:
        handler.setFormatter(formatter)

