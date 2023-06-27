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

from typing import List, NamedTuple, Tuple
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag_sents, pos_tag, map_tag
from nltk.tokenize import word_tokenize

from utils import iso_639_1_to_full, iso_639_1_to_639_2

class TokenisedSentence(NamedTuple):
    original_file_line: int
    tokens: List[str]

class TaggedToken(NamedTuple):
    token: str
    tag: str

class TaggedSentence(NamedTuple):
    original_file_line: int
    tokens: List[TaggedToken]

class WordExtractor:
    """
    Vocabulary extractor

    Args:
        path_to_txt: path to text to extract words from
        language: language of the text, specified in ISO 639-1
    """

    def __init__(self, path_to_txt: str, path_to_stopwords: str, language: str) -> None:
        self.language_full = iso_639_1_to_full(language)
        self.language_639_1 = language
        self.language_639_2 = iso_639_1_to_639_2(language)

        with open(path_to_txt, "r") as f:
            self.text = f.readlines()

        with open(path_to_stopwords, "r") as f:
            self.stopwords = f.readlines()

    def extract_vocabulary(self) -> List[Tuple[str, str]]:
        """
        TODO: docs
        returns [(lemma,tag,original)] (use NamedTuple for this TODO)
        """
        tokenised_sentences = self._tokenise()
        tagged_tokens = self._tag(tokenised_sentences)
        pass

    def _tokenise(self) -> List[TaggedSentence]:
        """
        Tokenises text whilst preserving sentence context.
        Also removes stopwords.

        Returns:
            list of TokenisedSentences
        """
        tagged_sentences = []
        for line_num,sentence in enumerate(self.text):
            # Tokenisation
            if tokens := word_tokenize(sentence, language=self.language_full):
                # Stopword removal
                tokens = list(filter(lambda x: x not in self.stopwords, tokens))

                # Tagging
                tagged_tokens = [TaggedToken(token,map_tag(
                    map_tag(source='en-ptb', target='universal', source_tag=tag) if tag != 'NNP' else (token, 'PROPN')
                    )) for token,tag in pos_tag(tokens)]
                
                # Filtering by tag
                relevant_universal = (
                    "VERB",
                    "NOUN",
                    "ADJ",
                    "ADV",
                    "ADP",
                    "CONJ",
                    "DET",
                )
                relevant_tokens = list(filter(lambda x: x.tag in relevant_universal, tagged_tokens))

                # Lemmatisation (TODO)

                tagged_sentences.append(TaggedSentence(line_num, relevant_tokens))

        return tagged_sentences

    def _tag(self, tokenised_sentences: List[TokenisedSentence]) -> List[TaggedSentence]:
        """
        Tags the given tokenised sentences using a language-dependent
        tagger and tagset.

        Args:
            tokenised_sentences: sentences containing the tokens to be tagged
        
        Returns:
            list of TaggedSentences
        """
        lines = [t.original_file_line for t in tokenised_sentences]
        sent_tokens = [t.tokens for t in tokenised_sentences]
        tagged_sentences = [[TaggedToken(token,tag) for (token,tag) in tagged_sent] for tagged_sent in pos_tag_sents(sent_tokens)]
        return [TaggedSentence(l,ts) for l,ts in zip(lines, tagged_sentences)]

    def _lemmatise(self):
        # Is this also language dependent?
        pass


    def _map_tags(self):
        # Use nltk's map_tag()
        pass