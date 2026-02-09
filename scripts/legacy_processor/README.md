# Legacy Processor

This directory contains recovered logic from the old CLI/API for parsing and extracting content from sources (Epub, Text).

## Files

- `contentextractor.py`: Logic for extracting text and metadata from `.epub` and `.txt` files.
- `textparser.py`: Logic for NLP processing (tokenization, lemmatization using Spacy) and parsing content into the database.
- `vocabmanager.py`: Logic for managing vocabulary (transferring to irrelevant, pushing status) and integration with Anki.
- `anki.py`: Client for interacting with AnkiConnect.
- `dbtypes.py`: Data models sharing the structure with the old API.
- `const.py`: Constants used in the scripts.
- `utils.py`: Utility functions.
- `apirequestor.py`: Legacy client for communicating with the old Python API server. **Note:** The API server has been replaced by Supabase, so this file serves mainly as a reference for the data structures and endpoints that were used.

## Usage

To use these scripts, you will need to install the Python dependencies:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_trf
```

You can then import the classes or run them as scripts (if adapted).

## Future integration

To enable source parsing via the frontend:
1.  **Option A (Python Service):** Wrap `TextParser` and `ContentExtractor` in a lightweight Python HTTP service (e.g., FastAPI) and deploy it (e.g., Google Cloud Run, AWS Lambda). The frontend can send files to this service, which processes them and writes to Supabase directly (or returns the data).
2.  **Option B (Port to JS):** Port `ContentExtractor` (epub parsing) to TypeScript (using libraries like `epub2`). For NLP (`TextParser`), use a JS-based NLP library (like `compromise` or `natural`), though Spacy's capabilities might be hard to match fully in JS.
3.  **Option C (Supabase Edge Functions + Python):** Investigate if Supabase Edge Functions can support the required Python environment (Spacy + models might be too heavy).
