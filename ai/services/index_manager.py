import os
import json
import numpy as np
import faiss
import threading
from datetime import datetime
import logging
from ai.schemas import Document

# Import Google Generative AI Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger("doc_retrieval_api.index_manager")


class FAISSIndexManager:
    def __init__(self,embedding_model_name , index_data_dir: str):
        self.model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # Vì embedding dimension không có sẵn -> tạo khi có embedding đầu tiên
        self.embedding_dimension = None
        self.documents = {}
        self.index = None
        self.lock = threading.Lock()
        self.index_data_dir = index_data_dir
        self.ensure_data_dir()

    def ensure_data_dir(self):
        if not os.path.exists(self.index_data_dir):
            os.makedirs(self.index_data_dir)
            os.makedirs(os.path.join(self.index_data_dir, "documents"))
            logger.info(f"Created index data directory at {self.index_data_dir}")

    def get_embedding(self, text: str):
        """Sinh embedding từ GoogleGenerativeAIEmbeddings"""
        try:
            embeddings = self.model.embed_query(text)
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def add_document(self, document: Document):
        with self.lock:
            if document.id in self.documents:
                return False

            # Tạo embedding
            embedding = self.get_embedding(document.content)
            if embedding is None:
                return False

            document.embedding = embedding.tolist()

            # Nếu chưa khởi tạo dimension, khởi tạo FAISS index
            if self.embedding_dimension is None:
                self.embedding_dimension = len(embedding)
                self.index = faiss.IndexFlatL2(self.embedding_dimension)

            # Thêm vào index
            self.index.add(np.array([embedding], dtype=np.float32))

            # Lưu document
            self.documents[document.id] = document

            # Lưu ra file
            self._save_document(document)

            return True

    def _save_document(self, document: Document):
        doc_data = {
            "id": document.id,
            "content": document.content,
            "source": document.source,
            "metadata": document.metadata,
            "created_at": document.created_at,
            "chat_id": document.chat_id,
            "embedding": document.embedding  # Lưu luôn embedding
        }

        path = os.path.join(self.index_data_dir, "documents", f"{document.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=2)

    def search(self, query: str, chat_id: str = None, top_k: int = 3, threshold: float = 0.5):
        with self.lock:
            if chat_id is not None:
                filtered_docs = {
                    doc_id: doc for doc_id, doc in self.documents.items() if doc.chat_id == chat_id
                }

            if len(filtered_docs) == 0:
                return []

            # Tạo embedding cho query
            query_embedding = self.get_embedding(query)
            if query_embedding is None or self.index is None:
                return []

            # Tìm kiếm
            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32),
                min(top_k * 3, len(self.documents))
            )

            results = []
            doc_ids = list(self.documents.keys())

            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(doc_ids):
                    continue

                distance = distances[0][i]
                similarity = 1.0 / (1.0 + distance)

                if similarity < threshold:
                    continue

                doc_id = doc_ids[idx]
                doc = self.documents[doc_id]

                if chat_id is not None and doc.chat_id != chat_id:
                    continue

                results.append((doc, similarity))

                if len(results) >= top_k:
                    break

            return results

    def _rebuild_index(self):
        if not self.documents:
            self.index = None
            self.embedding_dimension = None
            return

        embeddings = []
        for doc in self.documents.values():
            if doc.embedding is not None:
                embeddings.append(doc.embedding)

        if not embeddings:
            return

        self.embedding_dimension = len(embeddings[0])
        self.index = faiss.IndexFlatL2(self.embedding_dimension)
        self.index.add(np.array(embeddings, dtype=np.float32))

    def delete_file(self, file_name: str):
        with self.lock:
            docs_to_delete = [
                doc_id for doc_id, doc in self.documents.items()
                if doc.source == file_name
            ]

            if not docs_to_delete:
                return 0

            for doc_id in docs_to_delete:
                del self.documents[doc_id]
                doc_path = os.path.join(self.index_data_dir, "documents", f"{doc_id}.json")
                if os.path.exists(doc_path):
                    os.remove(doc_path)
                    logger.info(f"Deleted document file: {doc_id}.json")

            self._rebuild_index()

            logger.info(f"Deleted {len(docs_to_delete)} documents with source '{file_name}'")
            return len(docs_to_delete)

    def delete_document(self, doc_id: str):
        with self.lock:
            if doc_id not in self.documents:
                return False

            del self.documents[doc_id]

            doc_path = os.path.join(self.index_data_dir, "documents", f"{doc_id}.json")
            if os.path.exists(doc_path):
                os.remove(doc_path)

            self._rebuild_index()
            return True

    def delete_chat_documents(self, chat_id: str):
        with self.lock:
            docs_to_delete = [
                doc_id for doc_id, doc in self.documents.items() if doc.chat_id == chat_id
            ]

            if not docs_to_delete:
                return 0

            for doc_id in docs_to_delete:
                del self.documents[doc_id]
                doc_path = os.path.join(self.index_data_dir, "documents", f"{doc_id}.json")
                if os.path.exists(doc_path):
                    os.remove(doc_path)

            self._rebuild_index()
            return len(docs_to_delete)

    def load_from_disk(self):
        with self.lock:
            doc_dir = os.path.join(self.index_data_dir, "documents")
            if not os.path.exists(doc_dir):
                return

            self.documents = {}

            for filename in os.listdir(doc_dir):
                if not filename.endswith('.json'):
                    continue

                try:
                    path = os.path.join(doc_dir, filename)
                    with open(path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)

                    doc = Document(
                        id=doc_data["id"],
                        content=doc_data["content"],
                        source=doc_data["source"],
                        metadata=doc_data["metadata"],
                        chat_id=doc_data.get("chat_id")
                    )
                    doc.created_at = doc_data.get("created_at", datetime.now().isoformat())

                    # Đọc embedding đã lưu, tránh gọi API lại
                    doc.embedding = doc_data.get("embedding")
                    if doc.embedding is None:
                        doc.embedding = self.get_embedding(doc.content).tolist()

                    self.documents[doc.id] = doc

                except Exception as e:
                    logger.error(f"Error loading document {filename}: {str(e)}")

            self._rebuild_index()
            logger.info(f"Loaded {len(self.documents)} documents from disk")

    def get_statistics(self, chat_id=None):
        with self.lock:
            filtered_docs = self.documents
            if chat_id is not None:
                filtered_docs = {
                    doc_id: doc for doc_id, doc in self.documents.items()
                    if doc.chat_id == chat_id
                }

            file_types = {}
            for doc in filtered_docs.values():
                file_type = doc.metadata.get("file_type", "unknown")
                file_types[file_type] = file_types.get(file_type, 0) + 1

            return {
                "document_count": len(filtered_docs),
                "file_types": file_types
            }

    def get_chat_documents(self, chat_id: str):
        with self.lock:
            return {
                doc_id: doc for doc_id, doc in self.documents.items()
                if doc.chat_id == chat_id
            }
