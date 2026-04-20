"""Unit tests for the RAG pipeline (ingestion, retrieval, vector_db)."""

import os
import sys
import importlib
import pytest
from unittest.mock import MagicMock, patch

# Add src to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
sys.path.insert(0, src_path)


@pytest.fixture
def mock_db():
    """Patch get_vector_db before importing ingestion/retrieval modules."""
    mock = MagicMock()
    mock.collection = MagicMock()

    with patch("src.services.ragutils.vector_db.get_vector_db", return_value=mock):
        # Force re-import so module-level db = get_vector_db() uses the mock
        import src.services.ragutils.ingestion as ingestion_mod
        import src.services.ragutils.retrieval as retrieval_mod

        ingestion_mod.db = mock
        retrieval_mod.db = mock

        yield mock, ingestion_mod, retrieval_mod


# --- Ingestion Tests ---


class TestValidateFile:
    """Tests for file validation logic."""

    def test_rejects_oversized_file(self, tmp_path, mock_db):
        _, ingestion, _ = mock_db

        large_file = tmp_path / "big.pdf"
        large_file.write_bytes(b"x" * (ingestion.MAX_FILE_SIZE_MB * 1024 * 1024 + 1))

        with pytest.raises(ValueError, match="exceeding the"):
            ingestion.validate_file(str(large_file), "big.pdf", "application/pdf")

    def test_accepts_valid_pdf(self, tmp_path, mock_db):
        _, ingestion, _ = mock_db

        small_file = tmp_path / "small.pdf"
        small_file.write_bytes(b"x" * 1000)

        ingestion.validate_file(str(small_file), "small.pdf", "application/pdf")

    def test_rejects_unsupported_extension(self, tmp_path, mock_db):
        _, ingestion, _ = mock_db

        bad_file = tmp_path / "file.exe"
        bad_file.write_bytes(b"x" * 100)

        with pytest.raises(ValueError, match="Unsupported file type"):
            ingestion.validate_file(str(bad_file), "file.exe", "application/octet-stream")

    def test_accepts_supported_text_extensions(self, tmp_path, mock_db):
        _, ingestion, _ = mock_db

        for ext in ingestion.SUPPORTED_TEXT_EXTENSIONS:
            f = tmp_path / f"test{ext}"
            f.write_bytes(b"content")
            ingestion.validate_file(str(f), f"test{ext}", "text/plain")


class TestIsDuplicate:
    """Tests for duplicate detection."""

    def test_detects_duplicate(self, mock_db):
        db_mock, ingestion, _ = mock_db
        db_mock.collection.get.return_value = {"ids": ["existing_id"]}

        assert ingestion.is_duplicate("report.pdf", "user123") is True

    def test_no_duplicate(self, mock_db):
        db_mock, ingestion, _ = mock_db
        db_mock.collection.get.return_value = {"ids": []}

        assert ingestion.is_duplicate("new_file.pdf", "user123") is False


class TestIngestFile:
    """Tests for the main ingest_file function."""

    def test_successful_ingestion(self, tmp_path, mock_db):
        db_mock, ingestion, _ = mock_db

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        # No duplicate
        db_mock.collection.get.return_value = {"ids": []}

        # Mock load_and_split
        mock_chunk = MagicMock()
        mock_chunk.page_content = "hello world"
        mock_chunk.metadata = {"page_number": 1}

        with patch.object(ingestion, "_load_and_split", return_value=[mock_chunk]):
            count, error = ingestion.ingest_file(
                str(test_file), "file123", "test.txt", "text/plain", "user1"
            )

        assert count == 1
        assert error is None
        db_mock.insert_chunks.assert_called_once()

    def test_skips_duplicate(self, tmp_path, mock_db):
        db_mock, ingestion, _ = mock_db

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        db_mock.collection.get.return_value = {"ids": ["existing"]}

        count, error = ingestion.ingest_file(
            str(test_file), "file123", "test.txt", "text/plain", "user1"
        )

        assert count == 0
        assert "already been ingested" in error
        db_mock.insert_chunks.assert_not_called()

    def test_rejects_oversized_file(self, tmp_path, mock_db):
        _, ingestion, _ = mock_db

        big_file = tmp_path / "huge.pdf"
        big_file.write_bytes(b"x" * (ingestion.MAX_FILE_SIZE_MB * 1024 * 1024 + 1))

        count, error = ingestion.ingest_file(
            str(big_file), "file123", "huge.pdf", "application/pdf", "user1"
        )

        assert count == 0
        assert "exceeding" in error

    def test_handles_load_error(self, tmp_path, mock_db):
        db_mock, ingestion, _ = mock_db

        test_file = tmp_path / "bad.txt"
        test_file.write_text("content")

        db_mock.collection.get.return_value = {"ids": []}

        with patch.object(ingestion, "_load_and_split", side_effect=Exception("parse error")):
            count, error = ingestion.ingest_file(
                str(test_file), "file123", "bad.txt", "text/plain", "user1"
            )

        assert count == 0
        assert "Failed to process" in error


# --- Retrieval Tests ---


class TestGetContext:
    """Tests for context retrieval."""

    def test_returns_formatted_context(self, mock_db):
        db_mock, _, retrieval = mock_db

        db_mock.search.return_value = {
            "documents": [["chunk1 text", "chunk2 text"]],
            "metadatas": [
                [
                    {"file_name": "report.pdf", "page_number": 1},
                    {"file_name": "report.pdf", "page_number": 2},
                ],
            ],
        }

        context, sources = retrieval.get_context("what is AI?", "user1")

        assert context is not None
        assert "[Source: report.pdf | Page: 1]" in context
        assert "[Source: report.pdf | Page: 2]" in context
        assert "chunk1 text" in context
        assert sources == ["report.pdf"]

    def test_returns_none_when_no_results(self, mock_db):
        db_mock, _, retrieval = mock_db

        db_mock.search.return_value = {"documents": [[]], "metadatas": [[]]}

        context, sources = retrieval.get_context("unknown query", "user1")

        assert context is None
        assert sources == []

    def test_handles_search_error_gracefully(self, mock_db):
        db_mock, _, retrieval = mock_db

        db_mock.search.side_effect = Exception("Connection refused")

        context, sources = retrieval.get_context("test query", "user1")

        assert context is None
        assert sources == []

    def test_deduplicates_sources(self, mock_db):
        db_mock, _, retrieval = mock_db

        db_mock.search.return_value = {
            "documents": [["chunk1", "chunk2", "chunk3"]],
            "metadatas": [
                [
                    {"file_name": "a.pdf", "page_number": 1},
                    {"file_name": "a.pdf", "page_number": 2},
                    {"file_name": "b.pdf", "page_number": 1},
                ],
            ],
        }

        context, sources = retrieval.get_context("query", "user1")

        assert sources == ["a.pdf", "b.pdf"]
