from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from vector_db import get_vector_db

# Get Vector DB Instance (Currently ChromaDB)
db = get_vector_db()

def ingest_file(file_path, file_id, file_name, user_id, file_type):
    docs = []
    
    # PDFs
    if file_type == "application/pdf":
        loader = PyPDFLoader(file_path)
        raw_docs = loader.load()
        
        # Add Page Numbers (Convert 0-index to 1-index)
        for doc in raw_docs:
            if "page" in doc.metadata:
                doc.metadata["page_number"] = doc.metadata["page"] + 1
            else:
                doc.metadata["page_number"] = 1
                
        # Split PDF
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = splitter.split_documents(raw_docs)

    # CODE / TEXT
    else:
        loader = TextLoader(file_path)
        raw_docs = loader.load()
        
        # Determine Language
        lang = Language.PYTHON if ".py" in file_name else Language.JS
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=lang, chunk_size=1000, chunk_overlap=100
        )
        docs = splitter.split_documents(raw_docs)
        
        # Default metadata for code
        for doc in docs:
            doc.metadata["page_number"] = 1

    # Prepare data for inserting chunks in the vector database
    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(docs):
        # Create ID: {file_id}_{index}
        chunk_id = f"{file_id}_{i}"
        
        # Clean Metadata
        meta = {
            "user_id": user_id,
            "source_file_id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "page_number": chunk.metadata.get("page_number", 1)
        }
        
        ids.append(chunk_id)
        documents.append(chunk.page_content)
        metadatas.append(meta)

    # insert chunks with metadata
    db.insert_chunks(ids, documents, metadatas)
    return len(ids)