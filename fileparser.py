"""
File Parser
===========

Parses a file into .txt-format.
Supports epub only for now.
"""
import ebooklib
import json

from bs4 import BeautifulSoup
from ebooklib import epub


class FileParser:
    """
    TODO
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def parse_epub(self) -> None:
        """
        TODO
        """
        self.book = epub.read_epub(self.path, {"ignore_ncx": True})

        # Meta data
        # Title, author, language
        # print()
        with open(self.path + ".meta.json", "w") as f:
            m = {}
            author_meta = self.book.get_metadata("DC", "creator")
            if author_meta:
                m["author"] = author_meta[0][1][
                    "{http://www.idpf.org/2007/opf}file-as"
                ]
            else:
                m['author'] = input('Please provide author manually: ')

            m['title'] = self.book.get_metadata("DC", "title")[0][0]
            m['language'] = self.book.get_metadata("DC", "language")[0][0]
            json.dump(m, f)

        # Contents
        items = self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        items = filter(lambda i: i.get_name().find(".html") >= 0, items)

        with open(self.path + ".content.txt", "w") as f:
            for item in items:
                soup = BeautifulSoup(item.get_body_content(), "html.parser")
                for p in soup.find_all("p"):
                    f.write(p.get_text().replace("\n", " "))


if __name__ == "__main__":
    fp = FileParser("assets/dev-samples/harry-potter.epub")
    fp.parse_epub()
