- `backend/requirements.txt` specifies dependencies for vercel lambdas
- poetry shell
- poetry run python cli.py (from deactivated shell, installation seems faulty)
- cd backend, poetry shell, cd .., make apiuvi / make

## Local setup
- `cd backend && poetry install`
- `cd frontend && pnpm i`

```
make setup
```

- conda activate lex-backend
- cd backend
- mypy .
- mypy --install-types
- pre-commit install --hook-type pre-commit
- make bsetupvalidate
- env file

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
