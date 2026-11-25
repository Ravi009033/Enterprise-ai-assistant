import asyncio
import uuid

from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.rag.ingestion import ingest_pdf


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)

BASE_DIR = Path(__file__).resolve().parents[2]

DOCUMENTS_DIRECTORY = BASE_DIR / "data" / "documents"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    # 1. Validate filename and extension
    original_filename = Path(file.filename or "").name

    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    # 2. Read uploaded file
    file_content = await file.read()

    # 3. Validate file size
    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds 10 MB limit"
        )

    # 4. Validate PDF signature
    if not file_content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file"
        )

    # 5. Create upload directory
    DOCUMENTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    # 6. Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}.pdf"

    file_path = DOCUMENTS_DIRECTORY / unique_filename

    # 7. Save uploaded file
    file_path.write_bytes(file_content)

    try:

        # 8. Run PDF ingestion without blocking async event loop
        result = await asyncio.to_thread(
            ingest_pdf,
            str(file_path),
            original_filename
        )

        return result

    except ValueError as error:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:

        file_path.unlink(missing_ok=True)

        print("PDF INGESTION ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to process PDF document"
        ) from error

    finally:
        await file.close()