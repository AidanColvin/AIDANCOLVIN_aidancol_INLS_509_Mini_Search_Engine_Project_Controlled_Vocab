"""Discovers the interaction-checker's backend call by driving the live page with Playwright.

Launches headless Chromium, attaches request and response listeners before
any interaction, submits patient #1's medication list through the real page
controls (found by accessible role and name, not guessed CSS selectors), and
logs every network exchange the submission triggers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, Request, Response, sync_playwright

SITE_URL = "https://rx-label-search-aidancolvins-projects.vercel.app/"
TEXTBOX_LABEL = "Medication list (comma, semicolon, or new-line separated)"
BUTTON_NAME = "Check interactions"
RESULTS_TIMEOUT_MS = 30_000
PATIENT_1_MEDICATIONS = (
    "Alprazolam 1 mg 3 times daily, Zolpidem 10 mg 1 time daily, Lisinopril 10 mg 1 time daily, "
    "Atorvastatin 20 mg 1 time daily, Sertraline 50 mg 1 time daily, Omeprazole 20 mg 1 time daily"
)


@dataclass
class NetworkLogEntry:
    """One captured request or response, in the order it was observed."""

    kind: str
    method: str | None
    url: str
    status: int | None
    payload: str | None
    body: str | None


@dataclass
class NetworkLog:
    """The full sequence of network entries captured during one page session."""

    entries: list[NetworkLogEntry] = field(default_factory=list)


def request_payload_text(request: Request) -> str | None:
    """
    Takes a Playwright request object.
    Reads its post body as text, when the request carries one.
    Gives the body text, or None when the request has no post data.
    """
    return request.post_data


def attach_listeners(page: Page, log: NetworkLog) -> None:
    """
    Takes the page to observe and the log to append to.
    Registers request and response handlers that record every network exchange.
    Gives nothing; the handlers append to the log as events occur.
    """

    def on_request(request: Request) -> None:
        """
        Takes a fired request.
        Records its method, URL, and payload.
        Gives nothing; appends one NetworkLogEntry.
        """
        log.entries.append(NetworkLogEntry("request", request.method, request.url, None, request_payload_text(request), None))

    def on_response(response: Response) -> None:
        """
        Takes a received response.
        Records its status and body text, when the body can be read as text.
        Gives nothing; appends one NetworkLogEntry.
        """
        body_text = read_response_body(response)
        log.entries.append(NetworkLogEntry("response", None, response.url, response.status, None, body_text))

    page.on("request", on_request)
    page.on("response", on_response)


def read_response_body(response: Response) -> str | None:
    """
    Takes a Playwright response object.
    Reads its body as text, guarding against bodies that cannot be read this way.
    Gives the body text, or None when the body cannot be read.
    """
    try:
        return response.text()
    except PlaywrightError:
        return None


def find_medication_textbox(page: Page):
    """
    Takes the page to search.
    Locates the medication-list textbox by its accessible label.
    Gives the Playwright locator for that textbox.
    """
    return page.get_by_role("textbox", name=TEXTBOX_LABEL)


def find_check_button(page: Page):
    """
    Takes the page to search.
    Locates the "Check interactions" button by its accessible role and name.
    Gives the Playwright locator for that button.
    """
    return page.get_by_role("button", name=BUTTON_NAME)


def submit_medications(page: Page, medications: str) -> None:
    """
    Takes the page and the medication-list text to submit.
    Fills the textbox, clicks the check button, and waits for the network to go idle.
    Gives nothing; raises Playwright's own TimeoutError if the controls are not found.
    """
    find_medication_textbox(page).fill(medications)
    find_check_button(page).click()
    page.wait_for_load_state("networkidle", timeout=RESULTS_TIMEOUT_MS)


def entry_to_json(entry: NetworkLogEntry) -> dict[str, str | int | None]:
    """
    Takes one network log entry.
    Converts it to a JSON-ready dictionary.
    Gives the dictionary.
    """
    return {"kind": entry.kind, "method": entry.method, "url": entry.url, "status": entry.status, "payload": entry.payload, "body": entry.body}


def run_discovery(output_path: Path) -> NetworkLog:
    """
    Takes the path to write the discovery log to.
    Launches headless Chromium, submits patient #1's list, and captures every network exchange.
    Gives the completed NetworkLog; also writes it to output_path as JSON.
    """
    log = NetworkLog()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        attach_listeners(page, log)
        page.goto(SITE_URL, wait_until="networkidle")
        submit_medications(page, PATIENT_1_MEDICATIONS)
        page.screenshot(path=str(output_path.parent / "results" / "patient_01.png"), full_page=True)
        browser.close()
    output_path.write_text(json.dumps([entry_to_json(entry) for entry in log.entries], indent=2), encoding="utf-8")
    return log


def main() -> None:
    """
    Takes no arguments.
    Runs discovery and prints a summary of every XHR/fetch exchange found.
    Gives nothing; prints to stdout.
    """
    base = Path(__file__).resolve().parent
    log = run_discovery(base / "results" / "discovery_log.json")
    for entry in log.entries:
        if entry.kind == "request" and entry.method in ("POST", "PUT", "PATCH"):
            print(f"REQUEST {entry.method} {entry.url}")
            print(f"  payload: {entry.payload}")
        if entry.kind == "response" and "/api/" in entry.url:
            print(f"RESPONSE {entry.status} {entry.url}")
            print(f"  body: {(entry.body or '')[:500]}")


if __name__ == "__main__":
    main()
