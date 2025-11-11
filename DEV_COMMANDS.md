# Development Scripts

## Activate Virtual Environment

### macOS/Linux:

```bash
source .venv/bin/activate
```

### Windows:

```bash
.venv\Scripts\activate
```

## Run FastAPI Development Server

After activating the virtual environment:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using UV directly (without activating):

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- Main API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Install Additional Dependencies

```bash
uv add <package-name>
```

## Linting and Formatting

### Check for linting issues:
```bash
uv run ruff check .
```

### Auto-fix linting issues:
```bash
uv run ruff check --fix .
```

### Format code:
```bash
uv run ruff format .
```

### Run pre-commit hooks manually:
```bash
uv run pre-commit run --all-files
```

## Run Tests (once set up)

```bash
uv run pytest
```
