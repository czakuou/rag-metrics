"""Main entrypoint for the evals slice: golden dataset to RAGAS to CI gate."""

from pathlib import Path

from rag.agent.tools import RetrieveToolFn

# TODO: implement


def run(dataset_path: Path, retrieve: RetrieveToolFn) -> bool:
    raise NotImplementedError


if __name__ == "__main__":
    pass
