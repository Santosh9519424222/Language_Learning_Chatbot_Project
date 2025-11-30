"""
Chroma Vector Store for Semantic Search
Handles PDF chunk embeddings and retrieval

Author: Santosh Yadav
Date: November 2025
"""

import os
import logging
import threading
from typing import List, Dict, Any, Optional
import uuid

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """
    Manages Chroma DB vector store for semantic search over PDF content.
    Uses CPU-friendly sentence-transformers for embeddings.
    """

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        model_name: str = "all-MiniLM-L6-v2",
        collection_name: str = "pdf_chunks"
    ):
        """
        Initialize Chroma Vector Store with persistent storage.

        Args:
            persist_directory: Directory for persistent storage
            model_name: Sentence transformer model name (CPU-friendly)
            collection_name: Name of the Chroma collection
        """
        self.persist_directory = persist_directory
        self.model_name = model_name
        self.collection_name = collection_name
        self._lock = threading.Lock()

        logger.info(f"Initializing ChromaVectorStore with model: {model_name}")

        try:
            # Create persist directory
            os.makedirs(persist_directory, exist_ok=True)

            # Initialize Chroma client with persistent storage (new API)
            self.client = chromadb.PersistentClient(path=persist_directory)

            # Initialize embedding function
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model_name
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "PDF learning content chunks"}
            )

            logger.info(f"✅ ChromaVectorStore initialized successfully")
            logger.info(f"   Collection: {collection_name}")
            logger.info(f"   Persist directory: {persist_directory}")
            logger.info(f"   Current document count: {self.collection.count()}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaVectorStore: {e}", exc_info=True)
            raise

    def add_pdf_chunks(self, pdf_id: str, chunks: List[Dict[str, Any]]) -> bool:
        """
        Add PDF chunks to vector store with metadata.

        Args:
            pdf_id: Unique PDF identifier
            chunks: List of chunk dictionaries with 'text', 'page', etc.

        Returns:
            bool: True if successful
        """
        if not chunks:
            logger.warning(f"No chunks provided for PDF {pdf_id}")
            return False

        logger.info(f"Adding {len(chunks)} chunks for PDF {pdf_id}")

        try:
            with self._lock:
                # Prepare data for Chroma
                ids = []
                documents = []
                metadatas = []

                for chunk in chunks:
                    # Generate unique ID
                    chunk_id = chunk.get('chunk_id', f"{pdf_id}_{uuid.uuid4()}")
                    ids.append(chunk_id)

                    # Extract text
                    documents.append(chunk['text'])

                    # Prepare metadata
                    metadata = {
                        'pdf_id': pdf_id,
                        'page': chunk.get('page', 0),
                        'difficulty': chunk.get('difficulty', 'Beginner'),
                        'is_vocabulary': chunk.get('is_vocabulary', False),
                        'word_count': chunk.get('word_count', 0),
                        'start_char': chunk.get('start_char', 0),
                        'end_char': chunk.get('end_char', 0)
                    }
                    metadatas.append(metadata)

                # Add to collection
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )

                # Persist to disk
                self.client.persist()

                logger.info(f"✅ Successfully added {len(chunks)} chunks for PDF {pdf_id}")
                logger.info(f"   Total documents in collection: {self.collection.count()}")

                return True

        except Exception as e:
            logger.error(f"Failed to add chunks for PDF {pdf_id}: {e}", exc_info=True)
            return False

    def retrieve_relevant_chunks(
        self,
        query: str,
        pdf_id: str,
        top_k: int = 5,
        difficulty_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using semantic search.

        Args:
            query: Search query
            pdf_id: PDF identifier to filter results
            top_k: Number of top results to return
            difficulty_filter: Optional difficulty level filter

        Returns:
            List[dict]: Relevant chunks with metadata and scores
        """
        logger.info(f"Searching for '{query}' in PDF {pdf_id} (top_k={top_k})")

        try:
            with self._lock:
                # Build where clause for filtering
                where_clause = {"pdf_id": pdf_id}
                if difficulty_filter:
                    where_clause["difficulty"] = difficulty_filter

                # Query collection
                results = self.collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    where=where_clause
                )

                # Format results
                chunks = []
                if results and results['documents'] and len(results['documents']) > 0:
                    for i in range(len(results['documents'][0])):
                        chunk = {
                            'content': results['documents'][0][i],
                            'page': results['metadatas'][0][i].get('page', 0),
                            'distance': results['distances'][0][i] if 'distances' in results else 0.0,
                            'chunk_id': results['ids'][0][i],
                            'is_vocabulary': results['metadatas'][0][i].get('is_vocabulary', False),
                            'difficulty': results['metadatas'][0][i].get('difficulty', 'Unknown'),
                            'word_count': results['metadatas'][0][i].get('word_count', 0)
                        }
                        chunks.append(chunk)

                logger.info(f"Found {len(chunks)} relevant chunks")

                return chunks

        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {e}", exc_info=True)
            return []

    def get_collection_stats(self, pdf_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the collection or specific PDF.

        Args:
            pdf_id: Optional PDF identifier to filter stats

        Returns:
            dict: Collection statistics
        """
        logger.debug(f"Getting collection stats for PDF: {pdf_id or 'all'}")

        try:
            with self._lock:
                stats = {
                    'total_chunks': self.collection.count(),
                    'pdf_id': pdf_id,
                    'collection_name': self.collection_name
                }

                if pdf_id:
                    # Get PDF-specific stats
                    results = self.collection.get(
                        where={"pdf_id": pdf_id}
                    )

                    if results and results['metadatas']:
                        stats['pdf_chunks'] = len(results['metadatas'])

                        # Aggregate difficulty levels
                        difficulties = {}
                        languages = set()
                        topics = set()

                        for metadata in results['metadatas']:
                            diff = metadata.get('difficulty', 'Unknown')
                            difficulties[diff] = difficulties.get(diff, 0) + 1

                        stats['difficulties'] = difficulties
                    else:
                        stats['pdf_chunks'] = 0

                return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}", exc_info=True)
            return {'error': str(e)}

    def delete_pdf_collection(self, pdf_id: str) -> bool:
        """
        Delete all chunks for a specific PDF.

        Args:
            pdf_id: PDF identifier

        Returns:
            bool: True if successful
        """
        logger.info(f"Deleting chunks for PDF {pdf_id}")

        try:
            with self._lock:
                # Get all IDs for this PDF
                results = self.collection.get(
                    where={"pdf_id": pdf_id}
                )

                if results and results['ids']:
                    # Delete by IDs
                    self.collection.delete(
                        ids=results['ids']
                    )

                    # Persist changes
                    self.client.persist()

                    logger.info(f"✅ Deleted {len(results['ids'])} chunks for PDF {pdf_id}")
                    return True
                else:
                    logger.warning(f"No chunks found for PDF {pdf_id}")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete PDF collection: {e}", exc_info=True)
            return False

    def clear_all(self) -> bool:
        """
        Clear all documents from the collection.
        WARNING: This deletes all data!

        Returns:
            bool: True if successful
        """
        logger.warning("Clearing ALL documents from collection")

        try:
            with self._lock:
                # Delete the collection
                self.client.delete_collection(name=self.collection_name)

                # Recreate empty collection
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"description": "PDF learning content chunks"}
                )

                # Persist changes
                self.client.persist()

                logger.info("✅ Collection cleared successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to clear collection: {e}", exc_info=True)
            return False

    def get_vocabulary_chunks(self, pdf_id: str, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get vocabulary-focused chunks from a PDF.

        Args:
            pdf_id: PDF identifier
            difficulty: Optional difficulty filter

        Returns:
            List[dict]: Vocabulary chunks
        """
        logger.info(f"Getting vocabulary chunks for PDF {pdf_id}")

        try:
            with self._lock:
                where_clause = {
                    "pdf_id": pdf_id,
                    "is_vocabulary": True
                }

                if difficulty:
                    where_clause["difficulty"] = difficulty

                results = self.collection.get(
                    where=where_clause,
                    limit=100  # Limit to prevent excessive results
                )

                chunks = []
                if results and results['documents']:
                    for i in range(len(results['documents'])):
                        chunks.append({
                            'content': results['documents'][i],
                            'page': results['metadatas'][i].get('page', 0),
                            'difficulty': results['metadatas'][i].get('difficulty', 'Unknown')
                        })

                logger.info(f"Found {len(chunks)} vocabulary chunks")
                return chunks

        except Exception as e:
            logger.error(f"Failed to get vocabulary chunks: {e}", exc_info=True)
            return []

    def search_by_page(self, pdf_id: str, page_number: int) -> List[Dict[str, Any]]:
        """
        Get all chunks from a specific page.

        Args:
            pdf_id: PDF identifier
            page_number: Page number

        Returns:
            List[dict]: Chunks from the specified page
        """
        logger.info(f"Getting chunks from page {page_number} of PDF {pdf_id}")

        try:
            with self._lock:
                results = self.collection.get(
                    where={
                        "pdf_id": pdf_id,
                        "page": page_number
                    }
                )

                chunks = []
                if results and results['documents']:
                    for i in range(len(results['documents'])):
                        chunks.append({
                            'content': results['documents'][i],
                            'metadata': results['metadatas'][i]
                        })

                return chunks

        except Exception as e:
            logger.error(f"Failed to search by page: {e}", exc_info=True)
            return []

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of vector store.

        Returns:
            dict: Health status
        """
        try:
            count = self.collection.count()
            return {
                'status': 'healthy',
                'collection_name': self.collection_name,
                'document_count': count,
                'persist_directory': self.persist_directory,
                'model_name': self.model_name
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# Singleton instance (optional, can be managed by FastAPI app state)
_vector_store_instance: Optional[ChromaVectorStore] = None


def get_vector_store(persist_directory: str = "./data/chroma_db") -> ChromaVectorStore:
    """
    Get or create ChromaVectorStore singleton instance.

    Args:
        persist_directory: Directory for persistent storage

    Returns:
        ChromaVectorStore: Vector store instance
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        _vector_store_instance = ChromaVectorStore(persist_directory=persist_directory)

    return _vector_store_instance

