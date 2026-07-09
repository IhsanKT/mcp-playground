import os
import uuid
from dataclasses import dataclass, field
from typing import Optional

from google import genai
from google.genai import types


@dataclass
class ContentBlock:
    type: str
    text: Optional[str] = None
    name: Optional[str] = None
    input: Optional[dict] = None
    id: Optional[str] = None


@dataclass
class Message:
    content: list
    role: str = "assistant"
    stop_reason: Optional[str] = None


class GeminiClient:
    def __init__(self, model: str):
        self.model_name = model
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Remembers which tool_use_id maps to which function name,
        # since Gemini needs the name (not just an id) to match a result.
        self._id_to_name: dict[str, str] = {}

    def add_user_message(self, messages: list, message):
        messages.append({
            "role": "user",
            "content": message.content if isinstance(message, Message) else message,
        })

    def add_assistant_message(self, messages: list, message):
        messages.append({
            "role": "assistant",
            "content": message.content if isinstance(message, Message) else message,
        })

    def text_from_message(self, message: Message):
        return "\n".join(
            block.text for block in message.content if block.type == "text"
        )

    def _block_type(self, block):
        return block.get("type") if isinstance(block, dict) else getattr(block, "type", None)

    def _convert_tools(self, tools):
        if not tools:
            return None
        declarations = []
        for t in tools:
            declarations.append(
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t.get("description", ""),
                    parameters=t.get("input_schema", {"type": "object", "properties": {}}),
                )
            )
        return [types.Tool(function_declarations=declarations)]

    def _convert_messages(self, messages):
        gemini_history = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            content = m["content"]
            parts = []

            if isinstance(content, str):
                parts.append(types.Part(text=content))
            elif isinstance(content, list):
                for block in content:
                    btype = self._block_type(block)

                    if btype == "text":
                        text = block.get("text") if isinstance(block, dict) else block.text
                        parts.append(types.Part(text=text))

                    elif btype == "tool_use":
                        name = block.get("name") if isinstance(block, dict) else block.name
                        args = block.get("input") if isinstance(block, dict) else block.input
                        parts.append(types.Part(
                            function_call=types.FunctionCall(name=name, args=args)
                        ))

                    elif btype == "tool_result":
                        # tool_result blocks only carry tool_use_id, not name —
                        # look up the name we recorded when the call was made.
                        tool_use_id = (
                            block.get("tool_use_id")
                            if isinstance(block, dict)
                            else getattr(block, "tool_use_id", None)
                        )
                        tool_content = (
                            block.get("content")
                            if isinstance(block, dict)
                            else getattr(block, "content", None)
                        )
                        name = self._id_to_name.get(tool_use_id, "unknown_tool")
                        parts.append(types.Part(
                            function_response=types.FunctionResponse(
                                name=name, response={"result": tool_content}
                            )
                        ))
            if parts:
                gemini_history.append(types.Content(role=role, parts=parts))
        return gemini_history

    def chat(
        self,
        messages,
        system=None,
        temperature=1.0,
        stop_sequences=[],
        tools=None,
        thinking=False,
        thinking_budget=1024,
    ) -> Message:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            tools=self._convert_tools(tools),
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=self._convert_messages(messages),
            config=config,
        )

        blocks = []
        has_tool_use = False
        candidate = response.candidates[0]

        for part in candidate.content.parts:
            if part.function_call and part.function_call.name:
                fc = part.function_call
                call_id = f"call_{uuid.uuid4().hex[:8]}"
                self._id_to_name[call_id] = fc.name  # remember for the result later
                blocks.append(ContentBlock(
                    type="tool_use",
                    name=fc.name,
                    input=dict(fc.args) if fc.args else {},
                    id=call_id,
                ))
                has_tool_use = True
            elif part.text:
                blocks.append(ContentBlock(type="text", text=part.text))

        return Message(
            content=blocks,
            stop_reason="tool_use" if has_tool_use else "end_turn",
        )