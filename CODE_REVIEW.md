# Review: macrotracker

**Scope:** the uncommitted working tree on `features/api`. Source files only. No code was changed.

**How this was checked:** I installed the dependencies in a throwaway venv outside the repo and ran the app through FastAPI's `TestClient`. FRED was mocked, with no network and no real key. The cases were a good response, a `"."` value, an HTTP 400 and an HTTP 404. Findings marked **(verified)** were reproduced this way. The rest come from reading the code.

## What changed since the last review

The earlier review found that the app could not start or serve a request. That is mostly fixed. With a good FRED response, `/available`, `/indicators` and `/macrotracker` now return correct JSON.

| Old # | Issue | Status |
|---|---|---|
| 1 | Wrong `HTTPException` import | Fixed |
| 2 | uvicorn target and missing `app` | **Still broken** (see C1) |
| 3 | `Settings` field names | Fixed |
| 4 | `HealthResponse` not a `BaseModel` | Fixed |
| 5 | `DataResponse` / `DataPoint` keyword names | Fixed |
| 6 | `sync_status` type | Fixed |
| 7 | Indicator dict vs attribute access | Fixed |
| 8 | FRED param `indicator_id` | Fixed (`series_id`) |
| 12 | 503 for "no data" | Moot: that branch is never reached (see H3) |
| 31 (part) | Unused imports | Fixed |

Everything else is still open and is listed below. Severities are re-ranked.

## Critical

### C1. The `macrotracker` command still cannot start the server
**File:** `src/macrotracker/__api__.py:6`
**Problem:** `uvicorn.run("src.macrotracker:create_app", factory=True, ...)` is still wrong, for two reasons:
- `src.` is not part of the installed package name, which is `macrotracker`. The package is installed through an editable `.pth` entry, so `src` is not importable from outside the repo root.
- `macrotracker/__init__.py` is empty, so there is no `create_app` attribute. **(verified)** `import src.macrotracker` works from the repo root, but `hasattr(..., "create_app")` is `False`.

The `macrotracker` script and `python -m macrotracker` both go through `main()`, so both fail with an import or attribute error.
**Fix:** Use `uvicorn.run("macrotracker.api.app:create_app", factory=True, ...)`.

## High

### H1. The API key leaks through `/available` (verified)
**File:** `database/syncdb.py:38`, `api/app.py:31-33`, `api/routes.py:24-36`
**Problem:** The key is sent as a `?api_key=` query parameter. `raise_for_status()` puts the full URL into the exception text. `lifespan` stores that as `sync_error`, and the unauthenticated `/available` returns it. With the mocked 400 and 404 responses the body was:
`{'sync_error': '400 Client Error for url: ...?series_id=UNRATE&api_key=SECRETKEY123'}`
The same text is written to `logs/app.log` by `logger.exception`.
**Fix:** Return a generic message to clients and log the detail server-side. Catch `requests.RequestException` and re-raise with the key stripped. Redact `api_key` in logs.

### H2. The live FRED key is in git history and probably already pushed
**File:** `.env` at commit `a6e70ee` (deleted in `4495ec7`, `f7b0dcd` and `62d622a`)
**Problem:** The key in the first commit is **identical to the key in the current local `.env`** (compared by hash, not printed). The branch tracks `origin/features/api` on GitHub, so treat the key as exposed. Deleting the file in later commits does not remove it from history.
**Fix:** Revoke and reissue the key now. Rewrite history with `git filter-repo` or BFG only if the repo needs to stay clean. `.env` is already in `.gitignore`.

### H3. "No data in range" and a missing file return 500 (verified)
**File:** `services/process_request.py:16, 26`, `api/routes.py:54-57`, `database/storage.py`
**Problem:** `retrive_data` raises `DatabaseQueryError`, but the route only catches `SeriesNotFound`, which is never raised. A valid request for an empty date range (for example 1900-01-01 to 1900-03-01) returns **500 Internal Server Error**. The 503 handler in the route is dead code.
**Fix:** Raise `SeriesNotFound` for the empty-range case. Catch both exceptions in the route and return 404 for no data. Map `DatabaseQueryError` or `DatabaseNotFound` to 404 or 503.

