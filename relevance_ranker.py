"""
Relevance Ranking Module

This module provides functionality for ranking sections by relevance to the persona
and job-to-be-done using TF-IDF vectorization and other relevance metrics.
"""

import os
import re
import math
import string
from typing import Dict, List, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RelevanceRanker:
    """
    Class for ranking sections by relevance to the persona and job-to-be-done.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the relevance ranker.
        
        Args:
            debug: Whether to print debug information
        """
        self.debug = debug
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)
        )
    
    def preprocess_query(self, persona: str, job: str) -> str:
        """
        Preprocess the persona and job to create a query for relevance ranking.
        
        Args:
            persona: Persona description
            job: Job-to-be-done description
            
        Returns:
            Preprocessed query
        """
        # Combine persona and job
        query = f"{persona} {job}"
        
        # Extract key terms from the job description
        job_terms = self._extract_key_terms(job)
        
        # Add more weight to job terms by repeating them
        query = f"{query} {' '.join(job_terms)} {' '.join(job_terms)}"
        
        return query
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms from text.
        
        Args:
            text: Text to extract key terms from
            
        Returns:
            List of key terms
        """
        # Remove punctuation and convert to lowercase
        text = text.lower()
        for char in string.punctuation:
            text = text.replace(char, ' ')
        
        # Split into words
        words = text.split()
        
        # Remove common stopwords
        stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'when', 'where', 'how', 'to', 'in', 'for', 'with', 'by', 'of'}
        words = [word for word in words if word not in stopwords and len(word) > 2]
        
        return words
    
    def calculate_relevance_scores(self, sections: List[Dict[str, Any]], persona: str, job: str) -> List[Dict[str, Any]]:
        """
        Calculate relevance scores for sections based on the persona and job-to-be-done.
        
        Args:
            sections: List of sections
            persona: Persona description
            job: Job-to-be-done description
            
        Returns:
            List of sections with relevance scores
        """
        if not sections:
            return []
        
        # Preprocess query
        query = self.preprocess_query(persona, job)
        
        # Extract section content for vectorization
        section_texts = []
        for section in sections:
            # Combine section title and content for better matching
            title = section.get('section_title', '')
            content = section.get('content', '')
            keywords = ' '.join(section.get('keywords', []))
            
            # Create a combined text representation
            combined_text = f"{title} {title} {content} {keywords}"  # Repeat title for more weight
            section_texts.append(combined_text)
        
        # Add the query to the texts for vectorization
        all_texts = section_texts + [query]
        
        # Vectorize texts
        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            # Calculate cosine similarity between each section and the query
            query_vector = tfidf_matrix[-1]  # Last vector is the query
            section_vectors = tfidf_matrix[:-1]  # All except the last are sections
            
            similarities = cosine_similarity(section_vectors, query_vector)
            
            # Add relevance scores to sections
            for i, section in enumerate(sections):
                section['relevance_score'] = float(similarities[i][0])
                
                # Apply additional heuristics to adjust scores
                self._apply_heuristics(section, persona, job)
            
            if self.debug:
                print(f"Calculated relevance scores for {len(sections)} sections")
                for i, section in enumerate(sections):
                    print(f"  {i+1}. {section.get('section_title', 'Untitled')} - Score: {section.get('relevance_score', 0)}")
            
            return sections
        
        except Exception as e:
            if self.debug:
                print(f"Error calculating relevance scores: {e}")
            
            # If vectorization fails, assign default scores
            for i, section in enumerate(sections):
                section['relevance_score'] = 1.0 / (i + 1)  # Simple fallback scoring
            
            return sections
    
    def _apply_heuristics(self, section: Dict[str, Any], persona: str, job: str) -> None:
        """
        Apply heuristics to adjust relevance scores.
        
        Args:
            section: Section to adjust score for
            persona: Persona description
            job: Job-to-be-done description
        """
        score = section.get('relevance_score', 0.0)
        
        # Boost score if section title contains key terms from persona or job
        title = section.get('section_title', '').lower()
        persona_terms = self._extract_key_terms(persona)
        job_terms = self._extract_key_terms(job)
        
        for term in persona_terms:
            if term in title:
                score += 0.1
        
        for term in job_terms:
            if term in title:
                score += 0.2
        
        # Boost score based on content length (longer content might be more informative)
        word_count = section.get('word_count', 0)
        if word_count > 500:
            score += 0.1
        elif word_count > 200:
            score += 0.05
        
        # Penalize very short sections
        if word_count < 50:
            score -= 0.1
        
        # Update the score
        section['relevance_score'] = max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def rank_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank sections by relevance score.
        
        Args:
            sections: List of sections with relevance scores
            
        Returns:
            List of sections ranked by relevance score
        """
        # Sort sections by relevance score (descending)
        ranked_sections = sorted(sections, key=lambda x: x.get('relevance_score', 0.0), reverse=True)
        
        # Add importance rank
        for i, section in enumerate(ranked_sections):
            section['importance_rank'] = i + 1
        
        return ranked_sections
    
    def select_top_sections(self, ranked_sections: List[Dict[str, Any]], max_sections: int = 5) -> List[Dict[str, Any]]:
        """
        Select the top N sections by importance rank.
        
        Args:
            ranked_sections: List of ranked sections
            max_sections: Maximum number of sections to select
            
        Returns:
            List of top N sections
        """
        # Take top sections based on importance rank
        top_sections = [s for s in ranked_sections if s.get('importance_rank', float('inf')) <= max_sections]
        
        return top_sections
    
    def analyze_subsections(self, top_sections: List[Dict[str, Any]], persona: str, job: str) -> List[Dict[str, Any]]:
        """
        Analyze subsections within the top-ranked sections.
        
        Args:
            top_sections: List of top-ranked sections
            persona: Persona description
            job: Job-to-be-done description
            
        Returns:
            List of analyzed subsections
        """
        subsections = []
        
        for section in top_sections:
            # Get subsections
            section_subsections = section.get('subsections', [])
            
            if section_subsections:
                # Calculate relevance scores for subsections
                subsection_texts = [s.get('text', '') for s in section_subsections]
                
                # Preprocess query
                query = self.preprocess_query(persona, job)
                
                # Add the query to the texts for vectorization
                all_texts = subsection_texts + [query]
                
                try:
                    # Vectorize texts
                    tfidf_matrix = self.vectorizer.fit_transform(all_texts)
                    
                    # Calculate cosine similarity between each subsection and the query
                    query_vector = tfidf_matrix[-1]  # Last vector is the query
                    subsection_vectors = tfidf_matrix[:-1]  # All except the last are subsections
                    
                    similarities = cosine_similarity(subsection_vectors, query_vector)
                    
                    # Select the most relevant subsection
                    best_idx = similarities.argmax()
                    best_subsection = section_subsections[best_idx]
                    
                    # Create subsection analysis
                    subsection_analysis = {
                        'document': section.get('document', ''),
                        'refined_text': best_subsection.get('text', ''),
                        'page_number': section.get('page_number', 0)
                    }
                    
                    subsections.append(subsection_analysis)
                
                except Exception as e:
                    if self.debug:
                        print(f"Error analyzing subsections: {e}")
                    
                    # If vectorization fails, use the first subsection
                    if section_subsections:
                        subsection_analysis = {
                            'document': section.get('document', ''),
                            'refined_text': section_subsections[0].get('text', ''),
                            'page_number': section.get('page_number', 0)
                        }
                        
                        subsections.append(subsection_analysis)
            else:
                # If no subsections, use a portion of the section content
                content = section.get('content', '')
                if content:
                    # Take the first 200 characters as the refined text
                    refined_text = content[:200] + '...' if len(content) > 200 else content
                    
                    subsection_analysis = {
                        'document': section.get('document', ''),
                        'refined_text': refined_text,
                        'page_number': section.get('page_number', 0)
                    }
                    
                    subsections.append(subsection_analysis)
        
        return subsections
    
    def process_sections(self, sections: List[Dict[str, Any]], persona: str, job: str, max_sections: int = 5) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process sections to rank them by relevance and analyze subsections.
        
        Args:
            sections: List of sections
            persona: Persona description
            job: Job-to-be-done description
            max_sections: Maximum number of sections to include in the output
            
        Returns:
            Tuple of (ranked_sections, subsection_analysis)
        """
        # Calculate relevance scores
        sections_with_scores = self.calculate_relevance_scores(sections, persona, job)
        
        # Rank sections
        ranked_sections = self.rank_sections(sections_with_scores)
        
        # Select top sections
        top_sections = self.select_top_sections(ranked_sections, max_sections)
        
        # Analyze subsections
        subsection_analysis = self.analyze_subsections(top_sections, persona, job)
        
        return ranked_sections, subsection_analysis

# Example usage
if __name__ == "__main__":
    import sys
    import json
    from pdf_extractor import PDFTextExtractor
    from section_processor import SectionProcessor
    
    if len(sys.argv) < 4:
        print("Usage: python relevance_ranker.py <pdf_dir> <persona> <job>")
        sys.exit(1)
    
    pdf_dir = sys.argv[1]
    persona = sys.argv[2]
    job = sys.argv[3]
    
    # Get PDF files
    pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    # Process each PDF
    all_sections = []
    extractor = PDFTextExtractor(debug=True)
    processor = SectionProcessor(debug=True)
    
    for pdf_path in pdf_files:
        # Extract text from PDF
        text_by_page = extractor.extract_text_from_pdf(pdf_path)
        
        # Process sections
        document_name = os.path.basename(pdf_path)
        sections = processor.process_sections(text_by_page, document_name)
        
        # Add sections to the list
        all_sections.extend(sections)
    
    # Rank sections
    ranker = RelevanceRanker(debug=True)
    ranked_sections, subsection_analysis = ranker.process_sections(all_sections, persona, job)
    
    print(f"\nTop 5 ranked sections:")
    for i, section in enumerate(ranked_sections[:5]):
        print(f"\n{i+1}. {section.get('section_title', 'Untitled')} (Page {section.get('page_number', 0)})")
        print(f"   Document: {section.get('document', '')}")
        print(f"   Relevance score: {section.get('relevance_score', 0)}")
        print(f"   Importance rank: {section.get('importance_rank', 0)}")
    
    print(f"\nSubsection analysis:")
    for i, subsection in enumerate(subsection_analysis):
        print(f"\n{i+1}. Document: {subsection.get('document', '')}")
        print(f"   Page: {subsection.get('page_number', 0)}")
        refined_text = subsection.get('refined_text', '')
        print(f"   Refined text: {refined_text[:100]}..." if len(refined_text) > 100 else f"   Refined text: {refined_text}")