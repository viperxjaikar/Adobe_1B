"""
Section Processing Module

This module provides functionality for processing extracted text from PDFs,
identifying sections and subsections, and preparing them for relevance ranking.
"""

import re
import os
import string
from typing import Dict, List, Any, Tuple

# We'll use simpler text processing to avoid NLTK dependency issues

class SectionProcessor:
    """
    Class for processing sections extracted from PDF documents.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the section processor.
        
        Args:
            debug: Whether to print debug information
        """
        self.debug = debug
        
        # Common English stopwords
        self.stop_words = set([
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
            'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
            'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
            'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
            'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
            'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
            'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to',
            'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
            's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
        ])
        
        # Patterns for identifying section titles
        self.section_patterns = [
            # Capitalized text (3-50 chars)
            r'^([A-Z][A-Za-z0-9\s\-:]{3,50})$',
            # Numbered sections
            r'^(\d+\.\s+[A-Za-z0-9\s\-:]{3,50})$',
            # Headings with colons
            r'^([A-Z][A-Za-z0-9\s\-]{3,40}):',
            # Common section headers
            r'^(Introduction|Conclusion|Summary|Overview|Background|Methods|Results|Discussion|References)$'
        ]
        
        # Common headers/footers to ignore
        self.ignore_patterns = [
            r'^Page \d+$',
            r'^\d+$',
            r'^[A-Za-z]+ \d+$',  # Month Year
            r'^Copyright',
            r'^All rights reserved',
            r'^Confidential'
        ]
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better section identification and relevance ranking.
        
        Args:
            text: Raw text
            
        Returns:
            Preprocessed text
        """
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        # Fix line breaks: ensure proper line breaks for paragraphs
        text = re.sub(r'(\w) (\w)', r'\1 \2', text)
        
        # Normalize newlines
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove headers and footers (common patterns)
        for pattern in self.ignore_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def is_section_title(self, line: str) -> bool:
        """
        Check if a line is likely to be a section title.
        
        Args:
            line: Line of text
            
        Returns:
            True if the line is likely a section title, False otherwise
        """
        # Skip empty lines
        if not line.strip():
            return False
        
        # Skip very short lines
        if len(line.strip()) < 4:
            return False
        
        # Skip lines that match ignore patterns
        for pattern in self.ignore_patterns:
            if re.match(pattern, line.strip()):
                return False
        
        # Check if line matches any section pattern
        for pattern in self.section_patterns:
            if re.match(pattern, line.strip()):
                return True
        
        # Additional heuristics for section titles
        
        # All caps or title case with limited length
        if (line.isupper() or line.istitle()) and 4 <= len(line) <= 50:
            return True
        
        # Ends with a colon and is relatively short
        if line.strip().endswith(':') and len(line) <= 50:
            return True
        
        # Contains keywords that suggest a section title
        section_keywords = ['chapter', 'section', 'part', 'introduction', 'conclusion']
        if any(keyword in line.lower() for keyword in section_keywords) and len(line) <= 50:
            return True
        
        return False
    
    def extract_section_title(self, line: str) -> str:
        """
        Extract the section title from a line.
        
        Args:
            line: Line of text
            
        Returns:
            Extracted section title
        """
        # Check if line matches any section pattern
        for pattern in self.section_patterns:
            match = re.match(pattern, line.strip())
            if match:
                return match.group(1).strip()
        
        # If no pattern matches, use the line as is
        return line.strip()
    
    def identify_sections(self, text_by_page: Dict[int, str], document_name: str) -> List[Dict[str, Any]]:
        """
        Identify sections within the extracted text.
        
        Args:
            text_by_page: Dictionary mapping page numbers to extracted text
            document_name: Name of the document
            
        Returns:
            List of identified sections with page numbers, titles, and content
        """
        sections = []
        current_section = None
        
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
                
                # Check if line is a section title
                if self.is_section_title(line):
                    section_title = self.extract_section_title(line)
                    
                    # If we have a current section, finalize it
                    if current_section:
                        sections.append(current_section)
                    
                    # Start a new section
                    current_section = {
                        'document': document_name,
                        'section_title': section_title,
                        'page_number': page_num,
                        'content': '',
                        'subsections': []
                    }
                else:
                    # Add line to current section content
                    if current_section:
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
                title = lines[0].strip() if lines and lines[0].strip() else f"Page {page_num}"
                
                # Create a section for this page
                section = {
                    'document': document_name,
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
                    # Clean and preprocess the paragraph
                    cleaned_paragraph = self.preprocess_text(paragraph)
                    
                    subsection = {
                        'text': cleaned_paragraph,
                        'page_number': section['page_number']
                    }
                    
                    section['subsections'].append(subsection)
        
        return sections
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract keywords from text for improved relevance ranking.
        
        Args:
            text: Text to extract keywords from
            top_n: Number of top keywords to extract
            
        Returns:
            List of extracted keywords
        """
        # Simple word tokenization (split by whitespace)
        words = text.lower().split()
        
        # Remove punctuation
        words = [word.strip(string.punctuation) for word in words]
        
        # Remove stopwords and very short words
        words = [word for word in words if word and word not in self.stop_words and len(word) > 2]
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N keywords
        return [word for word, freq in sorted_words[:top_n]]
    
    def enrich_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich sections with additional metadata for improved relevance ranking.
        
        Args:
            sections: List of sections
            
        Returns:
            Enriched list of sections
        """
        for section in sections:
            # Extract keywords from section content
            content = section.get('content', '')
            keywords = self.extract_keywords(content)
            
            # Add keywords to section metadata
            section['keywords'] = keywords
            
            # Extract sentences for potential use in subsection analysis (simple split by period)
            sentences = [s.strip() + '.' for s in content.split('.') if s.strip()]
            section['sentences'] = sentences[:5]  # Store first 5 sentences
            
            # Calculate section length (word count)
            words = content.split()
            section['word_count'] = len(words)
        
        return sections
    
    def process_sections(self, text_by_page: Dict[int, str], document_name: str) -> List[Dict[str, Any]]:
        """
        Process sections from extracted text.
        
        Args:
            text_by_page: Dictionary mapping page numbers to extracted text
            document_name: Name of the document
            
        Returns:
            Processed list of sections
        """
        # Identify sections
        sections = self.identify_sections(text_by_page, document_name)
        
        # Identify subsections
        sections = self.identify_subsections(sections)
        
        # Enrich sections with additional metadata
        sections = self.enrich_sections(sections)
        
        return sections

# Example usage
if __name__ == "__main__":
    import sys
    from pdf_extractor import PDFTextExtractor
    
    if len(sys.argv) != 2:
        print("Usage: python section_processor.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Extract text from PDF
    extractor = PDFTextExtractor(debug=True)
    text_by_page = extractor.extract_text_from_pdf(pdf_path)
    
    # Process sections
    processor = SectionProcessor(debug=True)
    document_name = os.path.basename(pdf_path)
    sections = processor.process_sections(text_by_page, document_name)
    
    print(f"\nFound {len(sections)} processed sections:")
    for i, section in enumerate(sections):
        print(f"\n{i+1}. {section['section_title']} (Page {section['page_number']})")
        print(f"   Keywords: {', '.join(section['keywords'])}")
        print(f"   Word count: {section['word_count']}")
        print(f"   Subsections: {len(section['subsections'])}")