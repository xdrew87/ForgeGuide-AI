# AI Usage Disclosure

## ForgeGuide AI — ABB Accelerator 2026

This document discloses where AI coding assistance was used in developing ForgeGuide AI, as required for hackathon transparency.

## AI Assistance Used

AI coding assistance (Claude by Anthropic) was used during development of this project for:

- Initial scaffold and directory structure generation
- FastAPI router and Pydantic model boilerplate
- SQLAlchemy model definitions
- Qdrant client integration code
- RRF fusion algorithm implementation
- Test suite generation
- Documentation drafts (README, ARCHITECTURE.md, SECURITY.md, DEMO.md)
- Tailwind/Next.js component structure

## Review and Acceptance

All AI-generated code was reviewed and accepted by the project owner prior to inclusion. The project owner:

- Read and understood every file before committing it
- Ran all 23 tests and verified they pass
- Reviewed the evidence gate logic (the core safety mechanism) independently
- Made deliberate architectural decisions (provider-agnostic LLM interface, RRF hybrid retrieval, evidence confidence threshold)

No code was included without review.

## AI Is Also the Product

ForgeGuide AI uses LLM inference (Anthropic Claude or OpenAI GPT-4) at runtime as the grounded answer generation component. The LLM is explicitly constrained by a system prompt that prohibits fabrication and safety control bypass. This is a deliberate design choice, not a dependency risk.

## Synthetic Demo Data

The MX-400 Maintenance Manual demo PDF was generated using `scripts/generate_demo_manual.py` with the reportlab library. All content in that document is fictional, created specifically for this demonstration, and clearly marked as synthetic.
