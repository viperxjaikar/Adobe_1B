"""
Output Generation Module

This module provides functionality for generating the final output in the required JSON format.
"""

import os
import json
import datetime
from typing import Dict, List, Any, Tuple

class OutputGenerator:
    """
    Class for generating the final output in the required JSON format.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the output generator.
        
        Args:
            debug: Whether to print debug information
        """
        self.debug = debug
    
    def generate_output(self, 
                        input_documents: List[str],
                        persona: str,
                        job: str,
                        ranked_sections: List[Dict[str, Any]],
                        subsection_analysis: List[Dict[str, Any]],
                        max_sections: int = 5) -> Dict[str, Any]:
        """
        Generate the final output in the required JSON format.
        
        Args:
            input_documents: List of input document filenames
            persona: Persona description
            job: Job-to-be-done description
            ranked_sections: List of ranked sections
            subsection_analysis: List of analyzed subsections
            max_sections: Maximum number of sections to include in the output
            
        Returns:
            Dictionary containing the final output in the required format
        """
        # Prepare metadata
        metadata = {
            'input_documents': input_documents,
            'persona': persona,
            'job_to_be_done': job,
            'processing_timestamp': datetime.datetime.now().isoformat()
        }
        
        # Prepare extracted sections (top N based on importance rank)
        extracted_sections = []
        for section in ranked_sections:
            if section.get('importance_rank', float('inf')) <= max_sections:
                extracted_section = {
                    'document': section.get('document', ''),
                    'section_title': section.get('section_title', ''),
                    'importance_rank': section.get('importance_rank', 0),
                    'page_number': section.get('page_number', 0)
                }
                extracted_sections.append(extracted_section)
        
        # Prepare final output
        output = {
            'metadata': metadata,
            'extracted_sections': extracted_sections,
            'subsection_analysis': subsection_analysis
        }
        
        if self.debug:
            print(f"Generated output with {len(extracted_sections)} extracted sections and {len(subsection_analysis)} subsection analyses")
        
        return output
    
    def write_output_to_file(self, output: Dict[str, Any], output_path: str) -> None:
        """
        Write the output to a JSON file.
        
        Args:
            output: Output dictionary
            output_path: Path to write the output to
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(output, f, indent=4)
            
            if self.debug:
                print(f"Output written to {output_path}")
        
        except Exception as e:
            if self.debug:
                print(f"Error writing output to {output_path}: {e}")

class DocumentIntelligenceSystem:
    """
    Main system class that orchestrates the document intelligence process.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the document intelligence system.
        
        Args:
            debug: Whether to print debug information
        """
        self.debug = debug
        
        # Import modules here to avoid circular imports
        from pdf_extractor import PDFTextExtractor
        from section_processor import SectionProcessor
        from relevance_ranker import RelevanceRanker
        
        self.extractor = PDFTextExtractor(debug=debug)
        self.processor = SectionProcessor(debug=debug)
        self.ranker = RelevanceRanker(debug=debug)
        self.generator = OutputGenerator(debug=debug)
    
    def process_documents(self, input_json_path: str, output_json_path: str) -> None:
        """
        Process documents based on the input JSON and generate the output JSON.
        
        Args:
            input_json_path: Path to the input JSON file
            output_json_path: Path to the output JSON file
        """
        try:
            # Load input JSON
            with open(input_json_path, 'r') as f:
                input_data = json.load(f)
            
            # Extract information from input JSON
            documents = input_data.get('documents', [])
            persona_data = input_data.get('persona', {})
            job_data = input_data.get('job_to_be_done', {})
            
            persona = persona_data.get('role', '')
            job = job_data.get('task', '')
            
            # Get document filenames and paths
            document_filenames = [doc.get('filename', '') for doc in documents]
            document_paths = []
            
            # Determine the base directory for PDFs
            input_dir = os.path.dirname(input_json_path)
            pdf_dir = os.path.join(input_dir, 'PDFs')
            
            for filename in document_filenames:
                pdf_path = os.path.join(pdf_dir, filename)
                document_paths.append(pdf_path)
            
            if self.debug:
                print(f"Processing {len(document_paths)} documents")
                print(f"Persona: {persona}")
                print(f"Job: {job}")
            
            # Process each document
            all_sections = []
            for pdf_path in document_paths:
                # Extract text from PDF
                text_by_page = self.extractor.extract_text_from_pdf(pdf_path)
                
                # Process sections
                document_name = os.path.basename(pdf_path)
                sections = self.processor.process_sections(text_by_page, document_name)
                
                # Add sections to the list
                all_sections.extend(sections)
            
            # Rank sections by relevance
            ranked_sections, subsection_analysis = self.ranker.process_sections(all_sections, persona, job)
            
            # Generate output
            output = self.generator.generate_output(
                document_filenames,
                persona,
                job,
                ranked_sections,
                subsection_analysis
            )
            
            # Write output to JSON file
            self.generator.write_output_to_file(output, output_json_path)
            
            if self.debug:
                print(f"Document intelligence process completed successfully")
        
        except Exception as e:
            if self.debug:
                print(f"Error processing documents: {e}")
                import traceback
                traceback.print_exc()

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python output_generator.py <input_json_path> <output_json_path>")
        sys.exit(1)
    
    input_json_path = sys.argv[1]
    output_json_path = sys.argv[2]
    
    system = DocumentIntelligenceSystem(debug=True)
    system.process_documents(input_json_path, output_json_path)