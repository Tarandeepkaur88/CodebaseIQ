from backend.services.bug_agent import _sources


def test_sources_reads_nested_metadata_and_removes_duplicates() -> None:
    matches = [
        {"metadata": {"file": "app.py", "start_line": 2, "end_line": 7}},
        {"metadata": {"file": "app.py", "start_line": 2, "end_line": 7}},
        {"metadata": {"file": "db.py", "start_line": 10, "end_line": 14}},
    ]

    assert _sources(matches) == [
        {"file": "app.py", "start_line": 2, "end_line": 7},
        {"file": "db.py", "start_line": 10, "end_line": 14},
    ]
