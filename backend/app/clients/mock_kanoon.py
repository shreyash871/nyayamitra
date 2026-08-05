"""Fake Indian Kanoon client that returns sample data.
Lets us build and test the whole pipeline before the real
API key arrives. Same method names as the real client."""


class MockKanoonClient:
    def search(self, query: str, page: int = 0) -> dict:
        return {
            "docs": [
                {
                    "tid": "1001",
                    "title": "State of Maharashtra vs Sample Accused",
                    "docsource": "Supreme Court of India",
                },
                {
                    "tid": "1002",
                    "title": "Sample Petitioner vs Union of India",
                    "docsource": "Delhi High Court",
                },
            ],
            "found": 2,
        }

    def get_document(self, doc_id: str) -> dict:
        return {
            "tid": doc_id,
            "title": f"Sample Judgment {doc_id}",
            "doc": (
                "This is sample judgment text for testing the ingestion "
                "pipeline. The accused was charged under IPC Section 420 "
                "for cheating. The court examined the evidence and the "
                "witness testimony before delivering its verdict."
            ),
            "docsource": "Supreme Court of India",
            "publishdate": "2023-05-15",
        }
