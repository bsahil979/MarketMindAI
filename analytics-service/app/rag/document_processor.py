"""
Document Processor - SEC 10-K and financial document processing
Handles PDF parsing, text extraction, chunking, and metadata extraction
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pypdf
from bs4 import BeautifulSoup

logger = logging.getLogger("marketmind.rag.document_processor")

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document processor
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Character overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # SEC-specific patterns for section detection
        self.sec_patterns = {
            "item_1": r"ITEM\s+1\.?\s+BUSINESS",
            "item_1a": r"ITEM\s+1A\.?\s+RISK\s+FACTORS",
            "item_7": r"ITEM\s+7\.?\s+MANAGEMENT['']S\s+DISCUSSION\s+AND\s+ANALYSIS",
            "item_7a": r"ITEM\s+7A\.?\s+QUANTITATIVE\s+AND\s+QUALITATIVE\s+DISCLOSURES",
            "item_8": r"ITEM\s+8\.?\s+FINANCIAL\s+STATEMENTS",
            "part_ii": r"PART\s+II",
            "part_iii": r"PART\s+III"
        }
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text and metadata from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            text = ""
            metadata = {
                "source": pdf_path,
                "filename": os.path.basename(pdf_path),
                "file_type": "pdf"
            }
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                metadata["page_count"] = len(pdf_reader.pages)
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
            
            # Try to extract company info from text
            metadata.update(self._extract_company_metadata(text))
            
            logger.info(f"Processed PDF: {pdf_path} ({len(text)} characters)")
            return {"text": text, "metadata": metadata}
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {e}")
            return {"text": "", "metadata": {"error": str(e)}}
    
    def process_text(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw text with provided metadata
        
        Args:
            text: Raw document text
            metadata: Document metadata
            
        Returns:
            Dictionary with processed text and metadata
        """
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Extract additional metadata
        extracted_metadata = self._extract_company_metadata(cleaned_text)
        metadata.update(extracted_metadata)
        
        return {"text": cleaned_text, "metadata": metadata}
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers and headers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        # Remove special characters but keep financial symbols
        text = re.sub(r'[^\w\s$%.,;:()\-\+]', ' ', text)
        return text.strip()
    
    def _extract_company_metadata(self, text: str) -> Dict[str, Any]:
        """Extract company information from text"""
        metadata = {}
        
        # Try to find company name (common patterns)
        company_patterns = [
            r'([A-Z][A-Za-z\s]+(?:Inc|Corp|LLC|Ltd|PLC))',
            r'COMPANY\s+NAME[:\s]+([A-Z][A-Za-z\s]+)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text[:5000])  # Search in first 5000 chars
            if match:
                metadata["company"] = match.group(1).strip()
                break
        
        # Try to find form type
        form_match = re.search(r'FORM\s+(10-K|10-Q|8-K)', text, re.IGNORECASE)
        if form_match:
            metadata["form_type"] = form_match.group(1).upper()
        
        # Try to find fiscal year
        year_match = re.search(r'FISCAL\s+YEAR\s+ENDED\s+(\d{4})', text, re.IGNORECASE)
        if year_match:
            metadata["fiscal_year"] = year_match.group(1)
        
        return metadata
    
    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Split document into chunks with metadata
        
        Args:
            text: Document text
            metadata: Document metadata
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        # Split by sections first (SEC documents have clear sections)
        section_chunks = self._split_by_sections(text)
        
        if len(section_chunks) > 1:
            # Use section-based chunks
            for section_name, section_text in section_chunks:
                sub_chunks = self._split_text_into_chunks(section_text)
                for i, chunk_text in enumerate(sub_chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata["section"] = section_name
                    chunk_metadata["chunk_index"] = i
                    chunk_metadata["chunk_count"] = len(sub_chunks)
                    chunks.append({"text": chunk_text, "metadata": chunk_metadata})
        else:
            # Use simple sliding window chunks
            text_chunks = self._split_text_into_chunks(text)
            for i, chunk_text in enumerate(text_chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = i
                chunk_metadata["chunk_count"] = len(text_chunks)
                chunks.append({"text": chunk_text, "metadata": chunk_metadata})
        
        logger.info(f"Chunked document into {len(chunks)} chunks")
        return chunks
    
    def _split_by_sections(self, text: str) -> List[tuple]:
        """Split text by SEC sections"""
        sections = []
        
        # Find all section headers
        section_matches = []
        for section_name, pattern in self.sec_patterns.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                section_matches.append((match.start(), section_name, match.group()))
        
        # Sort by position
        section_matches.sort(key=lambda x: x[0])
        
        # Extract sections
        for i, (start, section_name, header) in enumerate(section_matches):
            end = section_matches[i + 1][0] if i + 1 < len(section_matches) else len(text)
            section_text = text[start:end].strip()
            if len(section_text) > 100:  # Only keep substantial sections
                sections.append((section_name, section_text))
        
        return sections if sections else [("full_document", text)]
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks using sliding window"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_endings = ['.', '!', '?', '\n']
                for i in range(min(100, len(text) - end)):  # Look back up to 100 chars
                    if text[end - i] in sentence_endings:
                        end = end - i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
        
        return chunks
    
    def process_directory(
        self,
        directory: str,
        file_pattern: str = "*.pdf"
    ) -> List[Dict[str, Any]]:
        """
        Process all documents in a directory
        
        Args:
            directory: Directory path
            file_pattern: File pattern to match
            
        Returns:
            List of processed documents
        """
        processed_docs = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return processed_docs
        
        for file_path in dir_path.glob(file_pattern):
            if file_path.suffix.lower() == '.pdf':
                doc = self.process_pdf(str(file_path))
                if doc["text"]:
                    processed_docs.append(doc)
        
        logger.info(f"Processed {len(processed_docs)} documents from {directory}")
        return processed_docs
    
    def create_sample_sec_documents(self) -> List[Dict[str, Any]]:
        """
        Create sample SEC document data for testing
        This is useful when you don't have actual SEC filings
        """
        sample_docs = [
            {
                "text": """
                ITEM 1. BUSINESS
                Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company sells its products under the Apple brand through retail stores, online stores, and direct sales force, as well as through third-party cellular network carriers, wholesalers, retailers, and resellers.
                
                Net sales were $391.0 billion in 2024, an increase of 2% compared to 2023. iPhone net sales were $201.2 billion. Services net sales reached a record $96.2 billion, driven by strength in App Store, Cloud, and Payment Services.
                """,
                "metadata": {
                    "ticker": "AAPL",
                    "company": "Apple Inc.",
                    "form_type": "10-K",
                    "fiscal_year": "2024",
                    "section": "ITEM 1. BUSINESS"
                }
            },
            {
                "text": """
                ITEM 1A. RISK FACTORS
                Total term debt was $106.6 billion as of September 28, 2024. Commercial paper outstanding was $6.0 billion. Cash, cash equivalents, and marketable securities totaled $156.7 billion, leaving a net cash position of $44.1 billion.
                
                The company's business is subject to intense competition across all markets. Global economic conditions could adversely affect demand for the company's products and services.
                """,
                "metadata": {
                    "ticker": "AAPL",
                    "company": "Apple Inc.",
                    "form_type": "10-K",
                    "fiscal_year": "2024",
                    "section": "ITEM 1A. RISK FACTORS"
                }
            },
            {
                "text": """
                ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
                Microsoft total revenue grew 16% to $245.1 billion in FY2024. Intelligent Cloud revenue increased 20% to $105.4 billion, led by Azure revenue growth of 30%. Server products and cloud services revenue rose significantly.
                
                Operating income increased to $96.0 billion from $88.5 billion in the prior year. The company's cloud computing segment continues to drive growth with strong adoption of AI services.
                """,
                "metadata": {
                    "ticker": "MSFT",
                    "company": "Microsoft Corporation",
                    "form_type": "10-K",
                    "fiscal_year": "2024",
                    "section": "ITEM 7. MD&A"
                }
            },
            {
                "text": """
                ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
                Revenue for FY2024 was $60.9 billion, up 126% from $27.0 billion in FY2023. Data Center revenue reached a record $47.5 billion, up 217%, driven by compute platforms using HGX Hopper GPU architecture for generative AI.
                
                Gross margin improved to 72.7% from 63.2% in the prior year, reflecting higher data center revenue mix and operational efficiencies.
                """,
                "metadata": {
                    "ticker": "NVDA",
                    "company": "Nvidia Corporation",
                    "form_type": "10-K",
                    "fiscal_year": "2024",
                    "section": "ITEM 7. MD&A"
                }
            }
        ]
        
        return sample_docs
