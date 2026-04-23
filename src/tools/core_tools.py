"""Core tools for the Chainlit application using Registry Pattern."""

import json
import chainlit as cl


render_pdf_schema = {
    "name": "render_pdf",
    "description": "Renders a remote PDF document in the chat interface so the user can read it. Use this when the user asks to view or read a PDF from a given URL.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The remote URL of the PDF to render.",
            },
            "name": {
                "type": "string",
                "description": "A descriptive name for the PDF document.",
            },
        },
        "required": ["url", "name"],
    },
}


async def render_pdf(url: str, name: str) -> str:
    """Takes a remote PDF URL and renders it in the Chainlit UI."""
    try:
        pdf_element = cl.Pdf(name=name, url=url, display="side")
        await cl.Message(
            content=f"Rendering PDF: **{name}**", elements=[pdf_element]
        ).send()
        # Return structured JSON so on_chat_resume can reconstruct the element
        return json.dumps({"status": "rendered", "name": name, "url": url})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


# Registry mapping tool names to their schemas and executable functions
TOOL_REGISTRY = {"render_pdf": {"schema": render_pdf_schema, "function": render_pdf}}


def get_regular_tools():
    """Returns a list of all tool schemas in the TOOL_REGISTRY.

    This function extracts the schema for each tool in the registry
    and returns them as a list suitable for passing to the OpenAI API.

    Returns:
        list: A list of tool schema dictionaries.
    """
    return [tool_config["schema"] for tool_config in TOOL_REGISTRY.values()]
