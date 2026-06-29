"""Main entrypoint for the agent slice: query -> ReAct loop -> answer."""

import asyncio

import typer

from rag.agent.react import run_react_loop
from rag.agent.types import AgentResult
from rag.config import Settings, settings
from rag.shared.logging import configure_logging, logger


async def run_agent(query: str, config: Settings) -> AgentResult:
    configure_logging()
    try:
        result = await run_react_loop(query, config)
    except Exception:
        logger.exception("agent run failed", query=query)
        raise
    logger.info(
        "agent run completed",
        query=query,
        iterations=result.iterations,
        citations=result.citations,
    )
    return result


def main(query: str) -> None:
    result = asyncio.run(run_agent(query, settings))
    typer.echo(result.answer)
    typer.echo(f"Citations: {', '.join(result.citations)}")


if __name__ == "__main__":
    typer.run(main)
