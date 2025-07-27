"""
Document Intelligence System - Main Script

This script provides a command-line interface for the document intelligence system.
It processes a collection of documents based on a persona and job-to-be-done,
extracting and prioritizing the most relevant sections.
"""

import os
import sys
import argparse
import json
from output_generator import DocumentIntelligenceSystem

def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Document Intelligence System')
    parser.add_argument('--input', '-i', type=str, required=True,
                        help='Path to the input JSON file')
    parser.add_argument('--output', '-o', type=str, required=True,
                        help='Path to the output JSON file')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug mode')
    
    return parser.parse_args()

def validate_input(input_path):
    """
    Validate the input JSON file.
    
    Args:
        input_path: Path to the input JSON file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(input_path):
            print(f"Error: Input file '{input_path}' does not exist")
            return False
        
        # Check if file is a valid JSON
        with open(input_path, 'r') as f:
            input_data = json.load(f)
        
        # Check if required fields are present
        if 'documents' not in input_data:
            print("Error: Input JSON must contain a 'documents' field")
            return False
        
        if 'persona' not in input_data:
            print("Error: Input JSON must contain a 'persona' field")
            return False
        
        if 'job_to_be_done' not in input_data:
            print("Error: Input JSON must contain a 'job_to_be_done' field")
            return False
        
        # Check if documents field is a list
        if not isinstance(input_data['documents'], list):
            print("Error: 'documents' field must be a list")
            return False
        
        # Check if documents list is not empty
        if len(input_data['documents']) == 0:
            print("Error: 'documents' list must not be empty")
            return False
        
        # Check if PDF directory exists
        pdf_dir = os.path.join(os.path.dirname(input_path), 'PDFs')
        if not os.path.exists(pdf_dir):
            print(f"Error: PDF directory '{pdf_dir}' does not exist")
            return False
        
        # Check if all document files exist
        for doc in input_data['documents']:
            if 'filename' not in doc:
                print("Error: Each document must have a 'filename' field")
                return False
            
            pdf_path = os.path.join(pdf_dir, doc['filename'])
            if not os.path.exists(pdf_path):
                print(f"Error: Document file '{pdf_path}' does not exist")
                return False
        
        return True
    
    except json.JSONDecodeError:
        print(f"Error: Input file '{input_path}' is not a valid JSON file")
        return False
    
    except Exception as e:
        print(f"Error validating input: {e}")
        return False

def main():
    """
    Main function.
    """
    # Parse arguments
    args = parse_arguments()
    
    # Validate input
    if not validate_input(args.input):
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process documents
    try:
        system = DocumentIntelligenceSystem(debug=args.debug)
        system.process_documents(args.input, args.output)
        
        print(f"Document intelligence process completed successfully")
        print(f"Output written to {args.output}")
    
    except Exception as e:
        print(f"Error processing documents: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()