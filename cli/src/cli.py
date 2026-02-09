import cProfile
from pathlib import Path

import typer
from rich import print as rprint

from .contentextractor import ContentExtractor
from .dbtypes import LemmaId
from .textparser import TextParser
from .utils import absolutify_path_from_root
from .vocabmanager import VocabManager

cli = typer.Typer()


@cli.command("add")
def add(path: Path, bv: bool = False, profile: bool = False):
    # sourcery skip: merge-else-if-into-elif
    """
    Parse a new file into the database or base vocabulary (--bv).
    Produce an `add.profile` file (--profile).
    """
    if not path.is_file():
        raise typer.BadParameter("path")

    extractor = ContentExtractor(str(path))
    content_path, meta_path = extractor.extract(meta=not bv)

    parser = TextParser()

    if bv:
        (
            cProfile.runctx(
                "parser.parse_into_base_vocab(content_path)",
                locals=locals(),
                globals=globals(),
                filename=absolutify_path_from_root(
                    "/uncommitted/dbparse-bv.profile"
                ),
            )
            if profile
            else parser.parse_into_base_vocab(content_path)
        )
    else:
        (
            cProfile.runctx(
                "parser.parse_into_db(content_path, meta_path)",
                locals=locals(),
                globals=globals(),
                filename=absolutify_path_from_root(
                    "/uncommitted/dbparse-7.profile"
                ),
            )
            if profile
            else parser.parse_into_db(content_path, meta_path)
        )

    extractor.clean()


@cli.command("rm")
def rm(
    lemma: str,
):
    """
    Remove a lemma and all associated data from the database.
    """
    vm = VocabManager()
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
    vm = VocabManager()
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
    vm = VocabManager()
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
    vm = VocabManager()
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
    Change the status of a lemma from 'committed' to 'pushed'.
    """
    vm = VocabManager()
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
    vm = VocabManager()
    if vm.push_lemmata(lids):
        rprint("[green]Successfully pushed all lemmata.")
    else:
        rprint(
            "[red]Not all lemma statuses could be pushed, make sure they are"
            " actually in the database and have 'committed' status."
        )


@cli.command("ls")
def list_staged_lemmata(
    head: int = 25,
):
    """
    List the top {head} staged lemmata.
    """
    vm = VocabManager()
    vm.print_staged_lemma_rows(page_size=head)


@cli.command("anki")
def add_to_anki(lemma: str):
    """
    Add a specific lemma to Anki.
    """
    vm = VocabManager()
    if vm.add_to_anki(lemma):
        rprint(f"[green]Successfully added '{lemma}' to Anki.")
    else:
        rprint(f"[red]Failed to add '{lemma}' to Anki.")


@cli.command("ankim")
def add_multiple_to_anki(lemma_ids: list[int]):
    """
    Add multiple lemmata to Anki by their IDs.
    """
    lids = {LemmaId(lid) for lid in lemma_ids}
    vm = VocabManager()
    if vm.add_lemmata_to_anki(lids):
        rprint("[green]Successfully added selected lemmata to Anki.")
    else:
        rprint("[red]Some lemmata could not be added to Anki.")


@cli.command("sync")
def sync_anki():
    """
    Trigger Anki synchronization with AnkiWeb.
    """
    vm = VocabManager()
    result = vm.anki.sync()
    if "error" in result and result["error"]:
        rprint(f"[red]Anki Sync Failed: {result['error']}")
    else:
        rprint("[green]Anki Sync triggered successfully.")


def main():
    cli()
