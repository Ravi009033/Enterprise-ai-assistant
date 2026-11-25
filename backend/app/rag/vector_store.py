from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma

from backend.app.rag.embeddings import get_embeddings


BASE_DIR = Path(__file__).resolve().parents[2]

CHROMA_DIRECTORY = BASE_DIR / "chroma_db"


@lru_cache(maxsize=1)
def get_vector_store():

    vector_store = Chroma(
        collection_name="enterprise_documents",
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIRECTORY)
    )

    return vector_store