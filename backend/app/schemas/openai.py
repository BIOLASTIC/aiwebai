from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    max_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None
    account_id: Optional[int] = None


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[Dict[str, int]] = None


class ResponsesRequest(BaseModel):
    model: str
    input: Union[str, List[Dict[str, Any]]]
    stream: bool = False
    account_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResponsesResponse(BaseModel):
    id: str
    object: str = "response"
    model: str
    output_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ImageGenerationRequest(BaseModel):
    model: str = "gemini-image-latest"
    prompt: str
    size: Optional[str] = "1024x1024"
    account_id: Optional[int] = None


class ImageEditRequest(BaseModel):
    model: str = "gemini-image-latest"
    prompt: str
    image: Optional[str] = None
    account_id: Optional[int] = None


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    owned_by: str = "gemini-gateway"
    capabilities: Dict[str, Any] = Field(default_factory=dict)
