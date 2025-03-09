import time
import uuid
import os
from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import config
# Import services
from ai.services.llm_services import LLMService
from ai.utils.logging_config import setup_logging
from ai.schemas import QueryRequest, QueryResponse, DocumentResponse, Document
from ai.services.text_processor import TextProcessor
import logging
from ai.ai_init import index_manager
# Initialize logger
logger = logging.getLogger("doc_retrieval_api.routes")

# Create router
router = APIRouter()

# Initialize services

llm_service = LLMService(
    model_name=config.LLM_MODEL_NAME,
    temperature=config.LLM_TEMPERATURE,
    max_tokens=config.LLM_MAX_TOKENS,
    timeout=config.LLM_TIMEOUT,
    max_retries=config.LLM_MAX_RETRIES
)

# Document upload function
async def upload_document_handler(
    file_id_save: str,
    chunk_size: int = 500,
    overlap: int =100,
    chat_id: str = ""
):
    """Upload document and process to add to index"""
    print("upload_document_handler")
    start_time = time.time()
    
    # Check extension
    # file_extension = os.path.splitext(file.filename)[1]
    
    # if file_extension.lower() not in config.SUPPORTED_EXTENSIONS:
    #     raise HTTPException(
    #         status_code=400, 
    #         detail=f"Unsupported file format. Supported: {', '.join(config.SUPPORTED_EXTENSIONS)}"
    #     )
    
    # try:
    # Read file content
    # file_content = await file.read()
    
    # Extract text
    with open("uploaded_files/" + file_id_save, "rb") as f:
        file_content = f.read()
    text = TextProcessor.extract_text(file_content, file_id_save.split(".")[-1])

    # text = TextProcessor.extract_text_from_txt(file_content)
    
    if not text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from file"
        )
    
    # Split text into chunks
    chunks = TextProcessor.chunk_text(text, chunk_size, overlap)
    
    # Create description

    description = llm_service.create_description_short_for_file(chunks[0], chunks[-1])

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="Could not create chunks from text"
        )
    
    # Create metadata
    metadata = {
        "chunk_size": chunk_size,
        "overlap": overlap,
        "chunk_count": len(chunks),
        "original_size": len(text)
    }
    
    # Add each chunk to index
    added_count = 0
    for i, chunk in enumerate(chunks):
        doc_id = f"{uuid.uuid4()}"
        doc = Document(
            id=doc_id,
            content=chunk,
            source=file_id_save,
            metadata={
                **metadata,
                "chunk_index": i,
                "chunk_total": len(chunks)
            },
            chat_id=chat_id
        )
        
        if index_manager.add_document(doc):
            added_count += 1
    
    processing_time = time.time() - start_time
    
    return {
            "file_name": file_id_save,
            "chunks_added": added_count,
            "total_chunks": len(chunks),
            "processing_time_seconds": processing_time,
            "chat_id": chat_id
        }, description

    # except HTTPException as e:
    #     print(e)
    #     raise e
    # except Exception as e:
    #     logger.error(f"Error processing file: {str(e)}")
    #     print(e)
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Error processing file: {str(e)}"
    #     )

# Query documents function
async def query_documents_handler(query: str, chat_id: str, top_k: int = 10, threshold: float = 0.5):
    """Query documents and generate answer"""
    start_time = time.time()

    


    
    try:
        retrieved_docs = index_manager.search(
            query=query,
            chat_id=chat_id,
            top_k=top_k,
            threshold=threshold
        )
        
        if not retrieved_docs:
            return {
                "query": query,
                "answer": "No relevant information found in documents.",
                "retrieved_documents": [],
                "processing_time": time.time() - start_time,
                "chat_id": chat_id
            }        
        # Generate answer
        answer = llm_service.generate_answer(query, retrieved_docs)
        
        # Convert results to response format
        retrieved_doc_responses = []
        for doc, score in retrieved_docs:
            retrieved_doc_responses.append(
                DocumentResponse(
                    id=doc.id,
                    content=doc.content,
                    source=doc.source,
                    metadata=doc.metadata,
                    score=float(score),
                    chat_id=doc.chat_id
                )
            )
        return {
            "query": query,
            "answer": answer,
            "retrieved_documents": retrieved_doc_responses,
            "processing_time": time.time() - start_time,
            "chat_id": chat_id
        }

    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

# Delete document function
async def delete_document_handler(doc_id: str):
    """Delete document from index"""
    if index_manager.delete_document(doc_id):
        return {"status": "success", "message": f"Deleted document {doc_id}"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {doc_id} not found"
        )

# Delete chat documents function
async def delete_chat_documents_handler(chat_id: str):
    """Delete all documents associated with a chat session"""
    deleted_count = index_manager.delete_chat_documents(chat_id)
    if deleted_count > 0:
        return {
            "status": "success", 
            "message": f"Deleted {deleted_count} documents for chat {chat_id}"
        }
    else:
        return {
            "status": "success", 
            "message": f"No documents found for chat {chat_id}"
        }

# Get statistics function
async def get_statistics_handler(chat_id: Optional[str] = Query(None)):
    """Get statistics about documents in the system, optionally filtered by chat_id"""
    return index_manager.get_statistics(chat_id=chat_id)

# Get chat documents function
async def get_chat_documents_handler(chat_id: str):
    """Get all documents associated with a specific chat session"""
    documents = index_manager.get_chat_documents(chat_id)
    
    if not documents:
        return {"documents": [], "count": 0}
    
    # Convert to response format
    doc_responses = []
    for doc_id, doc in documents.items():
        doc_responses.append({
            "id": doc.id,
            "source": doc.source,
            "metadata": doc.metadata,
            "created_at": doc.created_at
        })
    
    return {"documents": doc_responses, "count": len(doc_responses)}

# Health check function
async def health_check_handler():
    """Check API operational status"""
    return {"status": "ok", "version": "1.0.0"}

# Register routes
def register_routes():
    """Register all routes with the router"""
    router.post("/api/documents/upload", response_model=dict)(upload_document_handler)
    router.post("/api/query", response_model=QueryResponse)(query_documents_handler)
    router.delete("/api/documents/{doc_id}")(delete_document_handler)
    router.delete("/api/chat/{chat_id}/documents")(delete_chat_documents_handler)
    router.get("/api/statistics")(get_statistics_handler)
    router.get("/api/chat/{chat_id}/documents")(get_chat_documents_handler)
    router.get("/api/health")(health_check_handler)
    
    return router

# Create and register routes
router = register_routes()