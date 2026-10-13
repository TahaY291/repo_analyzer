import operator
from typing import Annotated , Literal , TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.messages import add_messages

class Finding(TypedDict):
    file: str
    summary: str
    relevance: Literal["high", "medium", "low"]

class InvestigationState(TypedDict):
    investigation_id: str
    repo_url : str
    owner: str
    repo: str
    focus: str | None

    # what we know about the repo 

    metadata: dict
    file_tree: list[str]

    # memory
    messages: Annotated[list[AnyMessage] , add_messages]
    files_read: Annotated[list[str], operator.add]
    findings: Annotated[list[Finding], operator.add]

    # control
    step: int
    stop_reason : str | None

    # output
    report : dict | None