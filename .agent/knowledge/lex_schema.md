# Supabase Schema Preference

## Context
In the `lex` project, the production data is stored in a custom schema named **`lex`**, not the default **`public`** schema. 

## Key Information
- **Schema Name**: `lex`
- **Tables**: `lemma`, `source`, `context`, `lemma_status`, `source_kind`, `lemma_context`, `lemma_source`.
- **Reason**: The `public` schema contains only a few testing rows. The actual production dataset is in the `lex` schema.

## Guidelines for AI Agents
When generating SQL queries or initializing a Supabase client for this project:
1.  **Always specify the schema**. Do not rely on the default `public` schema.
2.  **Supabase Client Initialization**: 
    When using `supabase-js`, initialize with the `lex` schema:
    ```typescript
    const supabaseClient = createClient(URL, KEY, {
      db: { schema: 'lex' }
    });
    ```
3.  **SQL Queries**:
    Always prefix table names with `lex.`, e.g., `SELECT * FROM lex.lemma;`.

## Troubleshooting
If a deployment or local query returns almost no data (only 1-2 rows per table), it is likely querying the `public` schema instead of `lex`. Verify the schema configuration in the client or query.
