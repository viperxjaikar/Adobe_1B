# Document Intelligence System

This system extracts and prioritizes the most relevant sections from a collection of documents based on a specific persona and their job-to-be-done.

## Features

- PDF text extraction with page number preservation
- Section and subsection identification
- Relevance ranking based on persona and job-to-be-done
- JSON output generation

## Requirements

- Docker

## Building the Docker Image

To build the Docker image, run the following command from the project root directory:

```bash
docker build -t document-intelligence .
```

## Running the System

The system takes an input JSON file and produces an output JSON file. The input JSON file should contain:

- A list of documents (with filenames)
- A persona description
- A job-to-be-done description

### Example Input JSON

```json
{
    "documents": [
        {
            "filename": "document1.pdf",
            "title": "Document 1"
        },
        {
            "filename": "document2.pdf",
            "title": "Document 2"
        }
    ],
    "persona": {
        "role": "Travel Planner"
    },
    "job_to_be_done": {
        "task": "Plan a trip of 4 days for a group of 10 college friends."
    }
}
```

### Running with Docker

To run the system with Docker, use the following command:

```bash
docker run -v /path/to/input/directory:/data/input -v /path/to/output/directory:/data/output document-intelligence
```

Replace `/path/to/input/directory` with the path to the directory containing your input JSON file and PDF documents, and `/path/to/output/directory` with the path where you want the output JSON file to be saved.

The input directory should have the following structure:

```
input/
├── challenge1b_input.json
└── PDFs/
    ├── document1.pdf
    ├── document2.pdf
    └── ...
```

### Custom Input and Output Files

You can specify custom input and output file paths:

```bash
docker run -v /path/to/input/directory:/data/input -v /path/to/output/directory:/data/output document-intelligence --input /data/input/custom_input.json --output /data/output/custom_output.json
```

## Output Format

The system produces a JSON file with the following structure:

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
        },
        ...
    ],
    "subsection_analysis": [
        {
            "document": "document1.pdf",
            "refined_text": "Refined text from the subsection...",
            "page_number": 5
        },
        ...
    ]
}
```

## Performance Constraints

- Runs on CPU only
- Model size ≤ 1GB
- Processing time ≤ 60 seconds for document collection (3-5 documents)
- No internet access required during execution