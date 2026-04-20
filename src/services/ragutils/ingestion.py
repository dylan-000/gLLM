import logging
import os

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

from src.services.ragutils.vector_db import get_vector_db

logger = logging.getLogger(__name__)

db = get_vector_db()

MAX_FILE_SIZE_MB = 50
SUPPORTED_TEXT_EXTENSIONS = {".py", ".txt", ".md", ".csv", ".json", ".xml", ".html", ".css", ".js", ".ts", ".yaml", ".yml"}


def validate_file(file_path, file_name, file_type):
    """Validate file size and type before ingestion."""
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File '{file_name}' is {file_size_mb:.1f}MB, exceeding the {MAX_FILE_SIZE_MB}MB limit."
        )

    ext = os.path.splitext(file_name)[1].lower()
    if file_type != "application/pdf" and ext not in SUPPORTED_TEXT_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: '{ext}'. Supported: PDF, {', '.join(sorted(SUPPORTED_TEXT_EXTENSIONS))}"
        )


def is_duplicate(file_name, user_id):
    """Check if a file with the same name has already been ingested by this user."""
    results = db.collection.get(
        where={"$and": [{"user_id": user_id}, {"file_name": file_name}]},
        limit=1,
    )
    return len(results["ids"]) > 0


def ingest_file(file_path, file_id, file_name, file_type, user_id):
    """Ingest a file into the vector database with validation and error handling."""

    try:
        validate_file(file_path, file_name, file_type)
    except ValueError as e:
        logger.warning("File validation failed: %s", e)
        return 0, str(e)

    if is_duplicate(file_name, user_id):
        msg = f"File '{file_name}' has already been ingested. Skipping duplicate."
        logger.info(msg)
        return 0, msg

    try:
        docs = _load_and_split(file_path, file_name, file_type)
    except Exception as e:
        msg = f"Failed to process file '{file_name}': {e}"
        logger.error(msg)
        return 0, msg

    if not docs:
        msg = f"No content extracted from '{file_name}'."
        logger.warning(msg)
        return 0, msg

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(docs):
        chunk_id = f"{file_id}_{i}"
        meta = {
            "user_id": user_id,
            "source_file_id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "page_number": chunk.metadata.get("page_number", 1),
        }
        ids.append(chunk_id)
        documents.append(chunk.page_content)
        metadatas.append(meta)

    try:
        db.insert_chunks(ids, documents, metadatas)
    except Exception as e:
        msg = f"Failed to store chunks for '{file_name}': {e}"
        logger.error(msg)
        return 0, msg

    logger.info("Ingested '%s': %d chunks", file_name, len(ids))
    return len(ids), None


def _load_and_split(file_path, file_name, file_type):
    """Load a file and split it into chunks."""

    if file_type == "application/pdf":
        loader = PyPDFLoader(file_path)
        raw_docs = loader.load()

        for doc in raw_docs:
            if "page" in doc.metadata:
                doc.metadata["page_number"] = doc.metadata["page"] + 1
            else:
                doc.metadata["page_number"] = 1

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = splitter.split_documents(raw_docs)

    else:
        loader = TextLoader(file_path)
        raw_docs = loader.load()
        lang = Language.PYTHON if file_name.endswith(".py") else Language.MARKDOWN

        splitter = RecursiveCharacterTextSplitter.from_language(
            language=lang, chunk_size=1000, chunk_overlap=100
        )
        docs = splitter.split_documents(raw_docs)

        for doc in docs:
            doc.metadata["page_number"] = 1

    return docs
