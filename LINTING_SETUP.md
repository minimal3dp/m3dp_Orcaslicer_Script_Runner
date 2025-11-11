# Linting and Code Quality Setup

## Overview

This project uses **Ruff** for linting and formatting, along with **pre-commit** hooks to ensure code quality before commits.

## Tools Installed

### Ruff
- **Fast** Python linter and formatter (10-100x faster than alternatives)
- Replaces multiple tools: Black, isort, flake8, pyupgrade, and more
- Configuration in `pyproject.toml`

### Pre-commit
- Automatically runs checks before each git commit
- Catches issues early in development
- Configuration in `.pre-commit-config.yaml`

## Using Ruff

### Lint Your Code
Check for linting issues:
```bash
# Check all files
uv run ruff check .

# Check specific directory
uv run ruff check app/

# Check and auto-fix issues
uv run ruff check --fix .
```

### Format Your Code
Format code according to project style:
```bash
# Format all files
uv run ruff format .

# Format specific directory
uv run ruff format app/

# Check formatting without making changes
uv run ruff format --check .
```

### VS Code Integration
Ruff is integrated into VS Code:
- **Auto-format on save** - Code is automatically formatted when you save
- **Auto-fix on save** - Some linting issues are fixed automatically
- **Inline linting** - See linting errors/warnings in the editor
- **Organize imports** - Imports are sorted automatically

To manually trigger formatting in VS Code:
- **Format Document**: `Shift + Option + F` (macOS) or `Shift + Alt + F` (Windows/Linux)
- **Organize Imports**: `Shift + Option + O` (macOS) or `Shift + Alt + O` (Windows/Linux)

## Using Pre-commit

### Automatic Checks
Pre-commit hooks run automatically before each commit. If any check fails, the commit is blocked until issues are fixed.

### Manual Execution
Run all hooks manually:
```bash
# Run on all files
uv run pre-commit run --all-files

# Run on staged files only
uv run pre-commit run

# Run specific hook
uv run pre-commit run ruff --all-files
```

### Update Hooks
Update pre-commit hook versions:
```bash
uv run pre-commit autoupdate
```

## Pre-commit Checks

The following checks run on every commit:

### 1. Ruff Linter
- Checks Python code for style and logical errors
- Auto-fixes issues when possible
- Enforces import sorting

### 2. Ruff Format
- Ensures consistent code formatting
- Similar to Black formatter
- Auto-formats code to match project style

### 3. File Checks
- **Trailing whitespace** - Removes trailing spaces
- **End of file** - Ensures files end with newline
- **YAML validation** - Checks YAML syntax
- **JSON validation** - Checks JSON syntax (excludes VS Code configs)
- **TOML validation** - Checks TOML syntax

### 4. Security Checks
- **Large files** - Prevents committing files >10MB
- **Case conflicts** - Detects case-insensitive filename conflicts
- **Merge conflicts** - Detects unresolved merge conflict markers
- **Private keys** - Detects accidentally committed private keys

### 5. Python-Specific
- **AST check** - Validates Python syntax
- **Builtin literals** - Suggests using literal syntax
- **Docstring first** - Ensures docstrings come before code
- **Debug statements** - Detects leftover debugger statements
- **Test naming** - Ensures test files follow naming convention

## Ruff Configuration

Configuration is in `pyproject.toml`. Key settings:

```toml
[tool.ruff]
line-length = 100          # Maximum line length
target-version = "py312"   # Target Python version

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify
    "ARG",  # flake8-unused-arguments
    "PTH",  # flake8-use-pathlib
    "RUF",  # Ruff-specific rules
]
```

## Common Workflows

### Before Committing
1. **Save your files** - VS Code will auto-format on save
2. **Check for issues** - `uv run ruff check .`
3. **Commit** - Pre-commit hooks will run automatically

### Fixing Linting Issues
```bash
# See what issues exist
uv run ruff check .

# Auto-fix what can be fixed
uv run ruff check --fix .

# Format code
uv run ruff format .

# Check everything is good
uv run pre-commit run --all-files
```

### Bypassing Pre-commit (Not Recommended)
If you absolutely need to commit without running hooks:
```bash
git commit --no-verify -m "Your message"
```

⚠️ **Warning**: Only use this in emergencies. Bypassing checks can introduce code quality issues.

## Troubleshooting

### Pre-commit Hooks Not Running
```bash
# Reinstall hooks
uv run pre-commit uninstall
uv run pre-commit install

# Clear cache and try again
uv run pre-commit clean
uv run pre-commit run --all-files
```

### Ruff Not Found in VS Code
1. Reload VS Code: `Cmd+Shift+P` → "Developer: Reload Window"
2. Check Python interpreter: Should be `.venv/bin/python`
3. Install Ruff extension: `charliermarsh.ruff`

### Format on Save Not Working
1. Check VS Code settings: `editor.formatOnSave` should be `true`
2. Check Python settings: `"[python]"."editor.defaultFormatter"` should be `"charliermarsh.ruff"`
3. Reload window and try again

### Pre-commit is Slow
First run is slow (installing environments), subsequent runs are much faster. The environment is cached.

## Best Practices

1. **Commit often** - Smaller commits are easier to review and fix
2. **Fix issues immediately** - Don't accumulate linting debt
3. **Read error messages** - Ruff provides helpful explanations
4. **Use auto-fix** - Let Ruff fix simple issues automatically
5. **Format on save** - Keep code formatted as you work
6. **Run pre-commit** - Check all files before pushing

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Python Code Quality](https://realpython.com/python-code-quality/)

---

**Last Updated**: 2025-11-11
