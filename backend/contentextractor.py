"""File Parser
==============

Parses file contents into .txt-format.
Supports epub only for now.
"""


import contextlib
import json
import os
import re
import shutil

import ebooklib
import typer
from bs4 import BeautifulSoup
from ebooklib import epub
from ebooklib.epub import EpubBook

from backend.dbtypes import SourceKindVal, SourceMetadata


class ContentExtractor:
    """ """

    def __init__(self, path: str) -> None:
        # TODO [ej] refactor to receive Path object which makes
        # usage of os.path functionality obsolete
        self.path = path
        self.file_name, self.file_extension = os.path.splitext(path)
        self.content_path = f"{self.file_name}.content.txt"
        self.meta_path = f"{self.file_name}.meta.json"

    def extract(self, meta: bool = True) -> tuple[str, str]:
        """
        Determines the respective parsing method for the given
        file type, and executes it.

        Args:
            meta: flag to enable metadata extraction
        """
        match (self.file_extension):
            case ".epub":
                self.extract_epub(meta)
            case ".txt":
                self.extract_txt(meta)
            case _:
                raise NotImplementedError(
                    f"""
                    Parsing for files of type {self.file_extension}
                    is not implemented yet. If this is not
                    the expected file type, make sure the 
                    file name is correct.
                    """
                )
        return self.content_path, self.meta_path

    def extract_epub(self, meta: bool = True) -> None:
        """Parses an epub file into .txt format, and
        saves the corresponding metadata in a JSON file.
        """
        book = epub.read_epub(self.path, {"ignore_ncx": True})

        if meta:
            self.save_metadata_epub(book)

        items = book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        items = filter(lambda i: i.get_name().find(".html") >= 0, items)

        with open(self.content_path, "w") as f:
            for item in items:
                soup = BeautifulSoup(item.get_body_content(), "html.parser")
                for p in soup.find_all("p"):
                    f.write(p.get_text())

    def save_metadata_epub(self, book: EpubBook):
        """Reads and saves metadata from an epub book."""
        with open(self.meta_path, "w") as f:
            source_kind = SourceKindVal.BOOK

            author = None
            if author_meta := book.get_metadata("DC", "creator"):
                with contextlib.suppress(KeyError):
                    author = author_meta[0][1][
                        "\{http://www.idpf.org/2007/opf}file-as"
                    ]
            if not author:
                author = typer.prompt(
                    "Please provide author manually (firstname .. lastname)",
                    type=str,
                )

            title = book.get_metadata("DC", "title")[0][0]
            language = book.get_metadata("DC", "language")[0][0]
            while not re.match(r"\w{2}", language):
                language = typer.prompt(
                    """
                    Language specifier does not conform to
                    ISO 639-1 (e.g. 'en'). Please enter
                    manually: 
                    """,
                    type=str,
                )
                # TODO [ej] possible to create regex-matching type?

            m = SourceMetadata(
                author=author,
                title=title,
                language=language,
                source_kind=source_kind,
            )
            json.dump(m.to_dict(), f)

    def extract_txt(self, meta: bool = True):
        shutil.copyfile(self.path, self.content_path)
        if meta:
            self.inquire_metadata()

    def inquire_metadata(self) -> None:
        # TODO [ej] validate input formats
        author = typer.prompt("Author (Firstname .. Lastname)", type=str)
        title = typer.prompt("Title", type=str)
        language = typer.prompt("Language (ISO 639-1, 'en')", type=str)
        source_kind = typer.prompt(
            f"Source kind {[k.value for k in SourceKindVal]}",
            type=SourceKindVal,
        )

        m = SourceMetadata(
            author=author,
            title=title,
            language=language,
            source_kind=source_kind,
        )
        with open(self.meta_path, "w") as f:
            json.dump(m.to_dict(), f)

    def clean(self, delete_original: bool = False) -> None:
        """Removes any files this parser might have created."""
        if delete_original and os.path.exists(self.path):
            os.remove(self.path)
        if os.path.exists(self.content_path):
            os.remove(self.content_path)
        if os.path.exists(self.meta_path):
            os.remove(self.meta_path)


if __name__ == "__main__":
    fp = ContentExtractor("assets/dev-samples/harry-potter.epub")
    fp.inquire_metadata()
    # fp.extract()
    # fp.clean()
