from pathlib import Path

import typer
from rich import print as rprint

from .api import ApiEnvironment
from .contentextractor import ContentExtractor
from .dbtypes import LemmaId
from .textparser import TextParser
from .vocabmanager import VocabManager

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
            f"[red]'{lemma}' could not be removed, make sure it is in the"
            " database"
        )


@cli.command("rmm")
def rmm(
    lemma_ids: list[int],
):
    """
    Remove all lemmata passed specified by their ID.
    """
    lids = {LemmaId(lid) for lid in lemma_ids}
    vm = VocabManager(api_env)
    if vm.transfer_lemmata_to_irrelevant_vocab(lids):
        rprint("[green]Successfully removed all lemmata.")
    else:
        rprint(
            "[red]Not all lemmata could be removed, make sure they are"
            " actually in the database."
        )


@cli.command("commit")
def commit(lemma: str):
    """
    Change the status of a lemma from 'staged' to 'committed'.
    """
    vm = VocabManager(api_env)
    if vm.commit_lemma(lemma):
        rprint(f"[green]Successfully committed '{lemma}'.")
    else:
        rprint(
            "[red]Commit unsuccessful. Make sure the lemma exists in the"
            " database, and that it indeed has the status 'staged'."
        )


@cli.command("commitm")
def commitm(lemma_ids: list[int]):
    """
    Commits all lemmata specified by their ID.
    """
    lids = {LemmaId(lid) for lid in lemma_ids}
    vm = VocabManager(api_env)
    if vm.commit_lemmata(lids):
        rprint("[green]Successfully updated all lemma statuses.")
    else:
        rprint(
            "[red]Not all lemma statuses could be updated, make sure they are"
            " actually in the database and have 'staged' status."
        )


@cli.command("push")
def push(lemma: str):
    """
    Change the status of a lemma from 'staged' to 'committed'.
    """
    vm = VocabManager(api_env)
    if vm.push_lemma(lemma):
        rprint(f"[green]Successfully pushed '{lemma}'.")
    else:
        rprint(
            "[red]Push unsuccessful. Make sure the lemma exists in the"
            " database, and that it indeed has the status 'committed'."
        )


@cli.command("pushm")
def pushm(lemma_ids: list[int]):
    """
    Push all lemmata specified by their ID.
    """
    lids = {LemmaId(lid) for lid in lemma_ids}
    vm = VocabManager(api_env)
    if vm.push_lemmata(lids):
        rprint("[green]Successfully pushed all lemmata.")
    else:
        rprint(
            "[red]Not all lemma statuses could be pushed, make sure they are"
            " actually in the database and have 'committed' status."
        )


@cli.command("ls")
def list(
    head: int = 25,
):
    """
    List the top {head} staged lemmata.
    """
    vm = VocabManager(api_env)
    vm.print_staged_lemma_rows(page_size=head)


def set_api_env():
    """
    Set the API environment to production or development.
    """
    api_env = typer.prompt(
        "Connect to API environment at DEV or PROD url?",
        type=ApiEnvironment,
        default=ApiEnvironment.DEV,
    )
    rprint(f"[green]Communicating with {api_env.value} API.")


if __name__ == "__main__":
    set_api_env()
    cli()
