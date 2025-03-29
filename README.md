# Lex
Recently I made an observation on [attentional bias](https://en.wikipedia.org/wiki/Attentional_bias) when encountering new words: after being presented with a new word for the first time, I see it everywhere from that point on, including in the books that I read. Usually I unconsciously memorise the sentence it appears in, which helps me tremendously remembering its meaning in the long-term.

Lex is an NLP tool which was developed around this observation. Its goal is to facilitate exhaustive vocabulary acquisition. Given a new book that I’m about to read, Lex selects all words that I do not know yet by referring to a reference vocabulary. It then contextualises them, i.e. for every new word it finds the surrounding context. This allows me to learn new words before reading a book.

## Usage
- `backend/requirements.txt` specifies dependencies for vercel lambdas
- from root: `poetry shell && make`
- spawn new shell, then: `cd backend && python cli.py [command]`

## Local setup
Prerequisites:
- python3.11
- poetry
- pnpm
- conda

Run:
- `cd backend && poetry install`
- `cd ../frontend && pnpm i`
- cd .. && make bsetup
- conda activate lex-backend
- cd backend
- mypy .
- mypy --install-types
- pre-commit install --hook-type pre-commit
- make bsetupvalidate

## commitizen
- `cz c` to commit staged files

## DB
- make dbdev
- source backend/db/schema.sql

## CLI
- Autocomplete

## To write up
- Add lex to Python path for internal module use
- deployment
  - backend: deta space
    - hacky workaround: comment out spacy transformer lib
