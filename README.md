# Document Intelligence System

A robust solution for extracting and prioritizing the most relevant sections from a collection of documents, tailored to a specific persona and their objectives.

## Key Features

- **PDF Text Extraction:** Retains original page numbers for traceability.
- **Structural Analysis:** Automatically identifies sections and subsections within documents.
- **Contextual Relevance Ranking:** Ranks document sections by relevance based on persona and task requirements.
- **Structured Output:** Generates concise, machine-readable JSON output for downstream applications.

## Prerequisites

- [Docker](https://www.docker.com/) must be installed.

## Getting Started

### Build the Docker Image

From the project root directory, execute:

```bash
docker build -t document-intelligence .
```

### Input Specifications

Prepare an input JSON file with the following structure:

```json
{
  "documents": [
    { "filename": "document1.pdf", "title": "Document 1" },
    { "filename": "document2.pdf", "title": "Document 2" }
  ],
  "persona": {
    "role": "Travel Planner"
  },
  "job_to_be_done": {
    "task": "Plan a trip of 4 days for a group of 10 college friends."
  }
}
```

### Directory Structure

Ensure your input directory is organized as follows:

```
input/
├── challenge1b_input.json
└── PDFs/
    ├── document1.pdf
    ├── document2.pdf
    └── ...
```

### Running the System with Docker

Run the following command, replacing the placeholder paths with your actual directories:

```bash
docker run \
  -v /path/to/input/directory:/data/input \
  -v /path/to/output/directory:/data/output \
  document-intelligence
```

**Note:**  
- `/path/to/input/directory` should contain your input JSON and PDF files.  
- `/path/to/output/directory` is where the output JSON will be saved.

#### Specify Custom Input and Output Files

To use custom file paths for input and output:

```bash
docker run \
  -v /path/to/input/directory:/data/input \
  -v /path/to/output/directory:/data/output \
  document-intelligence \
  --input /data/input/custom_input.json \
  --output /data/output/custom_output.json
```

## Output Format

The system produces a JSON file structured as follows:

```json
{
  "metadata": {
    "input_documents": ["document1.pdf", "document2.pdf"],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a trip of 4 days for a group of 10 college friends.",
    "processing_timestamp": "2025-07-24T15:30:45.123456"
  },
  "extracted_sections": [
    {
      "document": "document1.pdf",
      "section_title": "Section Title",
      "importance_rank": 1,
      "page_number": 5
    }
    // ...
  ],
  "subsection_analysis": [
    {
      "document": "document1.pdf",
      "refined_text": "Refined text from the subsection...",
      "page_number": 5
    }
    // ...
  ]
}
```

## Performance & Constraints

- **CPU-Only Execution:** No GPU required.
- **Model Size:** ≤ 1GB.
- **Processing Time:** ≤ 60 seconds for 3–5 documents.
- **Offline Operation:** Does not require internet access during execution.



---

For questions or support, please contact the repository maintainer.
````
