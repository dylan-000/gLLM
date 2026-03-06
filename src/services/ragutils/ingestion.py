from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

from src.services.ragutils.vector_db import get_vector_db


db = get_vector_db()


def ingest_file(file_path, file_id, file_name, file_type, user_id):

    print(file_path, file_name, file_type)
    docs = []

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
        lang = Language.PYTHON if ".py" in file_name else Language.MARKDOWN
        print(f"inside lang block, lang is {lang}")

        splitter = RecursiveCharacterTextSplitter.from_language(
            language=lang, chunk_size=1000, chunk_overlap=100
        )
        docs = splitter.split_documents(raw_docs)

        for doc in docs:
            doc.metadata["page_number"] = 1

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

    db.insert_chunks(ids, documents, metadatas)
    return len(ids)
