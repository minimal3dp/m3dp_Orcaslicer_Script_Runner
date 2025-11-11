# Changelog

All notable changes to the BrickLayers Web Application project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project will adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added - 2025-11-11

#### Project Setup
- Initialized UV package manager with Python 3.12.9
- Created virtual environment (.venv)
- Installed FastAPI (0.121.1) and Uvicorn (0.38.0)
- Set up VS Code workspace configuration
- Created debug configuration for FastAPI

#### Code Quality Tools
- Added Ruff (0.14.4) for fast linting and formatting
- Configured Ruff with comprehensive rule set (pycodestyle, pyflakes, isort, etc.)
- Added pre-commit (4.4.0) hooks for automated quality checks
- Installed pre-commit hooks into git repository
- Configured VS Code to use Ruff for formatting and linting

#### Project Structure
- Created `app/` directory for FastAPI application
- Created `app/main.py` with basic FastAPI setup and health endpoints
- Created `.vscode/` with settings, launch, and extensions configurations
- Created `.pre-commit-config.yaml` with comprehensive hooks

#### Documentation
- Created TODO.md with detailed 5-phase development roadmap
- Created CHANGELOG.md for tracking project progress
- Created VSCODE_SETUP.md with environment setup instructions
- Created DEV_COMMANDS.md with common development commands
- Created LINTING_SETUP.md with code quality guidelines

#### Configuration Files
- Updated `pyproject.toml` with Ruff configuration
- Configured line length (100), target Python version (3.12)
- Enabled linting rules: pycodestyle, pyflakes, isort, pyupgrade, bugbear, simplify
- Configured import sorting and formatting preferences

### Project Inception

- Analyzed BrickLayers v0.2.1-10-g6409588 script for web integration
- Identified technology stack: Python (FastAPI) + HTML/JavaScript
- Defined project scope and phases

### Planning

- Documented MVP requirements (Phase 1)
- Outlined enhancement roadmap (Phases 2-5)
- Identified key technical decisions needed
- Created milestone timeline estimates
- Listed learning resources and deployment options

---

## [0.1.0] - TBD (Planned MVP Release)

### Planned Features

- Basic web interface for G-code upload
- Integration with BrickLayers processing engine
- Parameter configuration (startAtLayer, extrusionMultiplier)
- Processed G-code download
- Basic error handling and validation
- Simple progress indication

### Technical Implementation (Planned)

- FastAPI or Flask backend
- HTML/JavaScript frontend (no framework initially)
- Temporary file storage with auto-cleanup
- Async processing support
- Basic security measures (file validation, size limits)

### Documentation (Planned)

- README with setup instructions
- Basic user guide
- API documentation

---

## Future Versions (Planned)

### [0.2.0] - Enhanced UX (Planned)

- Real-time progress reporting (WebSocket/SSE)
- Improved UI with responsive design
- Better error messages and user feedback
- Before/after file statistics

### [0.3.0] - Advanced Features (Planned)

- G-code visualization/preview
- Additional BrickLayers parameters
- Parameter presets
- Batch file processing

### [0.4.0] - Production Ready (Planned)

- User accounts (optional)
- Job history
- Performance optimizations
- Comprehensive testing suite
- Production deployment

### [1.0.0] - Public Launch (Planned)

- Full feature set complete
- Comprehensive documentation
- Community features
- Stable API
- Marketing and launch

---

## Development Notes

### References to Upstream BrickLayers Script

This web application is based on the BrickLayers post-processing script:

- **Current Version**: v0.2.1-10-g6409588
- **Repository**: https://github.com/GeekDetour/BrickLayers
- **Alternative Fork**: https://github.com/TengerTechnologies/Bricklayers
- **Author**: Everson Siqueira (Geek Detour)
- **License**: GNU GPL v3

### Key Changes from Original Script

_(To be documented as development progresses)_

- Refactored for web API integration
- Separated CLI from core processing logic
- Added async processing support
- Implemented progress callback mechanism
- Enhanced error handling for web context

---

## Contributing

This project is in its early planning and development phase. Contributions, suggestions, and feedback are welcome!

### How to Contribute

1. Review the TODO.md for planned features
2. Check existing issues and discussions
3. Suggest improvements or report bugs
4. Submit pull requests with clear descriptions

---

## Links

- **Project Repository**: TBD (to be created on GitHub)
- **Original BrickLayers Script**: https://github.com/GeekDetour/BrickLayers
- **CNC Kitchen Blog**: https://www.cnckitchen.com/blog/brick-layers-make-3d-prints-stronger
- **Hackaday Article**: https://hackaday.com/2025/03/17/3d-printed-brick-layers-for-everyone/

---

## Acknowledgments

- **Everson Siqueira (Geek Detour)**: Original BrickLayers script author
- **Stefan Hermann (CNC Kitchen)**: BrickLayers technique popularization
- **TengerTechnologies**: Alternative implementation and contributions
- **3D Printing Community**: Testing and feedback

---

**Legend**:

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

---

**Project Start Date**: 2025-11-11
**Last Updated**: 2025-11-11
**Status**: Planning Phase
