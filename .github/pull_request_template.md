## Summary

<!-- What does this change do, and why? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Dependency / security update
- [ ] Refactor / chore

## Checklist

- [ ] `docker compose exec backend python -m pytest tests/ -v` passes (or `cd backend && python -m pytest tests/ -v`)
- [ ] `cd frontend && npm run lint && npm run build` passes
- [ ] If this touches retrieval, confidence scoring, or the LLM call path: I confirmed the evidence gate still declines to answer when the manual doesn't cover the question (no-fabrication regression) — see `docs/SECURITY.md`
- [ ] I updated relevant docs (`README.md`, `docs/`) if behavior or setup changed

## Related issues

<!-- e.g. Closes #12 -->
