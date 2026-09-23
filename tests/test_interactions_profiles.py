"""Tests for the drug profile on the medication card (interactions/profiles.py): class explanations and quoted label statements."""

from __future__ import annotations

import json
from pathlib import Path

from rx_label_search.interactions.profiles import classes_for, clean_sentence, label_profile

TABLE = json.loads((Path(__file__).resolve().parent.parent / "data" / "reference" / "drug_classes.json").read_text())


def test_label_profile_quotes_uses_mechanism_dose_maximum_and_duration() -> None:
    """
    Takes no arguments.
    Builds a profile from a label record shaped like the alprazolam label.
    Gives nothing; asserts each section quotes the right sentence and study sentences are not read as duration advice.
    """
    record = {
        "openfda": {"pharm_class_epc": ["Benzodiazepine [EPC]"]},
        "indications_and_usage": ["1 INDICATIONS AND USAGE Alprazolam tablets are indicated for the acute treatment of generalized anxiety disorder in adults [see Clinical Studies (14.1)]."],
        "mechanism_of_action": ["12.1 Mechanism of Action Alprazolam binds the benzodiazepine site of GABA-A receptors and enhances GABA-mediated synaptic inhibition."],
        "dosage_and_administration": ["2.1 Recommended starting oral dosage is 0.25 mg to 0.5 mg three times daily. The maximum recommended dosage is 4 mg daily. To reduce the risk of withdrawal reactions, use a gradual taper to discontinue alprazolam."],
        "warnings_and_cautions": ["In short-term studies, patients improved."],
    }
    profile = label_profile(record)
    assert profile["indications"] == ["Alprazolam tablets are indicated for the acute treatment of generalized anxiety disorder in adults."]
    assert "GABA-A" in profile["mechanism"][0]
    assert profile["dose_recommended"] == ["Recommended starting oral dosage is 0.25 mg to 0.5 mg three times daily."]
    assert profile["dose_maximum"] == ["The maximum recommended dosage is 4 mg daily."]
    assert profile["duration"] == ["To reduce the risk of withdrawal reactions, use a gradual taper to discontinue alprazolam."]


def test_clean_sentence_drops_headers_and_cross_references() -> None:
    """
    Takes no arguments.
    Cleans a label sentence carrying a section header and a cross-reference.
    Gives nothing; asserts only the statement remains.
    """
    assert clean_sentence("1 INDICATIONS AND USAGE Zolpidem is indicated for insomnia ( 1 ) [see Warnings (5.1)].") == "Zolpidem is indicated for insomnia."


def test_classes_match_salts_and_every_class_cites_an_nih_or_pubmed_source() -> None:
    """
    Takes no arguments.
    Looks up alprazolam and lithium carbonate, and checks every class's sources.
    Gives nothing; asserts the benzodiazepine and lithium classes are found and every source is NIH NCBI Bookshelf or PubMed.
    """
    assert [entry["id"] for entry in classes_for(["alprazolam"], TABLE)] == ["benzodiazepine"]
    assert [entry["id"] for entry in classes_for(["lithium carbonate"], TABLE)] == ["lithium"]
    for entry in TABLE["classes"]:
        for source in entry["sources"]:
            assert source["url"].startswith(("https://www.ncbi.nlm.nih.gov/books/", "https://pubmed.ncbi.nlm.nih.gov/"))
