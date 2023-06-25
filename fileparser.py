"""
File Parser
===========

Parses file contents into .txt-format.
Supports epub only for now.
"""

import ebooklib
import json
import os
import re

from bs4 import BeautifulSoup
from ebooklib import epub


class FileParser:
    """ """

    def __init__(self, path: str) -> None:
        self.path = path
        self.file_name, self.file_extension = os.path.splitext(path)
        self.contentpath = self.file_name + ".content.txt"
        self.metapath = self.file_name + ".meta.json"

    def parse(self) -> None:
        """
        Determines the respective parsing method for the given
        file type, and executes it.

        Args:
            filetype: type of file (e.g. epub, pdf)
        """
        match (self.file_extension):
            case ".epub":
                self.parse_epub()
            case _:
                raise NotImplementedError(
                    f"""
                    Parsing for files of type {self.file_extension}
                    is not implemented yet. If this is not
                    the expected file type, make sure the 
                    file name is correct.
                    """
                )

    def parse_epub(self) -> None:
        """
        Parses an epub file into .txt format, and
        saves the corresponding metadata in a JSON file.
        """
        book = epub.read_epub(self.path, {"ignore_ncx": True})

        self.save_metadata_epub(book)

        items = book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        items = filter(lambda i: i.get_name().find(".html") >= 0, items)

        with open(self.contentpath, "w") as f:
            for item in items:
                soup = BeautifulSoup(item.get_body_content(), "html.parser")
                for p in soup.find_all("p"):
                    f.write(p.get_text())

    def save_metadata_epub(self, book):
        """
        Reads and saves metadata from an epub book.
        """
        with open(self.metapath, "w") as f:
            m = {}
            author_meta = book.get_metadata("DC", "creator")
            if author_meta:
                m["author"] = author_meta[0][1]["\{http://www.idpf.org/2007/opf}file-as"]
            else:
                m["author"] = input("Please provide author manually: ")
            m["title"] = book.get_metadata("DC", "title")[0][0]
            m["language"] = book.get_metadata("DC", "language")[0][0]
            while not re.match(r"\w{2}", m["language"]):
                m["language"] = input(
                    """
                    Language specifier does not conform to
                    ISO 639-1 (e.g. 'en'). Please enter
                    manually: 
                    """
                )
            json.dump(m, f)

    def clean(self) -> None:
        """
        Removes any files this parser might have created.
        """
        if os.path.exists(self.contentpath):
            os.remove(self.contentpath)
        if os.path.exists(self.metapath):
            os.remove(self.metapath)


if __name__ == "__main__":
    fp = FileParser("assets/dev-samples/harry-potter.epub")
    fp.parse()
    # fp.clean()
