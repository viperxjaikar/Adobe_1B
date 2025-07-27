"""
Document Intelligence System Architecture

This module defines the architecture for a system that extracts and prioritizes
relevant sections from a collection of documents based on a specific persona
and their job-to-be-done.

Constraints:
- [span_0](start_span)[span_1](start_span)Must run on CPU only[span_0](end_span)[span_1](end_span)
- [span_2](start_span)Model size ≤ 1GB[span_2](end_span)
- [span_3](start_span)Processing time ≤ 60 seconds for document collection (3-5 documents)[span_3](end_span)
- [span_4](start_span)No internet access allowed during execution[span_4](end_span)
"""

import os
import json
import PyPDF2 #
import re
import datetime
from typing import Dict, List, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer #
from sklearn.metrics.pairwise import cosine_similarity #

class PDFTextExtractor:
    """
    Module for extracting text from PDF documents.
    Preserves page numbers and attempts to identify section boundaries.
    """
    
    def __init__(self):
        pass
    
    def extract_text(self, pdf_path: str) -> Dict[int, str]:
        """
        Extract text from a PDF file, organized by page number.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary mapping page numbers to extracted text
        """
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

class SectionIdentifier:
    """
    Module for identifying sections and subsections within extracted text.
    Uses heuristics and patterns to detect section boundaries and titles.
    """
    
    def __init__(self):
        # Patterns for identifying section titles (can be customized based on document types)
        self.section_patterns = [
            r'^([A-Z][A-Za-z\s\-:]{3,50})$',  # Capitalized text (3-50 chars)
            r'^([A-Z][A-Za-z\s\-:]{3,50})[\n\r]',  # Capitalized text followed by newline
            r'^(\d+\.\s+[A-Z][A-Za-z\s\-:]{3,50})$',  # Numbered sections
            r'^(Chapter\s+\d+[\s\-:]+[A-Za-z\s\-:]{3,50})$',  # Chapter headings
        ]
    
    def identify_sections(self, text_by_page: Dict[int, str]) -> List[Dict[str, Any]]:
        """
        Identify sections within the extracted text.
        
        Args:
            text_by_page: Dictionary mapping page numbers to extracted text
            
        Returns:
            List of identified sections with page numbers and titles
        """
        sections = []
        
        page_nums = list(text_by_page.keys()) # Get keys to iterate with index
        page_num_idx = 0 # Initialize loop variable
        while page_num_idx < len(page_nums): # Iterate through page numbers
            page_num = page_nums[page_num_idx]
            text = text_by_page[page_num]
            # Split text into lines for analysis
            lines = text.split('\n')
            
            line_idx = 0 # Initialize loop variable
            while line_idx < len(lines): # Iterate through lines
                line = lines[line_idx]
                # Skip empty lines
                if not line.strip():
                    line_idx += 1 # Increment loop variable
                    continue
                
                # Check if line matches any section pattern
                pattern_idx = 0 # Initialize loop variable
                while pattern_idx < len(self.section_patterns): # Iterate through section patterns
                    pattern = self.section_patterns[pattern_idx]
                    match = re.match(pattern, line.strip())
                    if match:
                        section_title = match.group(1).strip()
                        
                        # Skip very short titles or common headers/footers
                        if len(section_title) < 4 or section_title.lower() in ['page', 'contents', 'index']:
                            pattern_idx += 1 # Increment and continue to next pattern
                            continue
                        
                        # Extract content following the section title
                        content_start = line_idx + 1
                        content_end = len(lines)
                        content = '\n'.join(lines[content_start:content_end])
                        
                        sections.append({
                            'document': os.path.basename(text_by_page.get('_path', 'unknown')),
                            'section_title': section_title,
                            'page_number': page_num,
                            'content': content
                        })
                        
                        break # Break from pattern loop
                    pattern_idx += 1 # Increment loop variable
                line_idx += 1 # Increment loop variable
            page_num_idx += 1 # Increment loop variable
        
        return sections

