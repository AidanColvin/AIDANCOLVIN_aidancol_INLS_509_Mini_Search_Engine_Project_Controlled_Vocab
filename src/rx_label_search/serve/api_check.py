"""Pure request/response handling for the interaction-check API, separate from the HTTP transport."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rx_label_search.interactions.run import run_check
from rx_label_search.serve.api_search import load_build_date

MAX_MEDICATION_TEXT_CHARS = 4000


def parse_check_body(body: dict[str, Any]) -> tuple[str, bool]:
    """
    Takes the decoded JSON request body.
    Reads the medication text and whether to skip the RxNorm fallback, with safe defaults.
    Gives (medication text, use_rxnorm), the text truncated to the maximum length.
    """
    text = str(body.get("medications", ""))[:MAX_MEDICATION_TEXT_CHARS]
    use_rxnorm = bool(body.get("use_rxnorm", True))
    return text, use_rxnorm


def build_check_response(build_dir: Path, body: dict[str, Any]) -> dict[str, Any]:
    """
    Takes the build directory and the decoded JSON request body.
    Runs the interaction checker on the request's medication text.
    Gives the check report. The medication text is never logged, stored, or cached; this function is stateless.
    """
    medication_text, use_rxnorm = parse_check_body(body)
    build_date = load_build_date(build_dir)
    return run_check(build_dir, medication_text, build_date, use_rxnorm)
