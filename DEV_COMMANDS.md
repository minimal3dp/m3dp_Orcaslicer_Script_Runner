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

## Run Tests (once set up)

```bash
uv run pytest
```
