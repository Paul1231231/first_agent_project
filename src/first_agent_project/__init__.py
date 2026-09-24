"""first_agent_project package."""

from __future__ import annotations

import asyncio

__all__ = ["main"]


def main() -> None:
    """Run the interactive database agent."""

    from .agent import run_agent

    asyncio.run(run_agent())
