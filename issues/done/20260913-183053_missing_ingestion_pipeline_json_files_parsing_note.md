# Issue: Missing Documentation for RAG Ingestion Pipeline Utils JSON Files Parsing Note

## Summary
`docs/03_rag_02_01_ingestion_pipeline-overview.md` mentions JSON parsing with orjson but provides a verification command that's difficult to use in practice.

## Evidence
- File: `docs/03_rag_02_01_ingestion_pipeline-overview.md`, File Lifecycle section
- Text: "> JSON files are parsed using `orjson.loads()`. For verification: `python -c \"import orjson; print(orjson.loads(open('FILE', 'rb').read()))\"`"
- The verification command requires manual file path substitution and binary mode reading
- No explanation of why orjson is used instead of standard json module

## Impact
- Operators attempting to verify JSON artifacts will struggle with the command
- The binary mode requirement (`'rb'`) is non-obvious and may cause confusion
- No guidance on what to look for when verifying the output

## Recommended Action
Improve the verification command documentation:
1. Provide a working example with placeholder file path
2. Explain why binary mode (`'rb'`) is required
3. Add expected output format description
4. Consider adding a helper script for artifact verification
