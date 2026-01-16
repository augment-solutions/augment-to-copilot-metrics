"""
Entry point for running augment_metrics as a module.

Usage:
    python -m augment_metrics --last-28-days
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())

