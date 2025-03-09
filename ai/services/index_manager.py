import os
import json
import numpy as np
import faiss
import threading
from datetime import datetime
from sentence_transformers import SentenceTransformer
import logging
from ai.schemas import Document

logger = logging.getLogger("doc_retrieval_api.index_manager")

class FAISSIndexManager:
    def __init__(self, embedding_model_name, index_data_dir):
        self.model = SentenceTransformer(embedding_model_name)
        self.documents = {}
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.embedding_dimension)
        self.lock = threading.Lock()
        self.index_data_dir = index_data_dir
        self.ensure_data_dir()
        
    def ensure_data_dir(self):
        """Ensure the index data directory exists"""
        if not os.path.exists(self.index_data_dir):
            os.makedirs(self.index_data_dir)
            os.makedirs(os.path.join(self.index_data_dir, "documents"))
            logger.info(f"Created index data directory at {self.index_data_dir}")
    
    def add_document(self, document: Document):
        """Add a document to the index"""
        with self.lock:
            if document.id in self.documents:
                return False
            
            # Create embedding
            embedding = self.model.encode([document.content])[0]
            document.embedding = embedding
            
            # Add to FAISS index
            self.index.add(np.array([embedding], dtype=np.float32))
            
            # Save document
            self.documents[document.id] = document
            
            # Save document to file
            self._save_document(document)
            
            return True
    
    def _save_document(self, document: Document):
        """Save document to JSON file"""
        doc_data = {
            "id": document.id,
            "content": document.content,
            "source": document.source,
            "metadata": document.metadata,
            "created_at": document.created_at,
            "chat_id": document.chat_id  # Lưu trữ chat_id
        }
        
        with open(os.path.join(self.index_data_dir, "documents", f"{document.id}.json"), "w", encoding="utf-8") as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=2)
    
    def search(self, query: str, chat_id: str = None, top_k: int = 3, threshold: float = 0.5):
        """Search for documents based on query and filter by chat_id"""
        with self.lock:
            # Lọc tài liệu theo chat_id nếu được chỉ định
            filtered_docs = self.documents
            if chat_id is not None:
                filtered_docs = {
                    doc_id: doc for doc_id, doc in self.documents.items() 
                    if doc.chat_id == chat_id
                }
                
            if len(filtered_docs) == 0:
                return []
            
            # Tạo embedding cho câu truy vấn
            query_embedding = np.array([self.model.encode(query)], dtype=np.float32)
            
            # Tìm kiếm trong tất cả tài liệu (vì FAISS không hỗ trợ lọc)
            distances, indices = self.index.search(query_embedding, min(top_k * 3, len(self.documents)))
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(self.documents):
                    continue
                
                # Tính điểm tương đồng (1 - khoảng cách L2 đã chuẩn hóa)
                distance = distances[0][i]
                similarity = 1.0 / (1.0 + distance)
                
                if similarity < threshold:
                    continue
                
                # Lấy document từ id
                doc_id = list(self.documents.keys())[idx]
                doc = self.documents[doc_id]
                
                # Kiểm tra nếu tài liệu thuộc về chat_id được chỉ định
                if chat_id is not None and doc.chat_id != chat_id:
                    continue
                
                results.append((doc, similarity))
                
                # Dừng khi đủ số lượng kết quả mong muốn
                if len(results) >= top_k:
                    break
            return results
    
    def delete_document(self, doc_id: str):
        """Delete document from index"""
        with self.lock:
            if doc_id not in self.documents:
                return False
            
            # Delete from dict
            del self.documents[doc_id]
            
            # Rebuild index
            self._rebuild_index()
            
            # Delete file
            doc_path = os.path.join(self.index_data_dir, "documents", f"{doc_id}.json")
            if os.path.exists(doc_path):
                os.remove(doc_path)
            
            return True
    
    def delete_chat_documents(self, chat_id: str):
        """Delete all documents associated with a specific chat_id"""
        with self.lock:
            docs_to_delete = [
                doc_id for doc_id, doc in self.documents.items() 
                if doc.chat_id == chat_id
            ]
            
            if not docs_to_delete:
                return 0
            
            # Delete documents
            for doc_id in docs_to_delete:
                del self.documents[doc_id]
                
                # Delete file
                doc_path = os.path.join(self.index_data_dir, "documents", f"{doc_id}.json")
                if os.path.exists(doc_path):
                    os.remove(doc_path)
            
            # Rebuild index
            self._rebuild_index()
            
            return len(docs_to_delete)
    
    def _rebuild_index(self):
        """Rebuild FAISS index after deleting documents"""
        if not self.documents:
            self.index = faiss.IndexFlatL2(self.embedding_dimension)
            return
        
        # Get embeddings from all remaining documents
        embeddings = []
        for doc in self.documents.values():
            if doc.embedding is not None:
                embeddings.append(doc.embedding)
        
        # Recreate index
        self.index = faiss.IndexFlatL2(self.embedding_dimension)
        if embeddings:
            self.index.add(np.array(embeddings, dtype=np.float32))
    
    def load_from_disk(self):
        """Load documents from disk"""
        with self.lock:
            doc_dir = os.path.join(self.index_data_dir, "documents")
            if not os.path.exists(doc_dir):
                return
            
            # Reset documents
            self.documents = {}
            
            # Read each file
            for filename in os.listdir(doc_dir):
                if not filename.endswith('.json'):
                    continue
                    
                try:
                    with open(os.path.join(doc_dir, filename), 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        
                    doc = Document(
                        id=doc_data["id"],
                        content=doc_data["content"],
                        source=doc_data["source"],
                        metadata=doc_data["metadata"],
                        chat_id=doc_data.get("chat_id")  # Đọc chat_id từ tệp
                    )
                    doc.created_at = doc_data.get("created_at", datetime.now().isoformat())
                    
                    # Create embedding
                    doc.embedding = self.model.encode([doc.content])[0]
                    
                    # Add to dict
                    self.documents[doc.id] = doc
                except Exception as e:
                    print(e)
                    logger.error(f"Error loading document {filename}: {str(e)}")
            
            # Rebuild index
            self._rebuild_index()
            logger.info(f"Loaded {len(self.documents)} documents from disk")
    
    def get_statistics(self, chat_id=None):
        """Get statistics about the number of documents, optionally filtered by chat_id"""
        with self.lock:
            # Lọc tài liệu theo chat_id nếu được chỉ định
            filtered_docs = self.documents
            if chat_id is not None:
                filtered_docs = {
                    doc_id: doc for doc_id, doc in self.documents.items() 
                    if doc.chat_id == chat_id
                }
            
            file_types = {}
            for doc in filtered_docs.values():
                file_type = doc.metadata.get("file_type", "unknown")
                if file_type in file_types:
                    file_types[file_type] += 1
                else:
                    file_types[file_type] = 1
                    
            return {
                "document_count": len(filtered_docs),
                "file_types": file_types
            }
    
    def get_chat_documents(self, chat_id: str):
        """Get all documents associated with a specific chat_id"""
        with self.lock:
            return {
                doc_id: doc for doc_id, doc in self.documents.items() 
                if doc.chat_id == chat_id
            }