from pathlib import Path

from backend.services.ast_chunker import chunk_python_file
from backend.services.chunker import chunk_file
from backend.services.indexer import collection_name
from backend.services.repo_reader import normalize_repo_url


def test_line_chunking_preserves_overlap(tmp_path: Path) -> None:
    source = tmp_path / "example.txt"
    source.write_text("\n".join(f"line {number}" for number in range(1, 11)))
    chunks = chunk_file(str(source), chunk_size=5, overlap=2)
    assert [(chunk["start_line"], chunk["end_line"]) for chunk in chunks] == [(1, 5), (4, 8), (7, 10), (10, 10)]


def test_ast_chunker_only_returns_top_level_definitions(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text("def outer():\n    def inner():\n        return 1\n    return inner()\n\nclass Example:\n    def method(self):\n        return 2\n")
    chunks = chunk_python_file(str(source))
    assert [chunk["name"] for chunk in chunks] == ["outer", "Example"]


def test_collection_name_is_stable_and_distinct() -> None:
    assert collection_name("https://github.com/org/repo") == collection_name("https://github.com/org/repo")
    assert collection_name("https://github.com/org/repo") != collection_name("https://github.com/org/other")


def test_browser_style_repository_url_is_normalized() -> None:
    assert normalize_repo_url("github.com/org/repo") == "https://github.com/org/repo"
