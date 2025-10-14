# Repository Guidelines

## Project Structure & Module Organization
- `backend/` — FastAPI services, WebSocket workers, and integration with the Korea Investment API. Source lives under `app/`, with tests in `backend/tests/` and helper scripts in `backend/scripts/`.
- `stock-trading-ui/` — Next.js 15 frontend. Components live in `src/components/`, hooks in `src/hooks/`, and API helpers in `src/lib/`. Run `npm install` here before frontend work.
- `docs/` — Architecture notes, recovery plans, and work logs. New execution notes belong in `docs/execution/`; bug-related write-ups go in `docs/bugfix/`.
- `brokers/`, `services/`, `core/`, and `utils/` at the repo root contain legacy/shared Python modules still referenced by the backend.

## Build, Test, and Development Commands
- `cd backend && scripts/start_backend.sh` — Activates the `vkis` virtual env and launches FastAPI with auto-reload at <http://localhost:8000>.
- `cd backend && ./vkis/bin/python -m pytest` — Runs backend unit and integration tests (pytest + asyncio plugins).
- `cd stock-trading-ui && npm run dev` — Starts the Next.js dev server on <http://localhost:9000>.
- `cd stock-trading-ui && npm run test` — Executes Jest/Testing Library suites for UI logic.

## Coding Style & Naming Conventions
- Python code follows PEP 8, 4-space indentation, and descriptive snake_case names. Prefer pydantic models for request/response schemas.
- TypeScript/React components use PascalCase filenames (e.g., `MarketOverview.tsx`), while hooks/utilities stay in camelCase.
- Use ESLint and Prettier defaults (`npm run lint` / `npm run format`) before committing frontend changes.

## Testing Guidelines
- Backend tests live under `backend/tests/`, named `test_<feature>.py`. Write async tests with `@pytest.mark.asyncio` when hitting live APIs.
- Frontend tests should mirror component locations inside `stock-trading-ui/src/__tests__/` or adjacent `*.test.ts(x)` files.
- When validating KIS integrations, prefer sandbox credentials and record raw responses in `logs/API_YYYYMMDD.log` for troubleshooting.

## Commit & Pull Request Guidelines
- Craft commit messages in imperative mood (“Add WebSocket cache for indices”). Use short subject lines (<72 chars) with optional detail in the body.
- Each PR should include: summary of changes, test evidence (`pytest`, `npm run test`, manuals), and linked task/issue IDs. Add screenshots or CLI output when UI or API behavior changes.

## Security & Configuration Tips
- Never commit API keys. Backend reads credentials from `config.yaml`/environment variables; share secrets via approved vaults.
- Regenerate Korean Investment tokens before integration tests and store them under `backend/token_backup/` only when encrypted.


## Fast Tools for Speedy Searches

To make your work faster in large repositories, use these optimized tools instead of the defaults. They are pre-installed or can be installed via your package manager (e.g., brew on macOS, apt on Linux).

### File Content Search
- Use `rg` (ripgrep) for searching text inside files. It's 10x faster than `grep`.
  - Example: `rg "pattern" .` to search for "pattern" in current directory.
  - Install: `brew install ripgrep` or `sudo apt install ripgrep`.

### File Discovery
- Use `fd` for finding files and directories. Faster and more user-friendly than `find`.
  - Example: `fd pattern` to find files matching "pattern".
  - Install: `brew install fd` or `sudo apt install fd-find` (then alias `fd=fdfind` in ~/.bashrc).

### JSON Processing
- Use `jq` for parsing and manipulating JSON data. Essential for API responses and config files.
  - Example: `cat data.json | jq '.key'`.
  - Install: `brew install jq` or `sudo apt install jq`.

### Usage Rules for Agent
- Always prefer these tools over `grep`, `find`, or manual parsing.
- If a tool is not available, fall back to defaults but note it in your response.
- For WSL/Windows: Ensure tools are installed in the Linux subsystem for seamless integration.

This setup reduces search time from seconds to milliseconds. Run `/setup fast tools` in a Codex session to auto-append this to AGENTS.md.
