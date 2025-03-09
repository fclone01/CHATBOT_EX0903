import re
import logging
import PyPDF2
import docx
from io import BytesIO

logger = logging.getLogger("doc_retrieval_api.text_processor")

class TextProcessor:
    @staticmethod
    def extract_text_from_pdf(file_content):
        """Extract text from PDF file"""
        try:
            reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF: {str(e)}")
            return ""
            
    @staticmethod
    def extract_text_from_docx(file_content):
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(BytesIO(file_content))
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting DOCX: {str(e)}")
            return ""
    
    @staticmethod
    def extract_text_from_txt(file_content):
        """Extract text from TXT file"""
        try:
            return file_content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return file_content.decode("latin-1")
            except:
                return ""
    
    @staticmethod
    def extract_text(file_content, file_extension):
        """Extract text from file based on format"""
        if file_extension.lower() == 'pdf':
            return TextProcessor.extract_text_from_pdf(file_content)
        elif file_extension.lower() == 'docx':
            return TextProcessor.extract_text_from_docx(file_content)
        elif file_extension.lower() == 'txt':
            return TextProcessor.extract_text_from_txt(file_content)
        else:
            return ""
    
    @staticmethod
    def chunk_text(text, chunk_size=500, overlap=100):
        """Split text into chunks of appropriate size"""
        if not text:
            return []
            
        # Process newlines and whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If sentence is longer than chunk_size, need to split further
            if len(sentence) > chunk_size:
                # Handle long sentences by splitting by words
                words = sentence.split()
                temp_chunk = ""
                
                for word in words:
                    if len(temp_chunk) + len(word) + 1 <= chunk_size:
                        temp_chunk += " " + word if temp_chunk else word
                    else:
                        chunks.append(temp_chunk)
                        temp_chunk = word
                
                if temp_chunk:
                    current_chunk += " " + temp_chunk if current_chunk else temp_chunk
            else:
                # Handle short sentences
                if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                    current_chunk += " " + sentence if current_chunk else sentence
                else:
                    chunks.append(current_chunk)
                    current_chunk = sentence
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # Create chunks with overlap
        result_chunks = []
        for i in range(len(chunks)):
            chunk = chunks[i]
            
            # Add overlap from next chunk if available
            if i < len(chunks) - 1 and len(chunk) < chunk_size:
                next_chunk = chunks[i+1]
                words_to_add = next_chunk.split()[:overlap]
                overlap_text = " ".join(words_to_add)
                
                if len(chunk) + len(overlap_text) + 1 <= chunk_size:
                    chunk += " " + overlap_text
            
            result_chunks.append(chunk)
        
        return result_chunks