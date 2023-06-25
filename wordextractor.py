"""
Word Extractor
==============
Extracts vocabulary from a text by performing these steps:

1) Tokenise
2) Remove stopwords
3) PoS-tag with tagset according to language
4) Remove tokens with irrelevant PoS (e.g. names)
5) Lemmatise
6) Return list of (lemma,PoS-tag,token)
"""

from typing import List, Tuple
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag_sents
from nltk.tokenize import word_tokenize

from utils import iso_639_1_to_full, iso_639_1_to_639_2


class WordExtractor:
    """
    Vocabulary extractor

    Args:
        path_to_txt: path to text to extract words from
        language: language of the text, specified in ISO 639-1
    """

    def __init__(self, path_to_txt: str, language: str) -> None:
        self.language_full = iso_639_1_to_full(language)
        self.language_639_1 = language
        self.language_639_2 = iso_639_1_to_639_2(language)

        with open(path_to_txt, "r") as f:
            self.text = f.readlines()

    def extract_vocabulary(self) -> List[Tuple[str, str]]:
        """
        TODO: docs
        returns [(lemma,tag,original)] (use NamedTuple for this TODO)
        """
        tokenised_sentences = self._tokenise()
        tagged_tokens = self._tag(tokenised_sentences)
        pass

    def _tokenise(self) -> List[List[str]]:
        """
        Tokenises text whilst preserving sentence context.

        Returns:
            list of lists, each representing a tokenised
            sentence
        """
        tokenised_sentences = []
        for line in self.text:
            if tokens := word_tokenize(line, language=self.language_full):
                tokenised_sentences.append(tokens)

        return tokenised_sentences

    def _tag(self, tokenised_sentences: List[List[str]]) -> List[Tuple[str, str]]:
        """
        Tags the given tokenised sentences using a language-dependent
        tagger and tagset.

        Args:
            tokenised_sentences: sentences containing the tokens to be tagged
        
        Returns:
            list of (token, tag) tuples
        """
        self.tag_lang = self.language_639_2
        tagset = self._determine_tagset(self)

        return pos_tag_sents(tokenised_sentences)

    def _determine_tagset(self) -> None:
        tagset = None
        match self.language_639_2:
            case 'eng':

    def _filter_irrelevant_words(self):
        pass

    def _lemmatise(self):
        # Is this also language dependent?
        pass


    def _map_tags(self):
        # Use nltk's map_tag()
        pass