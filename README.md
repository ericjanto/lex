Lex is a vocabulary management system for personal use.

## Local setup

```
make setup
```

- conda activate lex-backend
- cd backend
- mypy .
- mypy --install-types
- pre-commit install
- make bsetupvalidate
- env file

## commitizen
- `cz c` to commit staged files


## CLI
- Autocomplete

## To write up
- Add lex to Python path for internal module use
- deployment
  - backend: deta space
    - hacky workaround: comment out spacy transformer lib
