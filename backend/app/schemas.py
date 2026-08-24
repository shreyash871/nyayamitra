"""Request and response models for the NyayaMitra API."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    k: int = Field(5, ge=1, le=50)
    hybrid: bool = Field(True, description="Apply BNS-IPC section boosting")


class SearchHit(BaseModel):
    chunk_id: int
    judgment_id: int
    chunk_idx: int
    year: int | None
    case_no: str | None
    outcome: str | None
    sections: list[str] = []
    similarity: float
    section_match: bool = False
    snippet: str


class SearchResponse(BaseModel):
    query: str
    reformulated_tags: list[str] = Field(
        default=[], description="Section tags the BNS-IPC bridge derived from the query"
    )
    count: int
    results: list[SearchHit]


class JudgmentDetail(BaseModel):
    id: int
    court: str
    case_no: str | None
    year: int | None
    outcome: str | None
    sections: list[str] = []
    sections_expanded: list[str] = []
    char_length: int
    chunk_count: int


class BridgeResponse(BaseModel):
    input_tag: str
    expanded: list[str]
    offence: str | None = None
    change_type: str | None = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=1000)
    k: int = Field(3, ge=1, le=5)


class AskSource(BaseModel):
    judgment_id: int
    year: int | None
    case_no: str | None
    similarity: float


class AskResponse(BaseModel):
    question: str
    answer: str | None
    grounded: bool
    reason: str | None
    sources: list[AskSource]
