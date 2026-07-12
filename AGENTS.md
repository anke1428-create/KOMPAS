# KOMPAS

Clinical reasoning agent (Dutch GGZ) built on the OpenAI Agents SDK. Turns case text into a
structured KOMPAS report (hypotheses, case conceptualization, maintaining mechanisms, treatment
indication). Exposes a CLI and a FastAPI server; can render reports to a Word (`.docx`) document.

## Cursor Cloud specific instructions

### Tooling / dependencies
- Package manager is **uv** (see `pyproject.toml` / `uv.lock`). It is installed to `~/.local/bin`
  and is already on `PATH` via `~/.bashrc`, so `uv` works in fresh shells.
- Refresh dependencies with `uv sync` (this is what the startup update script runs). This creates
  the `.venv/` used by `uv run`.
- Target runtime is Python `>=3.11`; the VM's system Python 3.12 satisfies this.

### Running (see `README.md` for the authoritative commands)
- CLI: `uv run python main.py --file data/sample_case.txt` (or pipe case text via stdin).
- API server: `PORT=8000 uv run python main.py`, then `GET /health`, `POST /analyze`,
  `POST /analyze/docx`.

### Runtime secrets (non-obvious)
- `OPENAI_API_KEY` **must** be present in the environment at runtime or the agent calls fail.
  `python-dotenv` is a dependency, so a git-ignored `.env.local` at the repo root is honored in
  addition to real environment variables. `.env` / `.env.local` are git-ignored — never commit them.
- `OPENAI_MODEL` is optional and overrides the default model.
- Use only anonymized / fictional case data during development (this is a clinical tool).
