"""Android/desktop entry point for Flet Build.

Flet's `build` command expects a single module at the app root; the real
application lives in the `easyotp` package.
"""
from easyotp.main import main

if __name__ == "__main__":
    main()
