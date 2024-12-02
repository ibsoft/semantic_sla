# Use Python 3.10 slim image
FROM python:3.10.3-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && apt-get clean

# Set working directory
WORKDIR /

# Copy your application files to the container
COPY . /

# Upgrade pip to avoid potential issues
RUN pip install --upgrade pip==24.1

RUN pip install gunicorn


# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for the Flask app
EXPOSE 5000

# Command to run your Flask app
CMD ["bash", "api.sh", "start"]
