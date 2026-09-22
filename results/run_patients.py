"""Drives the live Drug Interaction Screen checker for 10 synthetic patients and reports the results.

For each patient, loads a fresh page, fills the medication-list textbox and
clicks "Check interactions" (both found by accessible role and name), waits
for the discovered POST /api/check network response directly rather than
scraping the DOM, and also captures the rendered results-panel text and a
full-page screenshot. Writes one Markdown report covering all ten patients.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Locator, Page, Response, TimeoutError as PlaywrightTimeoutError, sync_playwright

SITE_URL = "https://rx-label-search-aidancolvins-projects.vercel.app/"
TEXTBOX_LABEL = "Medication list (comma, semicolon, or new-line separated)"
BUTTON_NAME = "Check interactions"
CHECK_ENDPOINT_MARKER = "/api/check"
RESULTS_TIMEOUT_MS = 30_000
RESULTS_DIR = Path(__file__).resolve().parent / "results"

PATIENTS: tuple[tuple[int, str], ...] = (
    (1, "Alprazolam 1 mg 3 times daily, Zolpidem 10 mg 1 time daily, Lisinopril 10 mg 1 time daily, Atorvastatin 20 mg 1 time daily, Sertraline 50 mg 1 time daily, Omeprazole 20 mg 1 time daily"),
    (2, "Metformin 500 mg 2 times daily, Amlodipine 5 mg 1 time daily, Simvastatin 20 mg 1 time daily, Losartan 50 mg 1 time daily, Gabapentin 300 mg 3 times daily, Levothyroxine 50 mcg 1 time daily"),
    (3, "Hydrochlorothiazide 25 mg 1 time daily, Metoprolol Succinate 50 mg 1 time daily, Escitalopram 10 mg 1 time daily, Pantoprazole 40 mg 1 time daily, Montelukast 10 mg 1 time daily, Rosuvastatin 10 mg 1 time daily"),
    (4, "Glipizide 5 mg 2 times daily, Valsartan 80 mg 1 time daily, Pravastatin 20 mg 1 time daily, Duloxetine 30 mg 1 time daily, Famotidine 20 mg 2 times daily, Albuterol 90 mcg 2 puffs as needed"),
    (5, "Carvedilol 6.25 mg 2 times daily, Furosemide 20 mg 1 time daily, Spironolactone 25 mg 1 time daily, Warfarin 5 mg 1 time daily, Digoxin 125 mcg 1 time daily, Potassium Chloride 20 mEq 1 time daily"),
    (6, "Bupropion XL 150 mg 1 time daily, Trazodone 50 mg 1 time daily at bedtime, Amoxicillin 500 mg 3 times daily, Ibuprofen 600 mg 3 times daily as needed, Cyclobenzaprine 10 mg 3 times daily as needed, Fluticasone 50 mcg 2 sprays daily"),
    (7, "Empagliflozin 10 mg 1 time daily, Telmisartan 40 mg 1 time daily, Ezetimibe 10 mg 1 time daily, Venlafaxine ER 75 mg 1 time daily, Esomeprazole 40 mg 1 time daily, Meloxicam 15 mg 1 time daily"),
    (8, "Diltiazem ER 180 mg 1 time daily, Apixaban 5 mg 2 times daily, Allopurinol 100 mg 1 time daily, Tamsulosin 0.4 mg 1 time daily, Finasteride 5 mg 1 time daily, Acetaminophen 500 mg 4 times daily as needed"),
    (9, "Sitagliptin 100 mg 1 time daily, Nifedipine ER 30 mg 1 time daily, Lovastatin 20 mg 1 time daily, Fluoxetine 20 mg 1 time daily, Famotidine 40 mg 1 time daily, Cetirizine 10 mg 1 time daily"),
    (10, "Ramipril 5 mg 1 time daily, Chlorthalidone 25 mg 1 time daily, Pitavastatin 2 mg 1 time daily, Paroxetine 20 mg 1 time daily, Dicyclomine 20 mg 4 times daily as needed, Loratadine 10 mg 1 time daily"),
)


@dataclass(frozen=True)
class PatientResult:
    """One patient's captured outcome: the API response, the rendered panel text, and pass/fail."""

    patient_number: int
    medications: str
    passed: bool
    status_code: int | None
    response_json: dict[str, object] | None
    panel_text: str
    error: str | None
    screenshot_path: Path


def find_medication_textbox(page: Page) -> Locator:
    """
    Takes the page to search.
    Locates the medication-list textbox by its accessible label.
    Gives the Playwright locator for that textbox.
    """
    return page.get_by_role("textbox", name=TEXTBOX_LABEL)


