import os
from abc import ABC, abstractmethod
import chromadb


class VectorDB(ABC):
    @abstractmethod
    def insert_chunks(self, ids, chunks, metadatas):
        """
        Inserts or updates chunks.
        """
        pass

    @abstractmethod
    def search(self, query, user_id, n_results=5):
        """
        Search strictly scoped to the user_id.
        """
        pass

    @abstractmethod
    def delete_file(self, file_id):
        """
        Deletes all chunks associated with a specific file.
        """
        pass


class ChromaDB(VectorDB):
    def __init__(self):
        host = os.getenv("CHROMA_HOST", "localhost")
        port = os.getenv("CHROMA_PORT", "8003")
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection = self.client.get_or_create_collection("context")

    def insert_chunks(self, ids, chunks, metadatas):
        """
        Inserts or updates chunks.
        """
        self.collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)

    def search(self, query, user_id, n_results=5):
        """
        Search strictly scoped to the user_id.
        """
        return self.collection.query(
            query_texts=[query], n_results=n_results, where={"user_id": user_id}
        )

    def delete_file(self, file_id):
        """
        Deletes all chunks associated with a specific file.
        """
        self.collection.delete(where={"source_file_id": file_id})


def get_vector_db():
    return ChromaDB()