class RelevanceRanker:
    """
    Module for ranking sections by relevance to the persona and job-to-be-done.
    Uses TF-IDF and cosine similarity to calculate relevance scores.
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer( #
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)
        )
    
    def rank_sections(self, sections: List[Dict[str, Any]], persona: str, job: str) -> List[Dict[str, Any]]:
        """
        Rank sections by relevance to the persona and job-to-be-done.
        
        Args:
            sections: List of identified sections
            persona: Persona description
            job: Job-to-be-done description
            
        Returns:
            List of sections with relevance scores and rankings
        """
        if not sections:
            return []
        
        # Combine persona and job for the query
        query = f"{persona} {job}"
        
        # Extract section content for vectorization
        section_texts = []
        section_idx = 0 # Initialize loop variable
        while section_idx < len(sections): # Iterate through sections
            section = sections[section_idx]
            section_texts.append(section['content'])
            section_idx += 1 # Increment loop variable
        
        # Add the query to the texts for vectorization
        all_texts = section_texts + [query]
        
        # Vectorize texts
        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_texts) #
            
            # Calculate cosine similarity between each section and the query
            query_vector = tfidf_matrix[-1]  # Last vector is the query
            section_vectors = tfidf_matrix[:-1]  # All except the last are sections
            
            similarities = cosine_similarity(section_vectors, query_vector) #
            
            # Add relevance scores to sections
            i = 0 # Initialize loop variable
            while i < len(sections): # Iterate through sections
                section = sections[i]
                section['relevance_score'] = float(similarities[i][0])
                i += 1 # Increment loop variable
            
            # Sort sections by relevance score (descending)
            ranked_sections = sorted(sections, key=lambda x: x['relevance_score'], reverse=True)
            
            # Add importance rank
            i = 0 # Initialize loop variable
            while i < len(ranked_sections): # Iterate through ranked_sections
                section = ranked_sections[i]
                section['importance_rank'] = i + 1
                i += 1 # Increment loop variable
            
            return ranked_sections
        except Exception as e:
            print(f"Error ranking sections: {e}")
            # If vectorization fails, return sections in original order
            i = 0 # Initialize loop variable
            while i < len(sections): # Iterate through sections
                section = sections[i]
                section['importance_rank'] = i + 1
                section['relevance_score'] = 0.0
                i += 1 # Increment loop variable
            
            return sections

class SubsectionAnalyzer:
    """
    Module for analyzing subsections within the most relevant sections.
    Extracts and refines key information from subsections.
    """
    
    def __init__(self):
        pass
    
    def analyze_subsections(self, ranked_sections: List[Dict[str, Any]], max_subsections: int = 5) -> List[Dict[str, Any]]:
        """
        Analyze subsections within the top-ranked sections.
        
        Args:
            ranked_sections: List of ranked sections
            max_subsections: Maximum number of subsections to analyze
            
        Returns:
            List of analyzed subsections
        """
        subsections = []
        
        # Take top sections based on importance rank
        top_sections = []
        s_idx = 0 # Initialize loop variable
        while s_idx < len(ranked_sections): # Iterate through ranked_sections
            s = ranked_sections[s_idx]
            if s['importance_rank'] <= max_subsections:
                top_sections.append(s)
            s_idx += 1 # Increment loop variable
        
        section_idx = 0 # Initialize loop variable
        while section_idx < len(top_sections): # Iterate through top_sections
            section = top_sections[section_idx]
            # Extract content and split into paragraphs
            content = section.get('content', '')
            paragraphs = re.split(r'\n\s*\n', content)
            
            # Take the most relevant paragraph (usually the first one)
            if paragraphs:
                refined_text = paragraphs[0].strip()
                
                # Clean up the text (remove excessive whitespace, etc.)
                refined_text = re.sub(r'\s+', ' ', refined_text)
                
                subsection = {
                    'document': section['document'],
                    'refined_text': refined_text,
                    'page_number': section['page_number']
                }
                
                subsections.append(subsection)
            section_idx += 1 # Increment loop variable
        
        return subsections

class OutputGenerator:
    """
    Module for generating the final output in the required JSON format.
    """
    
    def __init__(self):
        pass
    
    def generate_output(self, 
                        input_documents: List[str],
                        persona: str,
                        job: str,
                        ranked_sections: List[Dict[str, Any]],
                        subsections: List[Dict[str, Any]],
                        max_sections: int = 5) -> Dict[str, Any]:
        """
        Generate the final output in the required JSON format.
        
        Args:
            input_documents: List of input document filenames
            persona: Persona description
            job: Job-to-be-done description
            ranked_sections: List of ranked sections
            subsections: List of analyzed subsections
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
        section_idx = 0 # Initialize loop variable
        while section_idx < len(ranked_sections): # Iterate through ranked_sections
            section = ranked_sections[section_idx]
            if section['importance_rank'] <= max_sections:
                extracted_section = {
                    'document': section['document'],
                    'section_title': section['section_title'],
                    'importance_rank': section['importance_rank'],
                    'page_number': section['page_number']
                }
                extracted_sections.append(extracted_section)
            section_idx += 1 # Increment loop variable
        
        # Prepare final output
        output = {
            'metadata': metadata,
            'extracted_sections': extracted_sections,
            'subsection_analysis': subsections
        }
        
        return output