def find_check_button(page: Page) -> Locator:
    """
    Takes the page to search.
    Locates the "Check interactions" button by its accessible role and name.
    Gives the Playwright locator for that button.
    """
    return page.get_by_role("button", name=BUTTON_NAME)


def find_results_panel(page: Page) -> Locator:
    """
    Takes the page to search.
    Locates the results panel by its element id, as seen in the page markup.
    Gives the Playwright locator for that panel.
    """
    return page.locator("#check-results")


def is_check_response(response: Response) -> bool:
    """
    Takes one network response.
    Checks whether its URL is the discovered interaction-check endpoint.
    Gives True when it is, False otherwise.
    """
    return CHECK_ENDPOINT_MARKER in response.url


def wait_for_panel_text_to_settle(page: Page, timeout_ms: int) -> str:
    """
    Takes the page and a timeout in milliseconds.
    Polls the results panel until its text is no longer the "Checking…" placeholder or empty.
    Gives the settled panel text, or whatever text is present when the timeout is reached.
    """
    panel = find_results_panel(page)
    try:
        page.wait_for_function(
            "el => el && el.innerText.trim().length > 0 && !el.innerText.includes('Checking')",
            arg=panel.element_handle(),
            timeout=timeout_ms,
        )
    except PlaywrightTimeoutError:
        pass
    return panel.inner_text()


def submit_one_patient(page: Page, patient_number: int, medications: str) -> PatientResult:
    """
    Takes the page, the patient number, and the medication list to submit.
    Fills the textbox, clicks the check button, and captures the /api/check response, the rendered panel text, and a screenshot.
    Gives the PatientResult, marked failed with the raw error when anything times out or the response is not 200.
    """
    screenshot_path = RESULTS_DIR / f"patient_{patient_number:02d}.png"
    find_medication_textbox(page).fill(medications)
    try:
        with page.expect_response(is_check_response, timeout=RESULTS_TIMEOUT_MS) as response_info:
            find_check_button(page).click()
        response = response_info.value
        panel_text = wait_for_panel_text_to_settle(page, RESULTS_TIMEOUT_MS)
        page.screenshot(path=str(screenshot_path), full_page=True)
        return build_result_from_response(patient_number, medications, response, panel_text, screenshot_path)
    except PlaywrightTimeoutError as error:
        page.screenshot(path=str(screenshot_path), full_page=True)
        return PatientResult(patient_number, medications, False, None, None, find_results_panel(page).inner_text(), f"timed out waiting for {CHECK_ENDPOINT_MARKER}: {error}", screenshot_path)


def build_result_from_response(patient_number: int, medications: str, response: Response, panel_text: str, screenshot_path: Path) -> PatientResult:
    """
    Takes the patient number, medications, the captured response, the panel text, and the screenshot path.
    Parses the response as JSON and checks its status.
    Gives the PatientResult, failed with the raw body when the status is not 200 or the body is not valid JSON.
    """
    if response.status != 200:
        return PatientResult(patient_number, medications, False, response.status, None, panel_text, f"HTTP {response.status}: {response.text()[:2000]}", screenshot_path)
    try:
        body = response.json()
    except ValueError as error:
        return PatientResult(patient_number, medications, False, response.status, None, panel_text, f"response was not valid JSON: {error}; raw body: {response.text()[:2000]}", screenshot_path)
    return PatientResult(patient_number, medications, True, response.status, body, panel_text, None, screenshot_path)


