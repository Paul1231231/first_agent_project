from dataclasses import dataclass
from typing import Any


@dataclass
class FakeContent:
    text: str


@dataclass
class FakeMCPResult:
    content: list[FakeContent]


class FakeMCPSession:
    def __init__(
        self,
        response_text: str = '{"rows": []}',
        error: Exception | None = None,
    ):
        self.response_text = response_text
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def call_tool(self, name: str, arguments: dict[str, Any]):
        self.calls.append(
            {
                "name": name,
                "arguments": arguments,
            }
        )

        if self.error:
            raise self.error

        return FakeMCPResult(
            content=[FakeContent(text=self.response_text)]
        )