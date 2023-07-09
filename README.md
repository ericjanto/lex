Lex is a vocabulary management system for personal use.

## Concept

```txt
Parse file             --> fileparser
Extract relevant words --> tokeniser
Update knowledge base  --> sync
```

## Local setup

```
make setup
```

## commitizen
- `cz commit` to commit staged files

## Supporting a new language
- Tokeniser: check if language supported, otherwise use English as default
- Tagger: only Russian and English supported, so would need to train own tagger
- Tag set: do research on which tag set to use, how to map it to universal tag set. pos_sent_tag uses a PerceptronTagger() under the hood
- Lemmatisation
