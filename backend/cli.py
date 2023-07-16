from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint

from backend.api import ApiEnvironment
from backend.contentextractor import ContentExtractor
from backend.textparser import TextParser
from backend.vocabmanager import VocabManager

cli = typer.Typer()
global api_env
api_env = ApiEnvironment.DEV


@cli.command("add")
def add(
    path: Path,
    bv: bool = False,
):
    """
    Parse a new file into the database or base vocabulary (--bv).
    """
    if not path.is_file():
        raise typer.BadParameter("path")

    extractor = ContentExtractor(str(path))
    content_path, meta_path = extractor.extract(meta=not bv)

    parser = TextParser(api_env)

    if bv:
        parser.parse_into_base_vocab(content_path)
    else:
        parser.parse_into_db(content_path, meta_path)

    extractor.clean()


@cli.command("rm")
def rm(
    lemma: str,
):
    """
    Remove a lemma and all associated data from the database.
    """
    vm = VocabManager(api_env)
    if vm.transfer_lemma_to_irrelevant_vocab(lemma):
        rprint(f"[green]Successfully removed '{lemma}'.")
    else:
        rprint(
            f"[red]'{lemma}' could not been removed, make sure it is in the"
            " database"
        )


@cli.command("ls")
def list(
    head: Optional[int] = None,  # noqa: UP007
):
    """
    List the top {head} pending lemmata. Retrieves all by default.
    """
    vm = VocabManager(api_env)
    vm.list_pending_lemma_rows(head)


@cli.command("commit")
def commit(lemma: str):
    """
    Change the status of a lemma from 'pending' to 'accepted'.
    """
    vm = VocabManager(api_env)
    if vm.accept_lemma(lemma):
        rprint(f"[green]Successfully accepted '{lemma}'.")
    else:
        rprint(
            "[red]Unsuccessful. Make sure the lemma exists in the database."
        )


def set_api_env():
    """
    Set the API environment to production or development.
    """
    api_env = typer.prompt(
        "Which API environment would you like to connect to?",
        type=ApiEnvironment,
        default=ApiEnvironment.DEV,
    )
    rprint(f"[green]Communicating with {api_env.value} API.")


if __name__ == "__main__":
    set_api_env()
    cli()
