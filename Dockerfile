FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies (build-essential and curl for network health checks)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK resources
RUN python -m nltk.downloader vader_lexicon punkt

# Copy all application source code, data, and docs
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Default command: launch the Streamlit dashboard on all interfaces
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
