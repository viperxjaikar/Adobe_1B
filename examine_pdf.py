import os
import json
import sys
from datetime import datetime
import PyPDF2 #

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text_by_page = {}
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file) #
            
            # Extract text from each page
            i = 0 # Initialize loop variable
            while i < len(reader.pages): # Iterate through pages
                page = reader.pages[i]
                text = page.extract_text() #
                if text:
                    text_by_page[i+1] = text  # Page numbers start from 1
                i += 1 # Increment loop variable
            
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
    page_nums = list(text_by_page.keys()) # Get keys to iterate with index
    j = 0 # Initialize loop variable
    while j < len(page_nums): # Iterate through page numbers
        page_num = page_nums[j]
        text = text_by_page[page_num]
        print(f"\nPage {page_num} sample:")
        print(text[:200] + "..." if len(text) > 200 else text)
        j += 1 # Increment loop variable

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python examine_pdf.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    analyze_pdf_structure(pdf_path)
