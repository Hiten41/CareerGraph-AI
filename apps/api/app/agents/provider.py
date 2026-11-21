from typing import Literal
import httpx
from pydantic import BaseModel, Field
from app.core.config import settings


class Function(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: Literal["function"]
    function: Function


class Reply(BaseModel):
    role: Literal["assistant"]
    content: str | None = None
    refusal: str | None = None
    tool_calls: list[ToolCall] | None = Field(default=None, max_length=32)


def completion(client: httpx.Client, messages: list, tools: list) -> Reply:
    response = client.post(
        settings.llm_base_url.rstrip("/") + "/chat/completions",
        headers={"Authorization": "Bearer " + settings.llm_api_key},
        json={"model": settings.llm_model, "messages": messages, "tools": tools, "temperature": 0},
    )
    response.raise_for_status()
    return Reply.model_validate(response.json()["choices"][0]["message"])
