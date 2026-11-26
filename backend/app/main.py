
from fastapi import FastAPI

from backend.app.api.chat import router as chat_router
from backend.app.api.documents import router as documents_router
from backend.app.api.hr import router as hr_router
from backend.app.api.auth import router as auth_router
from backend.app.api.employee import router as employee_router

app = FastAPI(
    title="Enterprise AI Assistant",
    description="Enterprise GenAI Chatbot and Voice Assistant",
    version="1.0.0"
)


# Register chat routes
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(hr_router)
app.include_router(employee_router)

@app.get("/")
async def root():

    return {
        "message": "Enterprise AI Assistant is running"
    }


@app.get("/health")
async def health_check():

    return {
        "status": "healthy",
        "application": "Enterprise AI Assistant"
    }


@app.get("/about")
async def about():

    return {
        "project": "Enterprise AI Assistant",
        "backend": "FastAPI",
        "frontend": "Streamlit",
        "version": "1.0.0"
    }
