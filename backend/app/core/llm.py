import os
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from backend.app.config import settings


@lru_cache(maxsize=1)
def get_llm():

    os.environ["GOOGLE_API_KEY"] = settings.google_api_key

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        max_retries=3
    )

    return llm