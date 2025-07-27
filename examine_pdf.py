import PyPDF2
import json
import sys
from datetime import datetime

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text_by_page = {}
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Extract text from each page
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_by_page[i+1] = text  # Page numbers start from 1
            
        return text_by_page
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return {}

def analyze_pdf_structure(pdf_path):
    """Analyze the structure of a PDF file."""
    text_by_page = extract_text_from_pdf(pdf_path)
    
    # Print basic info
    print(f"\nAnalyzing PDF: {pdf_path}")
    print(f"Number of pages: {len(text_by_page)}")
    
    # Print a sample of text from each page (first 200 chars)
    for page_num, text in text_by_page.items():
        print(f"\nPage {page_num} sample:")
        print(text[:200] + "..." if len(text) > 200 else text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python examine_pdf.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    analyze_pdf_structure(pdf_path)