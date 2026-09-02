# Contributing to ForgeGuide AI

Thanks for considering a contribution. This project's non-negotiable
constraint is the evidence gate — see the "no evidence, no answer" principle
in the [README](README.md). Any change touching retrieval, confidence
scoring, or the LLM call path must preserve it.

## Getting set up

macOS / Linux:

```bash
git clone https://github.com/xdrew87/ForgeGuide-AI.git
cd ForgeGuide-AI
bash setup.sh
```

Windows (PowerShell 7+):

```powershell
git clone https://github.com/xdrew87/ForgeGuide-AI.git
cd ForgeGuide-AI
.\setup.ps1
```

See the [README Quick start](README.md#quick-start) for provider
configuration (Anthropic, OpenAI, or Ollama).

## Making a change

1. Fork the repo and create a branch off `main`
2. Make your change
3. Run the checks:

   ```bash
   # Backend
   docker compose exec backend python -m pytest tests/ -v

   # Frontend
   cd frontend && npm run lint && npm run build
   ```

4. If your change touches retrieval, `_estimate_confidence`, or the QA
   prompt/parsing in `backend/app/services/qa.py`, manually verify the
   no-fabrication behavior still holds: ask a question the loaded manual
   doesn't cover and confirm you get `INSUFFICIENT_EVIDENCE`, not a guess.
5. Update `README.md` / `docs/` if you changed setup, behavior, or the API
6. Open a PR against `main` using the PR template

## Code style

- Backend: standard Python, type hints where practical, no new
  abstractions/config flags beyond what the change needs
- Frontend: TypeScript, existing component patterns in `frontend/src`
- Keep diffs focused — unrelated cleanup belongs in its own PR

## Reporting bugs / requesting features

Use the issue templates. For security vulnerabilities, see
[SECURITY.md](SECURITY.md) instead of opening a public issue.

## License

By contributing, you agree your contributions are licensed under the
project's [MIT License](LICENSE).
