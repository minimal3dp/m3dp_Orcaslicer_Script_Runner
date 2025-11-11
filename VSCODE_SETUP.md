# VS Code Setup for UV Virtual Environment

## ✅ Setup Complete!

Your VS Code workspace is now configured to use the UV virtual environment.

## What's Been Set Up

### 1. Virtual Environment

- **Location**: `.venv/` (in project root)
- **Python Version**: 3.12.9
- **Package Manager**: UV (faster than pip)

### 2. Installed Packages

- ✅ FastAPI (0.121.1)
- ✅ Uvicorn (0.38.0) - ASGI server
- ✅ Pydantic (2.12.4) - Data validation
- ✅ Starlette (0.49.3) - FastAPI core

### 3. VS Code Configuration

#### `.vscode/settings.json`

- Python interpreter set to `.venv/bin/python`
- Auto-activation in terminals enabled
- Python testing configured (pytest)
- Format on save enabled
- Import organization on save

#### `.vscode/launch.json`

- **Python: FastAPI** - Debug configuration for FastAPI app
- **Python: Current File** - Debug any Python file

#### `.vscode/extensions.json`

- Recommended extensions:
  - Python (ms-python.python)
  - Pylance (ms-python.vscode-pylance)
  - Python Debugger (ms-python.debugpy)

### 4. Project Structure

```
m3dp_Orcaslicer_Script_Runner/
├── .venv/                      # Virtual environment (UV)
├── .vscode/                    # VS Code configuration
│   ├── settings.json
│   ├── launch.json
│   └── extensions.json
├── app/                        # FastAPI application
│   ├── __init__.py
│   └── main.py                 # Main application entry point
├── scripts/
│   └── BrickLayers/            # Original BrickLayers script
├── pyproject.toml              # Project dependencies (UV)
└── README.md
```

## How to Use

### 1. Open New Terminal in VS Code

When you open a new terminal in VS Code, it should automatically activate the virtual environment. You'll see `(.venv)` in the terminal prompt.

### 2. Run the FastAPI Server

**Option A: Using UV (recommended)**

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Option B: After manual activation**

```bash
source .venv/bin/activate  # Activate venv
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Option C: Using VS Code Debugger**

1. Press `F5` or go to Run & Debug
2. Select "Python: FastAPI"
3. Server starts with debugger attached

### 3. Access the Application

Once running, you can access:

- **API Root**: http://127.0.0.1:8000/
- **Interactive Docs (Swagger UI)**: http://127.0.0.1:8000/docs
- **Alternative Docs (ReDoc)**: http://127.0.0.1:8000/redoc

### 4. Test the API

```bash
# Test root endpoint
curl http://127.0.0.1:8000/

# Test health endpoint
curl http://127.0.0.1:8000/health
```

## Managing Dependencies

### Add New Package

```bash
uv add <package-name>
```

### Add Development Package

```bash
uv add --dev <package-name>
```

### Update All Packages

```bash
uv sync --upgrade
```

### List Installed Packages

```bash
uv pip list
```

## Common Commands Reference

See `DEV_COMMANDS.md` for a comprehensive list of development commands.

## Troubleshooting

### Python Interpreter Not Found

1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Python: Select Interpreter"
3. Choose `.venv/bin/python`

### Virtual Environment Not Activating

1. Reload VS Code window: `Cmd+Shift+P` → "Developer: Reload Window"
2. Close all terminals and open a new one
3. Manually activate: `source .venv/bin/activate`

### Import Errors in Editor

- The editor may show import errors until it fully indexes the virtual environment
- Try: `Cmd+Shift+P` → "Python: Restart Language Server"
- Or simply reload the window

## Next Steps (Phase 1.1)

Now that your environment is set up, you can start with:

1. **Task 1.1.1**: Extract BrickLayers core logic into reusable module
2. **Task 1.1.3**: Implement file upload endpoint
3. **Task 1.2.1**: Create upload interface (HTML)

See `TODO.md` for the complete development roadmap.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [UV Documentation](https://github.com/astral-sh/uv)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [VS Code Python Tutorial](https://code.visualstudio.com/docs/python/python-tutorial)

---

**Status**: ✅ Environment Ready for Development
**Last Updated**: 2025-11-11
