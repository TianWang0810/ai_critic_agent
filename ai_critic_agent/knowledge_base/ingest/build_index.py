"""
Build FAISS Vector Index for Knowledge Base
Run once to create the searchable vector database
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


class FAISSIndexBuilder:
    """
    Builds FAISS vector index from markdown files
    """
    
    def __init__(
        self,
        data_dir: str = "knowledge_base/data",
        index_dir: str = "knowledge_base/vector_store",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the index builder
        
        Args:
            data_dir: Directory containing markdown files
            index_dir: Where to save FAISS index and metadata
            embedding_model: Sentence transformer model
        """
        self.data_dir = Path(data_dir)
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Load embedding model
        print(f"Loading embedding model: {embedding_model}")
        
        # Set environment to avoid multiprocessing issues on Mac M4
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        os.environ['OMP_NUM_THREADS'] = '1'
        
        self.embedding_model = SentenceTransformer(
            embedding_model,
            device='cpu'  # Explicitly use CPU for Mac compatibility
        )
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded, embedding dimension: {self.embedding_dim}")
    
    def load_markdown_files(self) -> List[Dict]:
        """
        Load all markdown files from data/ directory
        
        Returns:
            List of document dictionaries
        """
        documents = []
        
        # Iterate through category directories
        for category_dir in self.data_dir.iterdir():
            if not category_dir.is_dir():
                continue
            
            category = category_dir.name
            print(f"\n📂 Loading from {category}/...")
            
            # Load each markdown file
            for md_file in category_dir.glob("*.md"):
                if md_file.name == "TEMPLATE.md":
                    continue  # Skip template
                
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    documents.append({
                        "source": md_file.name,
                        "category": category,
                        "full_path": str(md_file),
                        "content": content
                    })
                    print(f"   ✓ {md_file.name}")
                    
                except Exception as e:
                    print(f"   ✗ Error loading {md_file.name}: {e}")
        
        print(f"\n✅ Loaded {len(documents)} documents")
        return documents
    
    def parse_markdown_sections(self, content: str) -> List[Dict]:
        """
        Parse markdown into sections based on ## headers
        This is KEY for semantic chunking!
        
        Args:
            content: Full markdown text
            
        Returns:
            List of section dictionaries
        """
        sections = []
        current_section = {"title": "", "content": ""}
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('## '):
                # Save previous section (skip if too short)
                if current_section["content"].strip():
                    # Only add sections with substantial content (>50 chars)
                    if len(current_section["content"].strip()) > 50:
                        sections.append(current_section)
                
                # Start new section
                current_section = {
                    "title": line[3:].strip(),  # Remove "## "
                    "content": ""
                }
            elif line.startswith('# '):
                # Document title - include in chunk for context
                current_section["content"] += line + "\n"
            else:
                current_section["content"] += line + "\n"
        
        # Save last section
        if current_section["content"].strip() and len(current_section["content"].strip()) > 50:
            sections.append(current_section)
        
        return sections
    
    def create_chunks(self, documents: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """
        Create semantic chunks from documents
        
        Strategy (OPTIMIZED):
        - Combine small sections (<150 words) with previous section
        - Keep medium sections (150-600 words) as-is
        - Split very large sections (>600 words) at paragraph boundaries
        
        Args:
            documents: List of document dicts
            
        Returns:
            Tuple of (chunk_texts, chunk_metadatas)
        """
        all_chunks = []
        all_metadata = []
        
        for doc in documents:
            sections = self.parse_markdown_sections(doc["content"])
            
            merged_sections = []
            current_merged = None
            
            for idx, section in enumerate(sections):
                title = section["title"]
                content = section["content"].strip()
                
                if not content:
                    continue
                
                word_count = len(content.split())
                
                # Strategy: Merge small sections with previous
                if word_count < 150 and current_merged:
                    # Append to previous section
                    current_merged["content"] += f"\n\n{title}\n\n{content}" if title else f"\n\n{content}"
                    current_merged["word_count"] = len(current_merged["content"].split())
                elif word_count < 150:
                    # Start new merge buffer
                    current_merged = {
                        "title": title,
                        "content": f"{title}\n\n{content}" if title else content,
                        "section_index": idx,
                        "word_count": word_count
                    }
                else:
                    # Save previous merged section
                    if current_merged:
                        merged_sections.append(current_merged)
                        current_merged = None
                    
                    # Add current section as-is
                    merged_sections.append({
                        "title": title,
                        "content": f"{title}\n\n{content}" if title else content,
                        "section_index": idx,
                        "word_count": word_count
                    })
            
            # Don't forget last merged section
            if current_merged:
                merged_sections.append(current_merged)
            
            # Create chunks from merged sections
            for idx, section in enumerate(merged_sections):
                metadata = {
                    "source": doc["source"],
                    "category": doc["category"],
                    "section_title": section["title"],
                    "section_index": idx,
                    "total_sections": len(merged_sections),
                    "word_count": section["word_count"]
                }
                
                all_chunks.append(section["content"])
                all_metadata.append(metadata)
        
        print(f"\n✅ Created {len(all_chunks)} chunks from {len(documents)} documents")
        avg_words = sum(m["word_count"] for m in all_metadata) // len(all_metadata)
        print(f"📊 Average chunk size: {avg_words} words")
        
        return all_chunks, all_metadata
    
    def build_faiss_index(
        self,
        chunk_texts: List[str],
        chunk_metadata: List[Dict]
    ) -> Tuple[faiss.Index, List[Dict]]:
        """
        Build FAISS index from chunks
        
        Args:
            chunk_texts: List of text chunks
            chunk_metadata: List of metadata dicts
            
        Returns:
            Tuple of (faiss_index, metadata_list)
        """
        print(f"\n🧠 Generating embeddings for {len(chunk_texts)} chunks...")
        
        # Generate embeddings (disable multiprocessing for Mac M4)
        embeddings = self.embedding_model.encode(
            chunk_texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=32,  # Smaller batch size for stability
            device='cpu'    # Explicitly use CPU
        )
        
        print(f"✅ Embeddings shape: {embeddings.shape}")
        
        # Create FAISS index
        # Using IndexFlatIP for exact inner product search (cosine similarity)
        print(f"\n📊 Building FAISS index...")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        
        # Add vectors to index
        index.add(embeddings.astype('float32'))
        
        print(f"✅ FAISS index created: {index.ntotal} vectors")
        
        return index, chunk_metadata
    
    def save_index(
        self,
        faiss_index: faiss.Index,
        metadata: List[Dict],
        chunk_texts: List[str]
    ):
        """
        Save FAISS index and metadata to disk
        
        Args:
            faiss_index: The FAISS index
            metadata: List of metadata dicts
            chunk_texts: Original chunk texts
        """
        # Save FAISS index
        index_path = self.index_dir / "faiss_index.bin"
        faiss.write_index(faiss_index, str(index_path))
        print(f"✅ FAISS index saved to {index_path}")
        
        # Save metadata as pickle (includes chunk texts)
        metadata_path = self.index_dir / "metadata.pkl"
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                "metadata": metadata,
                "chunk_texts": chunk_texts,
                "embedding_dim": self.embedding_dim,
                "total_chunks": len(chunk_texts)
            }, f)
        print(f"✅ Metadata saved to {metadata_path}")
        
        # Save stats as JSON for easy inspection
        stats = {
            "total_documents": len(set(m["source"] for m in metadata)),
            "total_chunks": len(chunk_texts),
            "categories": {},
            "embedding_dimension": self.embedding_dim
        }
        
        # Count chunks per category
        for meta in metadata:
            cat = meta["category"]
            stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
        
        stats_path = self.index_dir / "index_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"✅ Stats saved to {stats_path}")
    
    def build(self):
        """
        Main method: Build complete index
        """
        print("=" * 70)
        print("FAISS Knowledge Base Index Builder")
        print("=" * 70)
        
        # Step 1: Load documents
        documents = self.load_markdown_files()
        
        if not documents:
            print("❌ No documents found! Add .md files to data/ subdirectories")
            return
        
        # Step 2: Create chunks
        chunk_texts, chunk_metadata = self.create_chunks(documents)
        
        # Step 3: Build FAISS index
        faiss_index, metadata = self.build_faiss_index(chunk_texts, chunk_metadata)
        
        # Step 4: Save everything
        self.save_index(faiss_index, metadata, chunk_texts)
        
        print("\n" + "=" * 70)
        print("✅ INDEX BUILD COMPLETE!")
        print("=" * 70)
        print(f"Documents: {len(documents)}")
        print(f"Chunks: {len(chunk_texts)}")
        print(f"Index file: {self.index_dir}/faiss_index.bin")
        print(f"Metadata file: {self.index_dir}/metadata.pkl")
    
    def verify_index(self):
        """
        Test the index with sample queries
        """
        print("\n" + "=" * 70)
        print("🧪 TESTING INDEX")
        print("=" * 70)
        
        # Load the index
        index_path = self.index_dir / "faiss_index.bin"
        metadata_path = self.index_dir / "metadata.pkl"
        
        if not index_path.exists():
            print("❌ Index not found. Run build() first.")
            return
        
        index = faiss.read_index(str(index_path))
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
        
        metadata = data["metadata"]
        chunk_texts = data["chunk_texts"]
        
        # Test queries
        test_queries = [
            "users won't pay for subscription services",
            "competition from big tech companies",
            "technology is not mature enough"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Search
            k = 3
            distances, indices = index.search(query_embedding.astype('float32'), k)
            
            # Display results
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                meta = metadata[idx]
                chunk = chunk_texts[idx]
                similarity = dist  # Already normalized, so distance = similarity
                
                print(f"\n  {i+1}. [{meta['category']}] {meta['source']}")
                print(f"     Section: {meta['section_title']}")
                print(f"     Similarity: {similarity:.3f}")
                print(f"     Preview: {chunk[:150]}...")


# ============================================================
# Main Execution
# ============================================================

if __name__ == "__main__":
    builder = FAISSIndexBuilder()
    
    # Build the index
    builder.build()
    
    # Verify it works
    builder.verify_index()