def run_all_patients() -> list[PatientResult]:
    """
    Takes no arguments.
    Loads a fresh page for each of the 10 patients and submits their medication list.
    Gives the list of PatientResult in patient order.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results: list[PatientResult] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for patient_number, medications in PATIENTS:
            page = browser.new_page()
            page.goto(SITE_URL, wait_until="domcontentloaded")
            find_medication_textbox(page).wait_for(state="visible", timeout=RESULTS_TIMEOUT_MS)
            results.append(submit_one_patient(page, patient_number, medications))
            page.close()
        browser.close()
    return results


def alerts_summary(response_json: dict[str, object] | None) -> str:
    """
    Takes a parsed /api/check response, or None.
    Formats each alert's kind, risk term, and title as one line per alert.
    Gives the joined summary text, or a fixed no-data message when the response is missing or has no alerts.
    """
    if response_json is None:
        return "(no response data)"
    alerts = response_json.get("alerts") or []
    if not alerts:
        return response_json.get("no_warning_text", "No warning found in the labels checked.")
    lines = [f"- [{alert['kind']}/{alert['risk']}] {alert['title']} — tier: {alert.get('tier_name', 'n/a')}" for alert in alerts]
    return "\n".join(lines)


def unresolved_summary(response_json: dict[str, object] | None) -> str:
    """
    Takes a parsed /api/check response, or None.
    Lists every unresolved medication entry and its reason.
    Gives the joined summary text, or "(none)" when nothing is unresolved or the response is missing.
    """
    if response_json is None:
        return "(no response data)"
    unresolved = response_json.get("unresolved_entries") or []
    if not unresolved:
        return "(none)"
    return "; ".join(f"\"{entry['raw_text']}\" ({entry['reason']})" for entry in unresolved)


def format_patient_section(result: PatientResult) -> str:
    """
    Takes one patient's result.
    Formats it as one Markdown section with the medication list, alerts, unresolved entries, and pass/fail.
    Gives the section text.
    """
    status = "PASS" if result.passed else "FAIL"
    lines = [
        f"## Patient {result.patient_number} — {status}",
        "",
        f"**Medications submitted:** {result.medications}",
        "",
        f"**HTTP status:** {result.status_code if result.status_code is not None else '(no response)'}",
        "",
        "**Alerts returned:**",
        "```",
        alerts_summary(result.response_json),
        "```",
        "",
        f"**Unresolved entries:** {unresolved_summary(result.response_json)}",
        "",
        f"**Screenshot:** `{result.screenshot_path.relative_to(RESULTS_DIR.parent)}`",
    ]
    if result.error is not None:
        lines += ["", f"**Error:** {result.error}"]
    lines += ["", "**Results panel text (verbatim):**", "```", result.panel_text.strip() or "(empty)", "```"]
    return "\n".join(lines)


def format_summary_table(results: list[PatientResult]) -> str:
    """
    Takes every patient's result.
    Builds a Markdown table with one row per patient: number, drug count, alert count, and pass/fail.
    Gives the table text.
    """
    header = "| Patient | Drugs | Alerts | Unresolved | Result |\n| :--- | ---: | ---: | ---: | :--- |"
    rows = []
    for result in results:
        drug_count = len(result.medications.split(","))
        alert_count = len((result.response_json or {}).get("alerts") or []) if result.response_json else 0
        unresolved_count = len((result.response_json or {}).get("unresolved_entries") or []) if result.response_json else 0
        rows.append(f"| {result.patient_number} | {drug_count} | {alert_count} | {unresolved_count} | {'PASS' if result.passed else 'FAIL'} |")
    return "\n".join([header, *rows])


def build_report(results: list[PatientResult]) -> str:
    """
    Takes every patient's result.
    Assembles the full Markdown report: a summary table followed by one section per patient.
    Gives the report text.
    """
    passed = sum(1 for result in results if result.passed)
    header = [
        "# Drug Interaction Screen — live QA report",
        "",
        f"Target: {SITE_URL}",
        f"Discovered endpoint: `POST {CHECK_ENDPOINT_MARKER}` with JSON body `{{\"medications\": <text>, \"use_rxnorm\": true}}`, found by intercepting network traffic from a real click of the \"{BUTTON_NAME}\" button.",
        f"Result: {passed} / {len(results)} patients returned interaction data successfully.",
        "",
        format_summary_table(results),
        "",
    ]
    sections = [format_patient_section(result) for result in results]
    return "\n".join(header) + "\n\n" + "\n\n".join(sections) + "\n"


def write_raw_json(results: list[PatientResult], path: Path) -> None:
    """
    Takes every patient's result and the output path.
    Writes the raw response JSON for every patient to one file, for anyone who wants the unformatted data.
    Gives nothing; writes the file.
    """
    payload = [
        {
            "patient_number": result.patient_number,
            "medications": result.medications,
            "passed": result.passed,
            "status_code": result.status_code,
            "response_json": result.response_json,
            "error": result.error,
        }
        for result in results
    ]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    """
    Takes no arguments.
    Runs all 10 patients, writes the Markdown report and the raw JSON, and prints the report to stdout.
    Gives nothing; writes results/report.md and results/raw_responses.json, and prints to stdout.
    """
    results = run_all_patients()
    report_text = build_report(results)
    (RESULTS_DIR / "report.md").write_text(report_text, encoding="utf-8")
    write_raw_json(results, RESULTS_DIR / "raw_responses.json")
    print(report_text)


if __name__ == "__main__":
    main()