### H4. `/macrotracker` does not check sync state, and failed syncs leave empty files (verified)
**File:** `api/routes.py:42-64`, `database/create_db.py:13-17`
**Problem:** `Database.__init__` creates an empty `<code>.db` file for each indicator before the first sync. If sync fails, the server still starts, and `/macrotracker` calls `pd.read_csv` on the empty file. This raised `EmptyDataError` and returned 500 in the 400, 404 and `"."` cases.
**Fix:** Return 503 when `state.sync_done` is false. Do not create empty placeholder files. Let `retrive_data` raise a clear error when the file is missing or empty.

### H5. One `"."` value from FRED aborts the whole sync (verified)
**File:** `database/syncdb.py:26`, `services/process_request.py:20`
**Problem:** FRED uses `"."` for missing observations. `pd.to_numeric` raised `ValueError: Unable to parse string '.'`, sync failed, and the app was left "not ready". Real series such as UNRATE and GDP are published with such gaps.
**Fix:** Use `pd.to_numeric(..., errors="coerce")` followed by `dropna(subset=["value"])`, at sync time and again on read.

### H6. A clean install cannot import the app
**File:** `pyproject.toml:10-17`, `requirements.txt`
**Problem:**
- `pandas` and `pyyaml` are imported but not declared. `uvicorn` was added.
- `requirements.txt` holds only `python-dotenv`, so it is not usable as a full dependency list.
- `dotenv>=0.9.9` is the legacy shim package. The real package is `python-dotenv`. Only `api_call_eg.py` uses it, because `pydantic-settings` reads `.env` itself.
**Fix:** Add `pandas` and `pyyaml`. Replace `dotenv` with `python-dotenv`, or drop it if the example script goes. Delete `requirements.txt` or generate it from `pyproject.toml`.

### H7. `readme = "README.md"` points at a missing file
**File:** `pyproject.toml:5`
**Problem:** No `README.md` exists, so building or installing the package with `uv_build` fails.
**Fix:** Add a README or remove the `readme` key.

## Medium

### M1. Circular import between `process_request` and `routes` (verified)
**File:** `services/process_request.py:5`, `api/routes.py:13`
**Problem:** `process_request` imports `DataRequest` from `macrotracker.api.routes`, and `routes` imports `retrive_data` from `process_request`. Importing `process_request` first raises `ImportError: cannot import name 'retrive_data' from partially initialized module`. The app only starts because `routes` happens to be imported first, so any unit test of the service will fail.
**Fix:** Import `DataRequest` from `macrotracker.models.models`.

### M2. Sync is not isolated per indicator or atomic
**File:** `database/syncdb.py:13-27`
**Problem:** An exception on one indicator stops the loop, so later indicators are never synced. `to_csv` writes straight over the live file, so a crash mid-write leaves a truncated file. This is low impact today, with one indicator and sync finishing before the server accepts requests, but it will matter once there are more indicators or a refresh.
**Fix:** Wrap each indicator in try/except and record per-indicator status. Write to a temp file, then `os.replace`.

### M3. Startup blocks on sync, so the readiness endpoint cannot show progress
**File:** `api/app.py:28-35`
**Problem:** `await asyncio.to_thread(sync, ...)` runs before `yield`, so the server accepts no connections until sync ends. `/available` can only say "ready" or "failed". Startup can take up to 30s per indicator, sync never reruns, and nothing runs after `yield`, so shutdown cannot cancel a running sync.
**Fix:** Run sync as a background task after `yield` and cancel it on shutdown, or keep it blocking and drop the unused "not ready" state. Add periodic resync if data should stay fresh.

### M4. Logs go to `src/logs/`, not the project root (verified)
**File:** `utils/logger.py:5`
**Problem:** `parents[2]` of the logger file is `src/`. The test run created `src/logs/`. `.gitignore` only has `/logs/`, so `src/logs/app.log` is not ignored and can be committed. The existing root `logs/app.log` is unused. In an installed wheel the path would land inside `site-packages`.
**Fix:** Use a configurable log path (env var or `cwd`), and ignore `logs/` at any level.

