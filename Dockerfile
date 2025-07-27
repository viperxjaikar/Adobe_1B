# Use a Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code files
COPY pdf_extractor.py .
COPY section_processor.py .
COPY relevance_ranker.py .
COPY output_generator.py .
COPY main.py .

# Create a directory for input and output
RUN mkdir -p /data/input /data/output

# Set the entrypoint
ENTRYPOINT ["python", "main.py"]

# Default command (can be overridden)
CMD ["--input", "/data/input/challenge1b_input.json", "--output", "/data/output/challenge1b_output.json", "--debug"]