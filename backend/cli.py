from pathlib import Path

import typer
from rich import print as rprint

from backend.api import ApiEnvironment
from backend.contentextractor import ContentExtractor
from backend.dbtypes import LemmaId
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
    if vm.transfer_lemmata_to_irrelevant_vocab([lemma]):
        rprint(f"[green]Successfully removed '{lemma}'.")
    else:
        rprint(
            f"[red]'{lemma}' could not been removed, make sure it is in the"
            " database"
        )


@cli.command("rmm")
def rmm(
    lemma_ids: list[int],
):
    """
    Remove all lemmata passed specified by their ID.
    """
    vm = VocabManager(api_env)
    if vm.transfer_lemmata_to_irrelevant_vocab(
        [LemmaId(lid) for lid in lemma_ids]
    ):
        rprint("[green]Successfully removed all lemmata.")
    else:
        rprint(
            "[red]Not all lemmata could be removed, make sure they are"
            " actually in the database."
        )


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


@cli.command("commitm")
def commitm(lemma_ids: list[int]):
    """
    Change the status of all lemma referenced by the passed IDs from 'pending'
    to 'accepted'.
    """
    vm = VocabManager(api_env)
    if vm.accept_lemmata([LemmaId(lid) for lid in lemma_ids]):
        rprint("[green]Successfully updated all lemma status.")
    else:
        rprint(
            "[red]Not all lemma status could be updated, make sure they are"
            " actually in the database."
        )


@cli.command("ls")
def list(
    head: int = 25,
):
    """
    List the top {head} pending lemmata.
    """
    vm = VocabManager(api_env)
    vm.print_pending_lemma_rows(page_size=head)


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
