from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.schema.models import User
from src.services.authservice import get_current_active_user
from src.services.ragutils.vector_db import get_vector_db

DocsRouter = APIRouter(prefix="/docs", tags=["documents"])

db = get_vector_db()


class DocumentInfo(BaseModel):
    file_name: str
    file_id: str
    chunk_count: int


@DocsRouter.get("/", response_model=list[DocumentInfo])
async def list_documents(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """List all documents uploaded by the current user."""
    results = db.collection.get(
        where={"user_id": current_user.identifier},
    )

    file_map: dict[str, DocumentInfo] = {}
    for meta in results["metadatas"]:
        fid = meta["source_file_id"]
        if fid not in file_map:
            file_map[fid] = DocumentInfo(
                file_name=meta["file_name"],
                file_id=fid,
                chunk_count=0,
            )
        file_map[fid].chunk_count += 1

    return list(file_map.values())


@DocsRouter.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    file_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Delete a document and all its chunks from the vector database."""
    # Verify the file belongs to this user
    results = db.collection.get(
        where={"$and": [{"source_file_id": file_id}, {"user_id": current_user.identifier}]},
        limit=1,
    )

    if not results["ids"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not owned by you.",
        )

    db.delete_file(file_id)
    return None
