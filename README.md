# Lex
Lex is an NLP tool developed around the observation of attentional bias in vocabulary acquisition. It facilitates exhaustive vocabulary acquisition by selecting unknown words from books, contextualizing them, and helping the user learn them before reading.

## Current Architecture
- **Frontend**: Next.js application (in `frontend/`)
- **API**: Supabase Edge Functions (in `supabase/functions/lex-api/`)
- **Database**: Supabase (Postgres)

## Local Setup
### Frontend
1. `cd frontend`
2. `pnpm install`
3. `pnpm dev`

### Supabase Edge Functions
Refer to the [Supabase Edge Functions documentation](https://supabase.com/docs/guides/functions) for local development and deployment.

## Maintenance
- `make fdev`: Run frontend development server
- `make psql`: Connect to the Supabase database
- `make pre`: Run pre-commit hooks manually
