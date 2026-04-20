import logging

from src.services.ragutils.vector_db import get_vector_db

logger = logging.getLogger(__name__)

db = get_vector_db()


def get_context(query_text, user_id, n_results=5):
    """
    Retrieves chunks and formats them into a string for the LLM.
    Returns: (formatted_context_string, list_of_sources)
    """

    try:
        results = db.search(query_text, user_id, n_results)
    except Exception as e:
        logger.error("Vector DB search failed: %s", e)
        return None, []

    context_string = ""
    sources = []

    if results and results.get("documents"):
        docs = results["documents"][0]
        metas = results["metadatas"][0]

        for text, meta in zip(docs, metas):
            citation = f"[Source: {meta['file_name']} | Page: {meta['page_number']}]"
            context_string += f"{citation}\n{text}\n\n"
            if meta["file_name"] not in sources:
                sources.append(meta["file_name"])

    if not context_string:
        return None, []

    return context_string, sources
