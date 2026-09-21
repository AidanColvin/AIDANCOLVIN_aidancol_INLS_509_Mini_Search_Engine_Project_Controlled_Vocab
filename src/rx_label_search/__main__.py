"""Module entry point that defers to the command-line interface."""

import sys

from rx_label_search.cli import main

if __name__ == "__main__":
    sys.exit(main())
