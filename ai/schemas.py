from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class Document:
    def __init__(self, id, content, source, metadata, chat_id=None):
        self.id = id
        self.content = content
        self.source = source
        self.metadata = metadata
        self.chat_id = chat_id  
        self.created_at = datetime.now().isoformat()
        self.embedding = None

# Pydantic models for API
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3
    threshold: float = 0.5
    chat_id: Optional[str] = None 

class DocumentResponse(BaseModel):
    id: str
    content: str
    source: str
    metadata: dict
    score: float
    chat_id: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    retrieved_documents: List[DocumentResponse]
    processing_time: float
    chat_id: Optional[str] = None

class DocumentStatistics(BaseModel):
    document_count: int
    file_types: dict