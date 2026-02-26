from src.ragutils.vector_db import get_vector_db

# Initialize DB connection
db = get_vector_db()


def get_context(query_text, user_id, n_results=5):
    """
    Retrieves chunks and formats them into a string for the LLM.
    Returns: (formatted_context_string, list_of_sources)
    """

    # DB Query
    results = db.search(query_text, user_id, n_results)

    # Merge into a single Context String
    context_string = ""
    sources = []

    # Chroma returns lists of lists (e.g. results['documents'][0])
    if results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0]

        for i, (text, meta) in enumerate(zip(docs, metas)):
            # Create a clean citation header for each chunk
            citation = f"[Source: {meta['file_name']} | Page: {meta['page_number']}]"

            # Append to the giant string
            context_string += f"{citation}\n{text}\n\n"

            # Keep track of unique sources for UI display (optional)
            if meta["file_name"] not in sources:
                sources.append(meta["file_name"])

    if not context_string:
        return None, []

    return context_string, sources
