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

from typing import List, NamedTuple
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag, map_tag
from nltk.tokenize import word_tokenize

class TokenisedSentence(NamedTuple):
    original_file_line: int
    tokens: List[str]

class TaggedToken(NamedTuple):
    token: str
    tag: str

class TaggedLemma(NamedTuple):
    lemma: str
    tag: str

class LemmatisedSentence(NamedTuple):
    original_file_line: int
    lemmata: List[TaggedLemma]

class LemmaExtractor:
    """
    Lemma extractor

    TODO: testing
    TODO: what's the output you *need*? Are original line numbers still necessary?
    TODO: currently uses PerceptronTagger, explained here: https://explosion.ai/blog/part-of-speech-pos-tagger-in-python
            - Indicates that as a feature, it looks at i-2 and i+2 tags. This means that rather than
              tagging each sentence individually, it'll be beneficial to parse sentences in context to
              each other to increase tagging performance near sentence boundaries.
            - Hence, use pos_tag_sents
    TODO: automated formatting with black
    TODO: documentation
    TODO: text passed into lemmata

    Args:
        path_to_txt: path to text to extract words from
        language: language of the text, specified in ISO 639-1
    """

    def __init__(self, path_to_txt: str, path_to_stopwords: str) -> None:
        self.lemmatise = WordNetLemmatizer().lemmatize

        with open(path_to_txt, "r") as f:
            self.text = f.readlines()

        with open(path_to_stopwords, "r") as f:
            self.stopwords = f.readlines()

    def extract_lemmata(self) -> List[LemmatisedSentence]:
        """
        Tokenises text whilst preserving sentence context.
        Also removes stopwords.
        TODO: docs

        Returns:
            list of TokenisedSentences
        """
        lemmatised_sentences = []
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

                # Lemmatisation
                tagmap_universal_lemmatiser = {
                    "VERB": "v",
                    "NOUN": "n",
                    "ADJ": "a",
                    "ADV": "r",
                }

                tagged_lemmata = []
                pos_default = 'n'
                for rt in relevant_tokens:
                    lemmatag = None
                    if rt.tag in tagmap_universal_lemmatiser:
                        lemmatag = tagmap_universal_lemmatiser[rt.tag]
                    lemma = self.lemmatise(rt.token, pos=lemmatag or pos_default)
                    tagged_lemmata.add(TaggedLemma(lemma, lemmatag or pos_default))

                lemmatised_sentences.append(LemmatisedSentence(line_num, tagged_lemmata))
        return lemmatised_sentences