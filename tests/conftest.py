"""Shared fixtures that load the committed openFDA label fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from rx_label_search.storage.read_json import read_json

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
LABEL_DIR = FIXTURE_DIR / "labels"
FIXTURE_NAMES = (
    "olanzapine_zyprexa",
    "adderall",
    "zolpidem_ambien",
    "trazodone",
    "desvenlafaxine",
    "venlafaxine",
    "cyclobenzaprine",
    "pregabalin_lyrica",
    "oxycontin",
    "gabapentin",
    "entresto",
    "dextroamphetamine",
    "losartan",
    "adderall_current_collection_winner",
    "adderall_xr",
)


def load_fixture_label(name: str) -> dict[str, Any]:
    """
    Takes a fixture name.
    Reads the fixture file and unwraps the raw openFDA label record inside it.
    Gives the label record, or raises FileNotFoundError when the fixture is missing.
    """
    return read_json(LABEL_DIR / f"{name}.json")["label"]


@pytest.fixture(scope="session")
def fixture_labels() -> dict[str, dict[str, Any]]:
    """
    Takes no arguments.
    Loads every committed fixture label once per test session.
    Gives a mapping from fixture name to raw label record.
    """
    return {name: load_fixture_label(name) for name in FIXTURE_NAMES}
