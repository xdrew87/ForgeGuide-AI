# ForgeGuide AI — Security Model

## Upload Security

- **Extension validation**: only `.pdf` accepted at the API boundary
- **Size limit**: configurable via `MAX_UPLOAD_SIZE_MB` (default 50 MB)
- **Filename sanitization**: `Path(filename).name` strips traversal components; regex removes non-alphanumeric chars
- **Storage**: UUID-prefixed filenames; stored to a controlled directory (`/app/uploads`, mode 700)
- **No arbitrary execution**: uploaded files are only passed to PyMuPDF / Tesseract — no shell invocation on user-supplied paths

## Image Upload Security

- Extension whitelist: `.jpg`, `.jpeg`, `.png`, `.webp`
- 10 MB size cap
- Temporary file written, processed, deleted in `finally` block
- Temp path not user-controlled

## API Security

- Input validation via Pydantic models on all endpoints
- String length limits on all user-supplied fields
- No SQL string interpolation — parameterized queries only (SQLAlchemy ORM)
- CORS restricted to known origins; tighten `allow_origins` for production

## Credential / Secret Handling

- No secrets in source control
- `.env.example` documents required variables without values
- API keys read from environment at runtime only
- Logs do not write document content, chunk text, or API key values

## Content Safety (Domain-Specific)

ForgeGuide AI applies domain-specific safety rules at the LLM prompt level:

1. Never recommend disabling LOTO (lockout/tagout) procedures
2. Never recommend bypassing interlocks, thermal protection, or safety circuits
3. Flag safety-critical content explicitly with `[SAFETY-CRITICAL]`
4. Distinguish retrieved evidence from model synthesis
5. Hard gate: no answer generated if evidence confidence below threshold

These constraints are enforced in the system prompt and are non-negotiable regardless of user input.

## No-Fabrication Guarantee

The evidence gate in `qa.py` is the primary safety mechanism. It is covered by a regression test (`TestNoEvidenceBehavior`) that asserts:

- When retrieval returns no chunks → `evidence_sufficient=False`, answer contains `<<INSUFFICIENT_EVIDENCE>>`
- When retrieval returns low-confidence chunks → same result
- No numbered step-by-step procedure appears in the decline response

This regression test must remain green. Any change to the evidence gate logic requires the test suite to pass.

## Production Hardening (Not Yet Implemented)

For a production deployment, additionally implement:

- Authentication (JWT or session-based)
- Rate limiting per user/IP
- Audit logging of all document uploads and queries
- Encrypted storage for sensitive manuals
- Signed upload URLs
- Virus/malware scanning on uploads
- mTLS between services
- Secrets management (Vault, AWS Secrets Manager, etc.)
