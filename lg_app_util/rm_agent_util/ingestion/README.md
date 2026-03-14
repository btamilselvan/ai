# Recipe Management Knowledge Base Ingestion

Ingests PDF documents into ChromaDB vector store for RAG-based recipe management assistant.

## Overview

This ingestion pipeline:
- Loads PDF documents from the `knowledge/` directory
- Splits documents into semantic chunks
- Generates embeddings using HuggingFace models
- Stores in ChromaDB with unique IDs to prevent duplicates

## Architecture

```
PDFs → PyPDFLoader → Text Splitter → Embeddings → ChromaDB
```

## Setup

### Prerequisites
```bash
uv add langchain-huggingface langchain-chroma langchain-community python-dotenv
```

### Directory Structure
```
ingestion/
├── ingestor.py           # Main ingestion script
├── chroma_db/            # Persistent vector store (auto-created)
└── ../knowledge/         # Source PDF documents
    ├── Recipe_Management_System.pdf
    ├── Kitchen_Safety_Guidelines.pdf
    └── Recipe_Measurement_Guide.pdf
```

## Configuration

### Embedding Model
- **Model**: `BAAI/bge-large-en-v1.5`
- **Dimensions**: 1024
- **Max Tokens**: 512

### Text Splitting
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 200 characters
- **Strategy**: RecursiveCharacterTextSplitter (splits on paragraphs → sentences → words)

### Vector Store
- **Database**: ChromaDB
- **Collection**: `rm_knowledge_collection`
- **Persistence**: `./chroma_db`

## Usage

### Run Ingestion
```bash
cd ingestion
uv run python ingest_documents.py
```

### Expected Output
```
embedding model initialized <HuggingFaceEmbeddings...>
documents ingested successfully.. Total pages: 15

results: 2

1. Source: ../knowledge/Kitchen_Safety_Guidelines.pdf
   Content preview: Kitchen Safety Guidelines
   1. Always wash hands before handling food...

2. Source: ../knowledge/Kitchen_Safety_Guidelines.pdf
   Content preview: Fire Safety
   Keep a fire extinguisher accessible...
```

## Key Features

### 1. Duplicate Prevention
Each chunk gets a unique ID based on filename and chunk index:
```python
chunk.id = f"{filename}_chunk_{i}"
# Example: Kitchen_Safety_Guidelines_chunk_0
```

**Behavior**: Re-running ingestion **upserts** (updates existing, inserts new) instead of creating duplicates.

### 2. Document Splitting
**Why Split?**
- Embedding models have token limits (~512 tokens)
- Smaller chunks = better semantic matching
- Prevents context dilution

**Example:**
- Input: 3 PDFs with 5 pages each = 15 pages
- Output: ~40-60 chunks (depending on content density)

### 3. Similarity Search
```python
results = vector_store.similarity_search(
    query="what are the safety guidelines in kitchen?", 
    k=2
)
```

Returns top 2 most semantically similar chunks.

## Troubleshooting

### Zero Results from Similarity Search
**Causes:**
1. Searching on wrong vector store instance
2. Documents not actually added
3. Embedding model mismatch

**Solution:**
```python
# ✅ Correct: Add to existing store
vector_store.add_documents(docs)
results = vector_store.similarity_search(query)

# ❌ Wrong: Create new store, search old one
db_store = vector_store.from_documents(docs)
results = vector_store.similarity_search(query)  # Empty!
```

### Duplicates on Re-run
**Cause:** Not using document IDs

**Solution:** Always assign unique IDs before adding:
```python
for i, chunk in enumerate(chunks):
    chunk.id = f"{filename}_chunk_{i}"
```

### Memory Issues with Large PDFs
**Solution:** Process PDFs in batches:
```python
for pdf_path in pdf_files:
    chunks = load_and_split(pdf_path)
    vector_store.add_documents(chunks)
    # Clears memory between files
```

## Integration with Agent

The ingested knowledge base is used by the Recipe Manager Agent:

```python
from langchain_chroma import Chroma
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

# Load existing vector store
embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
vector_store = Chroma(
    collection_name="rm_knowledge_collection",
    embedding_function=embedding,
    persist_directory="./ingestion/chroma_db"
)

# Retrieve context for user query
docs = vector_store.similarity_search(user_query, k=3)
context = "\n\n".join([doc.page_content for doc in docs])

# Inject into system prompt
system_prompt = SYSTEM_PROMPT.format(context=context)
```

## Best Practices

### 1. Incremental Updates
To add new documents without re-processing existing ones:
```python
new_docs = load_and_split("new_document.pdf")
vector_store.add_documents(new_docs)
```

### 2. Clear and Rebuild
To start fresh:
```bash
rm -rf chroma_db/
uv run python ingest_documents.py
```

### 3. Verify Ingestion
Always test similarity search after ingestion:
```python
results = vector_store.similarity_search("test query", k=1)
assert len(results) > 0, "No documents found!"
```

### 4. Monitor Chunk Count
```python
print(f"Total chunks: {len(all_docs)}")
# Expected: ~10-20 chunks per PDF page
```

## Performance

| Metric | Value |
|--------|-------|
| Ingestion Time | ~2-5 seconds per PDF |
| Embedding Generation | ~100ms per chunk |
| Search Latency | ~50-100ms |
| Storage | ~1MB per 100 chunks |

## References

- [LangChain PDF Loaders](https://python.langchain.com/docs/integrations/document_loaders/pypdf)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [HuggingFace Embeddings](https://huggingface.co/BAAI/bge-large-en-v1.5)
- [Text Splitting Strategies](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
