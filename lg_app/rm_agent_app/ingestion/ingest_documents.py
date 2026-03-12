import os
from dotenv import load_dotenv
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

load_dotenv()

CHROMA_CLOUD_API_KEY = os.getenv("CHROMA_CLOUD_API_KEY")

embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
print(f"embedding model initialized {embedding}")

vector_store = Chroma(
    collection_name="rm_knowledge_collection",
    embedding_function=embedding,
    persist_directory="./chroma_db"
)

pdf_files = [
    "../knowledge/Cooking_Guide.pdf",
    "../knowledge/Kitchen_Safety_Guidelines.pdf",
    "../knowledge/Recipe_Measurement_Guide.pdf"
]

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

all_docs = []
for pdf_path in pdf_files:
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    
    # Split each page into chunks
    chunks = text_splitter.split_documents(docs)
    
    # Add unique ID: filename_chunk_X
    filename = os.path.basename(pdf_path).replace(".pdf", "")
    for i, chunk in enumerate(chunks):
        chunk.id = f"{filename}_chunk_{i}"
    
    all_docs.extend(chunks)

vector_store.add_documents(documents=all_docs)
print(f"documents ingested successfully.. Total pages: {len(all_docs)}")

results = vector_store.similarity_search(
    query="can you tell me about safety guidelines included in the system?")

print(f"results: {len(results)}")
for i, doc in enumerate(results, 1):
    print(f"\n{i}. Source: {doc.metadata.get('source')}")
    print(f"   Content preview: {doc.page_content[:200]}...")
