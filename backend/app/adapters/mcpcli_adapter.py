import asyncio
import subprocess
import json
import time
import uuid
from typing import AsyncGenerator, List, Optional, Dict, Any
from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.openai import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice, ChatMessage
from backend.app.schemas.native import ImageGenerationRequest


class McpCliAdapter(BaseAdapter):
    def __init__(self, profile: Optional[str] = None):
        self.profile = profile

    async def _run_gemcli(self, args: List[str]) -> str:
        # Use absolute path to gemcli in .venv/bin
        import os
        from pathlib import Path

        # Determine the .venv path relative to the project root
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        gemcli_path = project_root / ".venv" / "bin" / "gemcli"

        if not gemcli_path.exists():
            # Fallback for other environments if needed
            gemcli_path = "gemcli"
        else:
            gemcli_path = str(gemcli_path)

        cmd = [gemcli_path]
        if self.profile:
            cmd.extend(["--profile", self.profile])
        cmd.extend(args)

        # We assume gemcli is in the PATH
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"gemcli failed: {stderr.decode()}")

        return stdout.decode()

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        last_message = request.messages[-1].content
        # gemcli chat "prompt" outputs the response
        output = await self._run_gemcli(["chat", last_message])

        choice = ChatCompletionChoice(
            index=0, message=ChatMessage(role="assistant", content=output.strip()), finish_reason="stop"
        )

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            created=int(time.time()),
            model=request.model,
            choices=[choice],
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

    async def stream_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[Dict[str, Any], None]:
        # gemcli might not support streaming via CLI easily, we'll simulate it for now
        # or use a more advanced way if gemcli supports it
        response = await self.chat_completion(request)
        content = response.choices[0].message.content

        # Simulate streaming by yielding chunks
        chunk_size = 20
        for i in range(0, len(content), chunk_size):
            yield {
                "id": response.id,
                "object": "chat.completion.chunk",
                "created": response.created,
                "model": request.model,
                "choices": [{"index": 0, "delta": {"content": content[i : i + chunk_size]}, "finish_reason": None}],
            }

        yield {
            "id": response.id,
            "object": "chat.completion.chunk",
            "created": response.created,
            "model": request.model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }

    async def generate_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        # gemcli image "prompt"
        output = await self._run_gemcli(["image", request.prompt])

        # Parse the output - gemcli might return a direct URL or a "saved to" message
        output_str = output.strip()

        # If gemcli returns a URL that requires authentication, our system needs to handle it
        # For now, let's handle the common case where it returns a URL
        # Later, we'll want to download and serve the image securely through our API

        # Placeholder for actual image handling - in production, we'd need to
        # download the image and make it available via our secure API endpoint
        # For now, return what gemcli gave us, but note this requires user to have gemcli logged in
        return {"created": int(time.time()), "data": [{"url": output_str}]}

    async def list_models(self) -> List[Dict[str, Any]]:
        """Return models available via gemini-web-mcp-cli (includes video/music/research capable ones)."""
        return [
            # Models confirmed to work through gemini-web-mcp-cli
            {"id": "gemini-2.0-flash", "display_name": "Gemini 2.0 Flash", "family": "gemini-2.0", "source": "mcpcli"},
            {
                "id": "gemini-2.0-flash-exp",
                "display_name": "Gemini 2.0 Flash (Exp)",
                "family": "gemini-2.0",
                "source": "mcpcli",
            },
            {
                "id": "gemini-2.0-pro-exp",
                "display_name": "Gemini 2.0 Pro (Exp)",
                "family": "gemini-2.0",
                "source": "mcpcli",
            },
            {"id": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro", "family": "gemini-1.5", "source": "mcpcli"},
            {"id": "gemini-1.5-flash", "display_name": "Gemini 1.5 Flash", "family": "gemini-1.5", "source": "mcpcli"},
            # Imagen for image / video generation (used by mcp-cli internally)
            {"id": "imagen-3.0", "display_name": "Imagen 3.0 (Image Gen)", "family": "imagen", "source": "mcpcli"},
            {"id": "veo-2.0", "display_name": "Veo 2.0 (Video Gen)", "family": "veo", "source": "mcpcli"},
            {"id": "lyria-1.0", "display_name": "Lyria 1.0 (Music Gen)", "family": "lyria", "source": "mcpcli"},
        ]

    async def health_check(self) -> bool:
        try:
            await self._run_gemcli(["doctor"])
            return True
        except Exception:
            return False

    async def get_limits(self) -> Dict[str, Any]:
        output = await self._run_gemcli(["limits"])
        # Parse output...
        return {"raw": output}

    async def generate_video(self, prompt: str) -> str:
        # gemcli video "prompt"
        output = await self._run_gemcli(["video", prompt])
        return output.strip()

    async def generate_music(self, prompt: str) -> str:
        # gemcli music "prompt"
        output = await self._run_gemcli(["music", prompt])
        return output.strip()

    async def deep_research(self, prompt: str) -> str:
        # gemcli research "prompt"
        output = await self._run_gemcli(["research", prompt])
        return output.strip()
