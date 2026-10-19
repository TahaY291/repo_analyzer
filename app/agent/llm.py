import json
import logging
from functools import lru_cache

import groq
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel

from app.core.config import settings

log = logging.getLogger(__name__)


def get_llm(max_output_tokens: int | None = None) -> ChatGroq:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
        max_tokens=max_output_tokens or settings.llm_max_output_tokens,
        max_retries=2,
        timeout=60,
    )


@lru_cache
def _json_llm(max_output_tokens: int | None):
    return get_llm(max_output_tokens)


def _extract_json(text: str) -> str:
    """Models sometimes wrap JSON in ```json fences or add a sentence before it."""
    start, end = text.find("{"), text.rfind("}")
    return text[start : end + 1] if start != -1 and end > start else text


async def ainvoke_json(
    messages: list, schema: type[BaseModel], max_output_tokens: int | None = None, retries: int = 2
) -> dict:
    """Plain-text JSON, no tool calls. Returns {"raw": message or None, "parsed": schema instance or None}."""
    instruction = HumanMessage(
        "Reply with ONLY one JSON object that matches this JSON schema. "
        "No markdown, no extra text, and do not call any tool.\n" + json.dumps(schema.model_json_schema())
    )
    convo = [*messages, instruction]
    raw = None
    for attempt in range(retries + 1):
        try:
            raw = await _json_llm(max_output_tokens).ainvoke(convo)
            return {"raw": raw, "parsed": schema.model_validate_json(_extract_json(str(raw.content)))}
        except ValueError as e:   # pydantic's ValidationError is a ValueError
            log.warning("JSON invalid (attempt %s): %s", attempt + 1, str(e)[:200])
            fix = f"Your last reply was not valid: {str(e)[:300]} Reply again with ONLY the JSON object."
        except groq.BadRequestError as e:
            log.warning("Groq rejected the request (attempt %s): %s", attempt + 1, str(e)[:200])
            fix = "Reply again with ONLY the JSON object. Do not call any tool."
        # At temperature 0 the same input gives the same output, so the retry must change the input.
        convo = [*messages, instruction, HumanMessage(fix)]
    return {"raw": raw, "parsed": None}


async def ainvoke_tool_call(llm, messages: list, retries: int = 2):
    """Call a tool-bound LLM. If Groq rejects a call to a tool that does not exist, retry with a reminder."""
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        msgs = messages if attempt == 0 else [
            *messages,
            HumanMessage(
                "Reminder: the only tools are list_directory, read_repository_file and search_in_file. "
                "Call exactly one of them with the exact argument names."
            ),
        ]
        try:
            return await llm.ainvoke(msgs)
        except groq.BadRequestError as e:
            last_error = e
            log.warning("Tool call rejected (attempt %s): %s", attempt + 1, str(e)[:200])
    raise RuntimeError(f"The model kept making invalid tool calls: {str(last_error)[:200]}")