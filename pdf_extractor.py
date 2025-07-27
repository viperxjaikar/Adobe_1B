"""
PDF Text Extraction Module

This module provides functionality for extracting text from PDF documents,
preserving page numbers, and preprocessing the text for better section identification.
"""

import os
import re
import PyPDF2
from typing import Dict, List, Any, Tuple, Optional

class PDFTextExtractor:
    """
    Class for extracting text from PDF documents with advanced preprocessing.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the PDF text extractor.
        
        Args:
            debug: Whether to print debug information
        """
        self.debug = debug
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[int, str]:
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
                reader = PyPDF2.PdfReader(file)
                
                # Extract text from each page
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        # Preprocess the text
                        text = self._preprocess_text(text)
                        text_by_page[i+1] = text  # Page numbers start from 1
                
            if self.debug:
                print(f"Extracted text from {pdf_path} ({len(text_by_page)} pages)")
                
            return text_by_page
        except Exception as e:
            if self.debug:
                print(f"Error extracting text from {pdf_path}: {e}")
            return {}
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess the extracted text to improve section identification.
        
        Args:
            text: Raw text extracted from a PDF page
            
        Returns:
            Preprocessed text
        """
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        # Fix line breaks: ensure proper line breaks for paragraphs
        text = re.sub(r'(\w) (\w)', r'\1 \2', text)  # Fix words split by spaces
        
        # Normalize newlines
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove headers and footers (common patterns)
        text = re.sub(r'^.*Page \d+.*\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n.*Page \d+.*$', '', text, flags=re.MULTILINE)
        
        return text
    
    def extract_sections_from_text(self, text_by_page: Dict[int, str], pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract sections from the text based on formatting and content patterns.
        
        Args:
            text_by_page: Dictionary mapping page numbers to extracted text
            pdf_path: Path to the PDF file
            
        Returns:
            List of sections with page numbers, titles, and content
        """
        sections = []
        current_section = None
        
        # Patterns for identifying section titles
        section_patterns = [
            r'^([A-Z][A-Za-z\s\-:]{3,50})$',  # Capitalized text (3-50 chars)
            r'^([A-Z][A-Za-z\s\-:]{3,50})[\n\r]',  # Capitalized text followed by newline
            r'^(\d+\.\s+[A-Z][A-Za-z\s\-:]{3,50})$',  # Numbered sections
            r'^(Chapter\s+\d+[\s\-:]+[A-Za-z\s\-:]{3,50})$',  # Chapter headings
        ]
        
        # Process each page
        for page_num in sorted(text_by_page.keys()):
            if isinstance(page_num, str):  # Skip metadata keys
                continue
                
            text = text_by_page[page_num]
            lines = text.split('\n')
            
            line_idx = 0
            while line_idx < len(lines):
                line = lines[line_idx].strip()
                
                # Skip empty lines
                if not line:
                    line_idx += 1
                    continue
                
                # Check if line matches any section pattern
                is_section_title = False
                for pattern in section_patterns:
                    match = re.match(pattern, line)
                    if match:
                        section_title = match.group(1).strip()
                        
                        # Skip very short titles or common headers/footers
                        if len(section_title) < 4 or section_title.lower() in ['page', 'contents', 'index']:
                            break
                        
                        # If we have a current section, finalize it
                        if current_section:
                            sections.append(current_section)
                        
                        # Start a new section
                        current_section = {
                            'document': os.path.basename(pdf_path),
                            'section_title': section_title,
                            'page_number': page_num,
                            'content': '',
                            'subsections': []
                        }
                        
                        is_section_title = True
                        break
                
                if not is_section_title and current_section:
                    # Add line to current section content
                    if current_section['content']:
                        current_section['content'] += '\n'
                    current_section['content'] += line
                
                line_idx += 1
        
        # Add the last section if it exists
        if current_section:
            sections.append(current_section)
        
        # If no sections were found, create a default section for each page
        if not sections:
            for page_num, text in text_by_page.items():
                if isinstance(page_num, str):  # Skip metadata keys
                    continue
                
                # Try to extract a title from the first line
                lines = text.split('\n')
                title = lines[0].strip() if lines else f"Page {page_num}"
                
                # Create a section for this page
                section = {
                    'document': os.path.basename(pdf_path),
                    'section_title': title,
                    'page_number': page_num,
                    'content': text,
                    'subsections': []
                }
                
                sections.append(section)
        
        return sections
    
    def identify_subsections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify subsections within each section.
        
        Args:
            sections: List of sections
            
        Returns:
            Updated list of sections with identified subsections
        """
        for section in sections:
            content = section.get('content', '')
            
            # Split content into paragraphs
            paragraphs = re.split(r'\n\s*\n', content)
            
            # Process each paragraph as a potential subsection
            for paragraph in paragraphs:
                if len(paragraph.strip()) > 50:  # Minimum length for a subsection
                    subsection = {
                        'text': paragraph.strip(),
                        'page_number': section['page_number']
                    }
                    
                    section['subsections'].append(subsection)
        
        return sections
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Process a PDF file to extract sections and subsections.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of sections with page numbers, titles, content, and subsections
        """
        # Extract text from PDF
        text_by_page = self.extract_text_from_pdf(pdf_path)
        
        # Extract sections from text
        sections = self.extract_sections_from_text(text_by_page, pdf_path)
        
        # Identify subsections
        sections = self.identify_subsections(sections)
        
        return sections

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python pdf_extractor.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    extractor = PDFTextExtractor(debug=True)
    sections = extractor.process_pdf(pdf_path)
    
    print(f"\nFound {len(sections)} sections:")
    for i, section in enumerate(sections):
        print(f"\n{i+1}. {section['section_title']} (Page {section['page_number']})")
        print(f"   Subsections: {len(section['subsections'])}")
        
        # Print first few characters of content
        content_preview = section['content'][:100] + "..." if len(section['content']) > 100 else section['content']
        print(f"   Content: {content_preview}")