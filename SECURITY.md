# Security Policy

## Reporting a vulnerability

If you find a security vulnerability in ForgeGuide AI, please report it
privately rather than opening a public issue:

- Preferred: open a [GitHub Security Advisory](../../security/advisories/new)
  for this repository (Security tab → "Report a vulnerability")
- Alternative: open a regular issue with minimal detail and ask for a private
  channel to share specifics

Please include:
- A description of the vulnerability and its impact
- Steps to reproduce (a minimal repro is ideal)
- The affected version/commit

We'll acknowledge reports within a few days and aim to release a fix or
mitigation promptly for anything credible. This is a hackathon/community
project without a formal SLA, but security reports are taken seriously —
especially anything that could let retrieval or the LLM call path bypass the
evidence gate (see the "no evidence, no answer" principle in the
[README](README.md)) or produce a fabricated maintenance recommendation.

## Supported versions

Only the `main` branch is supported. There are no maintained release
branches at this time — always run the latest commit.

## Security model

For how ForgeGuide AI handles uploads, credentials, CORS, and LLM-prompt
safety constraints, see [docs/SECURITY.md](docs/SECURITY.md).
