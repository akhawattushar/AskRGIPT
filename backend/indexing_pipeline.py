"""
Document Indexing Pipeline
Automated indexing with progress tracking, incremental updates, and validation.
"""
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from document_processor import DocumentProcessor
from vector_store import VectorStore
from config import config


class IndexingPipeline:
    def __init__(self):
        """Initialize indexing pipeline."""
        self.processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.index_metadata_file = os.path.join(config.VECTOR_DB_DIR, "index_metadata.json")
        self.index_metadata = self._load_index_metadata()
    
    def _load_index_metadata(self) -> Dict:
        """Load indexing metadata."""
        if os.path.exists(self.index_metadata_file):
            try:
                with open(self.index_metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "indexed_files": {},
            "last_indexed": None,
            "total_chunks": 0
        }
    
    def _save_index_metadata(self):
        """Save indexing metadata."""
        os.makedirs(os.path.dirname(self.index_metadata_file), exist_ok=True)
        with open(self.index_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.index_metadata, f, indent=2, ensure_ascii=False)
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _is_file_indexed(self, file_path: str) -> bool:
        """Check if file is already indexed and unchanged."""
        if not os.path.exists(file_path):
            return False
        
        file_hash = self._get_file_hash(file_path)
        file_mtime = os.path.getmtime(file_path)
        
        indexed_info = self.index_metadata.get("indexed_files", {}).get(file_path)
        
        if indexed_info:
            # Check if file hash matches (file unchanged)
            if indexed_info.get("hash") == file_hash:
                return True
            # Check if file modification time matches and hash is same
            if indexed_info.get("mtime") == file_mtime:
                return True
        
        return False
    
    def _mark_file_indexed(self, file_path: str, chunk_count: int):
        """Mark file as indexed."""
        file_hash = self._get_file_hash(file_path)
        file_mtime = os.path.getmtime(file_path)
        
        if "indexed_files" not in self.index_metadata:
            self.index_metadata["indexed_files"] = {}
        
        self.index_metadata["indexed_files"][file_path] = {
            "hash": file_hash,
            "mtime": file_mtime,
            "chunk_count": chunk_count,
            "indexed_at": datetime.now().isoformat()
        }
    
    def index_all_documents(self, incremental: bool = True, clear_existing: bool = False):
        """
        Index all documents in the data directory.
        
        Args:
            incremental: Only process new/changed files
            clear_existing: Clear existing index before indexing
        """
        print(f"\n{'='*60}")
        print(f"📚 Document Indexing Pipeline")
        print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        all_chunks = []
        all_metadata = []
        processed_files = []
        skipped_files = []
        
        # Process all subdirectories
        folders = ["pdfs", "notices", "policies", "handbooks"]
        
        for folder in folders:
            folder_path = os.path.join(config.DATA_DIR, folder)
            if not os.path.exists(folder_path):
                continue
            
            print(f"\n📁 Processing folder: {folder}")
            
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                
                # Check if file is supported
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in config.SUPPORTED_FORMATS:
                    continue
                
                # Check if already indexed (incremental mode)
                if incremental and self._is_file_indexed(file_path):
                    print(f"   ⏭️  Skipping (already indexed): {filename}")
                    skipped_files.append(file_path)
                    continue
                
                # Process document
                print(f"   📄 Processing: {filename}")
                chunks, metadata = self.processor.process_document(file_path)
                
                if chunks:
                    all_chunks.extend(chunks)
                    all_metadata.extend(metadata)
                    processed_files.append(file_path)
                    self._mark_file_indexed(file_path, len(chunks))
        
        # Index documents
        if all_chunks:
            print(f"\n📥 Indexing {len(all_chunks)} chunks...")
            self.vector_store.add_documents(
                all_chunks, 
                all_metadata,
                clear_existing=clear_existing
            )
            
            self.index_metadata["last_indexed"] = datetime.now().isoformat()
            self.index_metadata["total_chunks"] = len(all_chunks)
            self._save_index_metadata()
            
            print(f"\n✅ Indexing complete!")
            print(f"   Processed: {len(processed_files)} files")
            print(f"   Skipped: {len(skipped_files)} files")
            print(f"   Total chunks: {len(all_chunks)}")
        else:
            print("\n⚠️  No new documents to index")
    
    def validate_index(self) -> Dict:
        """
        Validate the index integrity.
        
        Returns:
            Dictionary with validation results
        """
        print("\n🔍 Validating index...")
        
        stats = self.vector_store.get_collection_stats()
        
        # Check metadata consistency
        issues = []
        
        if stats['total_documents'] == 0:
            issues.append("Index is empty")
        
        # Get sample documents
        sample = self.vector_store.collection.peek(limit=min(10, stats['total_documents']))
        
        if sample['metadatas']:
            for i, meta in enumerate(sample['metadatas']):
                if 'source' not in meta:
                    issues.append(f"Document {i} missing 'source' metadata")
        
        validation_result = {
            "valid": len(issues) == 0,
            "total_documents": stats['total_documents'],
            "categories": stats['categories'],
            "issues": issues
        }
        
        if validation_result["valid"]:
            print("✅ Index validation passed")
        else:
            print(f"⚠️  Index validation found {len(issues)} issues:")
            for issue in issues:
                print(f"   - {issue}")
        
        return validation_result
    
    def reindex_file(self, file_path: str):
        """Re-index a specific file."""
        print(f"\n🔄 Re-indexing: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        # Remove from metadata (force re-indexing)
        if file_path in self.index_metadata.get("indexed_files", {}):
            del self.index_metadata["indexed_files"][file_path]
        
        # Process and index
        chunks, metadata = self.processor.process_document(file_path)
        
        if chunks:
            self.vector_store.add_documents(chunks, metadata)
            self._mark_file_indexed(file_path, len(chunks))
            self._save_index_metadata()
            print(f"✅ Re-indexed: {len(chunks)} chunks")
        else:
            print(f"⚠️  No chunks extracted from file")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Document Indexing Pipeline")
    parser.add_argument("--incremental", action="store_true", default=True,
                       help="Only process new/changed files")
    parser.add_argument("--full", action="store_true",
                       help="Full re-index (clears existing)")
    parser.add_argument("--validate", action="store_true",
                       help="Validate index integrity")
    
    args = parser.parse_args()
    
    pipeline = IndexingPipeline()
    
    if args.validate:
        pipeline.validate_index()
    elif args.full:
        pipeline.index_all_documents(incremental=False, clear_existing=True)
    else:
        pipeline.index_all_documents(incremental=args.incremental)