### M5. Defaults depend on the working directory
**File:** `config/source.py:20-25`
**Problem:** `.env`, `Path("database")` and `Path("config/indicator.yaml")` are all relative to the process's current directory. Running from another directory fails with a `RuntimeError` for the missing key or a `FileNotFoundError` for the YAML. The default `database/` directory also differs from the empty `data/` directory in the repo.
**Fix:** Anchor defaults to the project root, or require explicit settings. Align the default with `data/`.

### M6. The indicator YAML is not validated
**File:** `config/source.py:41-59`
**Problem:** An empty YAML gives `None`, and `.get` then raises `AttributeError` in `Database.__init__` and the routes. A missing `fred_code` raises `KeyError`. There is no check for duplicates, and codes are not normalised.
**Fix:** Parse into a pydantic model and uppercase and strip `fred_code` on load. This also fixes the case-sensitivity mismatch with `DataRequest.indicator`, which is always uppercased. A lower-case code in the YAML can never be matched.

### M7. `.db` files are CSV
**File:** `database/create_db.py:15`, `database/syncdb.py:27`, `services/process_request.py:14`
**Problem:** The files are named `<code>.db` but contain CSV. SQLite tools cannot open them, and the `database` and `DatabaseQueryError` names suggest a real DB.
**Fix:** Use `.csv`, or switch to `sqlite3` or parquet.

### M8. Dead 404 branch in `query_api`
**File:** `database/syncdb.py:36-49`
**Problem:** `raise_for_status()` runs first and already raises `HTTPError` on 404, so the `DatabaseNotFound` branch can never run. **(verified)** The 404 case surfaced as an `HTTPError`. `DatabaseNotFound` is also the wrong exception for an upstream 404.
**Fix:** Check the status code before `raise_for_status()`, or delete the branch.

### M9. The server binds to `0.0.0.0` with no authentication
**File:** `__api__.py:8`
**Problem:** Every endpoint is public on all interfaces. Together with H1, anyone on the network can read the key from `/available`.
**Fix:** Default to `127.0.0.1` and make the host configurable. Add auth if the service is meant to be exposed.

## Low

### L1. Inefficient request handling
**File:** `services/process_request.py:18-28`, `api/routes.py:45-46`
**Problem:** Every request re-reads and re-parses the whole CSV and builds `DataPoint` objects with `iterrows()`. The indicator ID list is rebuilt on every request.
**Fix:** Cache parsed data in memory after sync, use a vectorised conversion, and precompute the set of codes at startup.

### L2. Loose response typing and misleading root text
**File:** `models/models.py:43-44`, `api/routes.py:38-43, 66-68`
**Problem:** `IndicatorsResponse.indicators` is `list[dict]`. `/macrotracker` has no `response_model`. The root endpoint tells users to use `/macrotracker`, but that route is POST-only. `/available` returns 500 for a failed sync, where 503 would be more usual for a readiness probe.
**Fix:** Add an `Indicator` model, declare `response_model=DataResponse`, and update the root message.

### L3. `api_call_eg.py` is a stray script
**File:** `api_call_eg.py`
**Problem:** It calls the network and needs a key at import time. It prints `page_observations[1:10]`, which skips the first observation. It has inconsistent indentation on lines 20-26 and duplicates `query_api`.
**Fix:** Delete it, or move it to `examples/` behind `if __name__ == "__main__":` and print `[:10]`.

### L4. Housekeeping
- `pyproject.toml:4` still says "Add your description here".
- The `test` dependency group has no tests, and **there are no tests at all**. The cases above (empty range, `"."` value, failed sync, circular import) are good first tests.
- `config/indicator.yaml` has no trailing newline. Several source files also lack one.
- `logger.py` is indented with tabs and the rest of the code with spaces.
- `database/storage.py` holds only exception classes and is misnamed. Typos: `retrive_data`, `fuction`, `peform`, `respose`.
- `data/` and `excel/` are empty and unused. `config/__init__.py` and similar files are empty placeholders.

## Suggested order of work

1. Revoke the leaked key (H2), then stop returning raw exception text (H1).
2. Fix the uvicorn target (C1). Declare the missing dependencies and the README (H6, H7).
3. Handle the FRED `"."` marker (H5). Fix the 500 paths in `/macrotracker` (H3, H4).
4. Break the circular import (M1) and add tests for the cases above.
