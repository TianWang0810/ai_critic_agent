"""
FAISS-based Knowledge Base Retriever
Provides query API for the critic knowledge base
"""

import pickle
from pathlib import Path
from typing import List, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from common.schemas import (
    RetrievalResult,
    EvidenceItem,
    RiskCategory
)
from common.constants import (
    DEFAULT_EVIDENCE_COUNT,
    MIN_RELEVANCE_SCORE
)


class CriticKnowledgeBase:
    """
    FAISS-based knowledge base retriever
    
    Provides semantic search over startup failure cases
    """
    
    def __init__(
        self,
        index_dir: str = "knowledge_base/vector_store",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the retriever
        
        Args:
            index_dir: Directory containing FAISS index and metadata
            embedding_model: Same model used during indexing
        """
        # Mac M4 FIX: Set environment before loading models
        import os
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        os.environ['OMP_NUM_THREADS'] = '1'
        
        self.index_dir = Path(index_dir)
        
        # Check if index exists
        index_path = self.index_dir / "faiss_index.bin"
        metadata_path = self.index_dir / "metadata.pkl"
        
        if not index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {index_dir}. "
                "Please run 'python -m knowledge_base.ingest.build_index' first."
            )
        
        # Load FAISS index
        print(f"Loading FAISS index from {index_path}...")
        self.index = faiss.read_index(str(index_path))
        print(f"✅ Loaded index with {self.index.ntotal} vectors")
        
        # Load metadata
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
        
        self.metadata = data["metadata"]
        self.chunk_texts = data["chunk_texts"]
        self.embedding_dim = data["embedding_dim"]
        
        # Load embedding model with Mac M4 safe settings
        print(f"Loading embedding model: {embedding_model}...")
        self.embedding_model = SentenceTransformer(
            embedding_model,
            device='cpu'  # Force CPU for Mac M4
        )
        print(f"✅ Model loaded (dim={self.embedding_dim})")
    
    def query(
        self,
        assumption: str,
        category: Optional[RiskCategory] = None,
        top_k: int = DEFAULT_EVIDENCE_COUNT,
        min_score: float = MIN_RELEVANCE_SCORE
    ) -> RetrievalResult:
        """
        Query the knowledge base for relevant evidence
        
        Args:
            assumption: The assumption to find counter-evidence for
            category: Optional risk category filter
            top_k: Number of results to return
            min_score: Minimum relevance score (0-1)
            
        Returns:
            RetrievalResult: Structured result with evidence items
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            [assumption],
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        # Search FAISS index
        # Get MORE candidates for better filtering
        search_k = min(top_k * 5, self.index.ntotal)  # 增加搜索范围
        distances, indices = self.index.search(
            query_embedding.astype('float32'),
            search_k
        )
        
        # Build evidence items
        evidence_items = []
        
        for dist, idx in zip(distances[0], indices[0]):
            # Skip invalid indices
            if idx == -1 or idx >= len(self.metadata):
                continue
            
            meta = self.metadata[idx]
            chunk_text = self.chunk_texts[idx]
            
            # Filter by category if specified
            if category and meta["category"] != category.value:
                continue
            
            # Convert distance to similarity score
            # FAISS IndexFlatIP returns inner product (higher = more similar)
            similarity_score = float(dist)
            
            # Apply dynamic threshold based on query complexity
            # Shorter queries need lower threshold
            adjusted_min_score = min_score
            if len(assumption.split()) < 5:  # Short query
                adjusted_min_score = max(0.2, min_score - 0.1)
            
            # Filter by minimum score
            if similarity_score < adjusted_min_score:
                continue
            
            # Create evidence item
            evidence_item = EvidenceItem(
                source=meta["source"],
                content=chunk_text,
                relevance_score=round(similarity_score, 3),
                category=RiskCategory(meta["category"])
            )
            evidence_items.append(evidence_item)
            
            # Stop if we have enough high-quality results
            if len(evidence_items) >= top_k and evidence_items[-1].relevance_score > 0.5:
                break
        
        # Sort by relevance (should already be sorted, but just in case)
        evidence_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return RetrievalResult(
            query=assumption,
            evidence=evidence_items[:top_k],
            total_retrieved=len(evidence_items)
        )
    
    def query_by_category(
        self,
        category: RiskCategory,
        top_k: int = 10
    ) -> List[EvidenceItem]:
        """
        Get top evidence items for a specific category
        
        Args:
            category: Risk category to retrieve
            top_k: Number of items to return
            
        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []
        
        for idx, (meta, chunk_text) in enumerate(zip(self.metadata, self.chunk_texts)):
            if meta["category"] == category.value:
                evidence_items.append(EvidenceItem(
                    source=meta["source"],
                    content=chunk_text,
                    relevance_score=1.0,  # Not using similarity here
                    category=category
                ))
                
                if len(evidence_items) >= top_k:
                    break
        
        return evidence_items
    
    def get_stats(self) -> dict:
        """
        Get knowledge base statistics
        
        Returns:
            dict: Statistics including counts by category
        """
        category_counts = {}
        for meta in self.metadata:
            cat = meta["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        unique_sources = set(meta["source"] for meta in self.metadata)
        
        return {
            "total_chunks": len(self.metadata),
            "total_documents": len(unique_sources),
            "categories": category_counts,
            "embedding_dimension": self.embedding_dim,
            "index_type": type(self.index).__name__
        }
    
    def get_chunk_by_id(self, chunk_id: int) -> tuple:
        """
        Get specific chunk by index ID
        
        Args:
            chunk_id: Index ID of the chunk
            
        Returns:
            Tuple of (metadata, chunk_text)
        """
        if 0 <= chunk_id < len(self.metadata):
            return self.metadata[chunk_id], self.chunk_texts[chunk_id]
        return None, None


# ============================================================
# Testing / Demo Usage
# ============================================================

if __name__ == "__main__":
    print("🔍 Testing FAISS Knowledge Base Retriever\n")
    
    # Initialize
    try:
        kb = CriticKnowledgeBase()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\nPlease run: python -m knowledge_base.ingest.build_index")
        exit(1)
    
    # Test 1: Basic query
    print("=" * 70)
    print("TEST 1: Query with assumption")
    print("=" * 70)
    
    result = kb.query(
        assumption="College students will pay for subscription services",
        category=RiskCategory.MARKET,
        top_k=3
    )
    
    print(f"\nQuery: {result.query}")
    print(f"Found {result.total_retrieved} relevant evidence items:\n")
    
    for i, evidence in enumerate(result.evidence, 1):
        print(f"{i}. [{evidence.category.value}] {evidence.source}")
        print(f"   Relevance: {evidence.relevance_score:.3f}")
        print(f"   Preview: {evidence.content[:200]}...")
        print()
    
    # Test 2: Query without category filter
    print("\n" + "=" * 70)
    print("TEST 2: Query without category filter")
    print("=" * 70)
    
    result = kb.query(
        assumption="AI technology is mature enough for production use",
        top_k=5
    )
    
    print(f"\nQuery: {result.query}")
    print(f"Found {result.total_retrieved} results across categories:\n")
    
    for i, evidence in enumerate(result.evidence, 1):
        print(f"{i}. [{evidence.category.value}] {evidence.source}")
        print(f"   Score: {evidence.relevance_score:.3f}")
    
    # Test 3: Browse by category
    print("\n" + "=" * 70)
    print("TEST 3: Browse competition category")
    print("=" * 70)
    
    competition_evidence = kb.query_by_category(
        category=RiskCategory.COMPETITION,
        top_k=3
    )
    
    print(f"\nTop {len(competition_evidence)} items from COMPETITION category:\n")
    for evidence in competition_evidence:
        print(f"- {evidence.source}")
        print(f"  {evidence.content[:150]}...\n")
    
    # Test 4: Statistics
    print("\n" + "=" * 70)
    print("TEST 4: Knowledge Base Statistics")
    print("=" * 70)
    
    stats = kb.get_stats()
    print(f"\nTotal chunks: {stats['total_chunks']}")
    print(f"Total documents: {stats['total_documents']}")
    print(f"Index type: {stats['index_type']}")
    print(f"\nChunks by category:")
    for category, count in sorted(stats['categories'].items()):
        print(f"  - {category}: {count} chunks")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)