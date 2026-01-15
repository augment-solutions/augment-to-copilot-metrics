# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (PR #2 - Authentication Layer)
- `src/augment_metrics/config.py` - Pydantic-based configuration management
- `src/augment_metrics/token_auth.py` - Secure API token storage and validation
- `src/augment_metrics/http.py` - HTTP client with Bearer token authentication
- Comprehensive unit tests (31 tests, 99% coverage)
- Virtual environment support with venv
- Development dependencies (pytest, black, ruff, mypy)

### Changed
- Updated `src/augment_metrics/__init__.py` to export new modules

## [0.1.0] - 2026-01-15

### Added (PR #1 - Project Foundation)
- Initial project structure (src/, tests/, docs/, scripts/)
- Python package configuration (pyproject.toml, requirements.txt)
- Environment configuration template (.env.example)
- Comprehensive documentation:
  - README.md - Project overview and quick start
  - docs/ARCHITECTURE.md - System architecture and design decisions
  - docs/FIELD_MAPPING.md - Augment → Copilot field transformations
  - docs/IMPLEMENTATION_PLAN.md - 8-phase development roadmap
  - docs/OLD_VS_NEW_COMPARISON.md - Comparison with cookie-based approach
- PR template for consistent contributions
- MIT License

[unreleased]: https://github.com/augment-solutions/augment-to-copilot-metrics/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/augment-solutions/augment-to-copilot-metrics/releases/tag/v0.1.0