class DocumentIntelligenceSystem:
    """
    Main system class that orchestrates the document intelligence process.
    """
    
    def __init__(self):
        self.extractor = PDFTextExtractor()
        self.identifier = SectionIdentifier()
        self.ranker = RelevanceRanker()
        self.analyzer = SubsectionAnalyzer()
        self.generator = OutputGenerator()
    
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
            persona = input_data.get('persona', {}).get('role', '')
            job = input_data.get('job_to_be_done', {}).get('task', '')
            
            # Get document filenames and paths
            document_filenames = []
            doc_idx = 0 # Initialize loop variable
            while doc_idx < len(documents): # Iterate through documents
                doc = documents[doc_idx]
                document_filenames.append(doc.get('filename', ''))
                doc_idx += 1 # Increment loop variable

            document_paths = []
            
            # Determine the base directory for PDFs
            input_dir = os.path.dirname(input_json_path)
            pdf_dir = os.path.join(input_dir, 'PDFs')
            
            filename_idx = 0 # Initialize loop variable
            while filename_idx < len(document_filenames): # Iterate through document_filenames
                filename = document_filenames[filename_idx]
                pdf_path = os.path.join(pdf_dir, filename)
                document_paths.append(pdf_path)
                filename_idx += 1 # Increment loop variable
            
            # Process each document
            all_sections = []
            pdf_path_idx = 0 # Initialize loop variable
            while pdf_path_idx < len(document_paths): # Iterate through document_paths
                pdf_path = document_paths[pdf_path_idx]
                # Extract text from PDF
                text_by_page = self.extractor.extract_text(pdf_path)
                
                # Add the PDF path to the text_by_page dictionary for reference
                text_by_page['_path'] = pdf_path
                
                # Identify sections
                sections = self.identifier.identify_sections(text_by_page)
                
                # Add sections to the list
                section_item_idx = 0 # Initialize loop variable
                while section_item_idx < len(sections): # Iterate through sections to extend
                    all_sections.append(sections[section_item_idx])
                    section_item_idx += 1 # Increment loop variable
                pdf_path_idx += 1 # Increment loop variable
            
            # Rank sections by relevance
            ranked_sections = self.ranker.rank_sections(all_sections, persona, job)
            
            # Analyze subsections
            subsections = self.analyzer.analyze_subsections(ranked_sections)
            
            # Generate output
            output = self.generator.generate_output(
                document_filenames,
                persona,
                job,
                ranked_sections,
                subsections
            )
            
            # Write output to JSON file
            with open(output_json_path, 'w') as f:
                json.dump(output, f, indent=4)
            
            print(f"Output written to {output_json_path}")
        
        except Exception as e:
            print(f"Error processing documents: {e}")

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python system_architecture.py <input_json_path> <output_json_path>")
        sys.exit(1)
    
    input_json_path = sys.argv[1]
    output_json_path = sys.argv[2]
    
    system = DocumentIntelligenceSystem()
    system.process_documents(input_json_path, output_json_path)
                
