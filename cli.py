from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint

from api import ApiEnvironment
from textparser import TextParser
from vocabmanager import VocabManager

cli = typer.Typer()


class Action(str, Enum):
    PARSE_INTO_DB = "dbparse"
    PARSE_INTO_BASE_VOCABULARY = "bvparse"
    TRANSFER_LEMMA = "lemtrans"


@cli.command()
def main(
    action: Annotated[Action, typer.Option(prompt=True)],
    api_env: ApiEnvironment = ApiEnvironment.DEV.value,  # type: ignore
):
    if action == Action.TRANSFER_LEMMA:
        vm = VocabManager(api_env)
        while True:
            vm.transfer_lemma_to_irrelevant_vocab(inquire_lemma())
            if not typer.prompt(
                text="Transfer more lemmata? [y/n]", type=bool
            ):
                break
    else:
        path = inquire_path()
        tp = TextParser(api_env)
        match action:
            case Action.PARSE_INTO_DB:
                meta_path = inquire_path(metadata=True)
                tp.parse(path, meta_path)
            case Action.PARSE_INTO_BASE_VOCABULARY:
                tp.parse_into_base_vocab(path)
        rprint("[green]Success!")


def inquire_path(metadata: bool = False) -> Path:
    path = Path(
        typer.prompt(
            text=(
                f"Path to {'metadata' if metadata else 'content'}-file to"
                " parse"
            )
        )
    )
    if not path.is_file():
        raise typer.BadParameter("Path could not be resolved")
    return path


def inquire_lemma() -> str:
    return typer.prompt(text="Provide lemma to be transferred", type=str)


if __name__ == "__main__":
    cli()
