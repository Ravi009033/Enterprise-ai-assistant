from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.app.rag.vector_store import get_vector_store


def ingest_pdf(file_path: str, original_filename: str):

    # 1. Load PDF
    loader = PyPDFLoader(file_path)

    documents = loader.load()

    # 2. Validate extracted content
    if not documents or not any(
        document.page_content.strip()
        for document in documents
    ):
        raise ValueError("No readable text found in PDF")

    # 3. Add original filename to document metadata
    for document in documents:
        document.metadata["source"] = original_filename

    # 4. Create text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    # 5. Split documents into chunks
    chunks = text_splitter.split_documents(documents)

    if not chunks:
        raise ValueError("Unable to create document chunks")

    # 6. Store chunks and embeddings in ChromaDB
    vector_store = get_vector_store()

    vector_store.add_documents(chunks)

    return {
        "filename": original_filename,
        "total_pages": len(documents),
        "total_chunks": len(chunks),
        "status": "indexed"
    }