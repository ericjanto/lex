"""
Word Extractor
==============
Extracts vocabulary from a text by performing these steps:

1) Tokenise
2) PoS-tag with tagset according to language
3) Remove tokens with irrelevant PoS (e.g. names)
4) Lemmatise
5) Map to universal tag (but also keep original)
"""

from typing import List, Tuple
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag_sents
from nltk.tokenize import word_tokenize

from utils import map_iso_lang_to_punkt

class WordExtractor():
    """
    Vocabluary extractor

    Args:
        path_to_txt: path to text to extract words from
        language: language of the text
    """
    def __init__(self, path_to_txt: str, language: str) -> None:
        self.lang = map_iso_lang_to_punkt(language)

        with open(path_to_txt, 'r') as f:
            self.text = f.readlines()

    
    def extract_vocabulary(self) -> List[Tuple[str, str]]:
        # returns [(word,tag)]
        pass


    def __tokenise(self):
        # TODO: tokeniser should take language into account
        pass

    def __tag(self):
        # TODO: add map for tags in utility class
        pass

    def __filter_irrelevant_words(self):
        pass

    def __lemmatise(self):
        # Is this also language dependent?
        pass

