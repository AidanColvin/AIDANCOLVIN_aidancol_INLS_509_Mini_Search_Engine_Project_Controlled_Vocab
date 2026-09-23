/**
 * Takes no arguments.
 * Builds the app's state, mounts the one-page app, and wires every event to a state change and a re-render.
 * Gives nothing; this module runs once when the page loads.
 */

import { ApiHttpError, ApiShapeError, fetchCheck, fetchSearch, fetchTermsOnly, maxMedicationTextChars } from "./api.js";
import { formatBuildDate } from "./format.js";
import { isWithinLengthLimit, joinMedicationLines, replaceNameKeepingDose, resolvedNames, splitEnteredText } from "./meds.js";
import { renderHeader } from "./render_header.js";
import {
  mountInteractionsView,
  updateInteractionsView,
  type InteractionsCallbacks,
} from "./render_interactions.js";
import { createInitialState, withState, type AppState, type CheckErrorState, type CheckResponse, type LabelLookup, type SearchHit, type SearchResponse } from "./records.js";

const CHECK_DEBOUNCE_MS = 300;
const LOOKUP_LIMIT = 12;
const LOOKUP_LIST_NAMES_MAX = 8;
const USE_RXNORM = true;

let state: AppState = createInitialState();
let checkAbortController: AbortController | null = null;
let checkDebounceHandle: ReturnType<typeof setTimeout> | undefined;
const lookupAbortControllers = new Map<string, AbortController>();

/**
 * Takes an unknown thrown value.
 * Checks whether it is a DOMException named "AbortError", the signal an in-flight fetch was cancelled on purpose.
 * Gives true when it is, false otherwise.
 */
function isAbortError(err: unknown): boolean {
  return err instanceof DOMException && err.name === "AbortError";
}

/**
 * Takes an unknown error thrown while running a check or a search.
 * Picks a one-line message saying what happened and a second line saying what to do, distinguishing an unbuilt checker, a rejected request, an unreadable response, and a network failure.
 * Gives the CheckErrorState to show in the error card.
 */
function describeRequestError(err: unknown): CheckErrorState {
  if (err instanceof ApiHttpError) {
    if (err.status === 503) {
      return { message: "The checker isn't ready yet.", detail: "The label data is still loading on the server. Wait a moment, then try again." };
    }
    return { message: "The server could not take that request.", detail: `${err.apiMessage} Fix the entries, then try again.` };
  }
  if (err instanceof ApiShapeError || err instanceof SyntaxError) {
    return { message: "Could not read the server's reply.", detail: "Reload the page, then try again." };
  }
  if (err instanceof TypeError) {
    return { message: "Could not reach the server.", detail: "Check your connection, then try again." };
  }
  return { message: "Something went wrong.", detail: "Try again. If it keeps happening, reload the page." };
}

/**
 * Takes no arguments.
 * Cancels any pending debounce timer and any in-flight /api/check request.
 * Gives nothing.
 */
function cancelPendingCheck(): void {
  if (checkDebounceHandle !== undefined) {
    clearTimeout(checkDebounceHandle);
    checkDebounceHandle = undefined;
  }
  checkAbortController?.abort();
  checkAbortController = null;
}

/**
 * Takes the render callback to call after every state change this function causes.
 * Debounces a run of /api/check for the current medication list, marking the check as loading right away, applying the length limit, and updating state as it settles.
 * Gives nothing; state.checkResponse, state.checkLoading, and state.checkError are updated as the request proceeds.
 */
function scheduleCheck(render: () => void): void {
  cancelPendingCheck();
  if (state.medicationLines.length === 0) {
    state = withState(state, { checkResponse: null, checkLoading: false, checkError: null });
    render();
    return;
  }
  const joined = joinMedicationLines(state.medicationLines);
  if (!isWithinLengthLimit(joined)) {
    state = withState(state, {
      checkLoading: false,
      checkError: { message: "The list is too long to check.", detail: `The limit is ${maxMedicationTextChars()} characters. Remove some medications, then try again.` },
    });
    render();
    return;
  }
  state = withState(state, { checkLoading: true, checkError: null });
  checkDebounceHandle = setTimeout(() => {
    void runCheck(joined, render);
  }, CHECK_DEBOUNCE_MS);
}

/**
 * Takes the joined medication text to send and the render callback.
 * Runs POST /api/check, updating loading and result state as it settles.
 * Gives nothing.
 */
async function runCheck(joined: string, render: () => void): Promise<void> {
  const controller = new AbortController();
  checkAbortController = controller;
  state = withState(state, { checkLoading: true, checkError: null });
  render();
  try {
    const response = await fetchCheck(joined, USE_RXNORM, controller.signal);
    if (controller.signal.aborted) {
      return;
    }
    state = withState(state, { checkResponse: response, checkLoading: false, checkError: null, buildDate: response.build_date });
    render();
    startLookups(linesNeedingLookup(response), render);
  } catch (err: unknown) {
    if (isAbortError(err)) {
      return;
    }
    state = withState(state, { checkLoading: false, checkError: describeRequestError(err) });
    render();
  }
}

/**
 * Takes a check response.
 * Finds every entry the checker could not place as one medication, whether it offered candidates or not.
 * Gives their lines, the words worth looking up in the label text as well.
 */
function linesNeedingLookup(response: CheckResponse): readonly string[] {
  return response.unresolved_entries.map((entry) => entry.raw_text);
}

/**
 * Takes a line and its new lookup record.
 * Replaces that line's lookup in state, or adds it when the line has none yet.
 * Gives nothing; state.lookups is updated.
 */
function setLookup(line: string, lookup: LabelLookup): void {
  const others = state.lookups.filter((candidate) => candidate.line !== line);
  state = withState(state, { lookups: [...others, lookup] });
}

/**
 * Takes the lines that still need a label lookup and the render callback.
 * Starts one GET /api/search per line that has no lookup yet, drops lookups for lines no longer on the list, and cancels their requests.
 * Gives nothing; each lookup's state is updated as its request settles.
 */
function startLookups(lines: readonly string[], render: () => void): void {
  for (const [line, controller] of lookupAbortControllers) {
    if (!lines.includes(line)) {
      controller.abort();
      lookupAbortControllers.delete(line);
    }
  }
  state = withState(state, { lookups: state.lookups.filter((lookup) => lines.includes(lookup.line)) });
  for (const line of lines) {
    if (state.lookups.some((lookup) => lookup.line === line)) {
      continue;
    }
    void runLookup(line, render);
  }
  render();
}

/**
 * Takes a search hit and the lowercase names of the medications on the list.
 * Checks whether the hit's brand or generic name is one of those medications.
 * Gives true when the label belongs to a drug on the list.
 */
function hitIsOnList(hit: SearchHit, namesOnList: readonly string[]): boolean {
  const own = [hit.brand_name, hit.generic_name].map((value) => value.trim().toLowerCase());
  return own.some((candidate) => candidate.length > 0 && namesOnList.some((listed) => listed === candidate || candidate.startsWith(`${listed} `) || listed.startsWith(`${candidate} `)));
}

/**
 * Takes the general search response for a word, the response for that word plus the list's drug names, and the list's names.
 * Puts the list's own labels that mention the word first, then the general hits, without repeating a label.
 * Gives one merged SearchResponse.
 */
function mergeLookupResponses(general: SearchResponse, targeted: SearchResponse | null, namesOnList: readonly string[]): SearchResponse {
  const own = targeted === null ? [] : targeted.hits.filter((hit) => hitIsOnList(hit, namesOnList));
  const seen = new Set(own.map((hit) => hit.set_id));
  const rest = general.hits.filter((hit) => !seen.has(hit.set_id));
  return { ...general, hits: [...own, ...rest] };
}

/**
 * Takes one line to look up and the render callback.
 * Runs GET /api/search for that line's text and, when medications are on the list, a second search for the text with their names so their own labels come first, recording the loading, result, and error states as it settles.
 * Gives nothing.
 */
async function runLookup(line: string, render: () => void): Promise<void> {
  const controller = new AbortController();
  lookupAbortControllers.set(line, controller);
  setLookup(line, { line, response: null, loading: true, error: null });
  render();
  const namesOnList = resolvedNames(state.checkResponse).slice(0, LOOKUP_LIST_NAMES_MAX);
  try {
    const general = await fetchSearch({ q: line, terms: [], operator: "AND", limit: LOOKUP_LIMIT }, controller.signal);
    const targeted = namesOnList.length === 0
      ? null
      : await fetchSearch({ q: `${line} ${namesOnList.join(" ")}`, terms: [], operator: "AND", limit: LOOKUP_LIMIT }, controller.signal);
    if (controller.signal.aborted) {
      return;
    }
    setLookup(line, { line, response: mergeLookupResponses(general, targeted, namesOnList), loading: false, error: null });
    render();
  } catch (err: unknown) {
    if (isAbortError(err)) {
      return;
    }
    setLookup(line, { line, response: null, loading: false, error: describeRequestError(err) });
    render();
  }
}

interface FooterRefs {
  readonly root: HTMLElement;
  readonly dateLabel: HTMLElement;
}

/**
 * Takes no arguments.
 * Builds the shared footer: the build date and the GitHub source link.
 * Gives the FooterRefs, hidden until a build date is known.
 */
function buildFooter(): FooterRefs {
  const root = document.createElement("footer");
  root.className = "app-footer";
  root.hidden = true;
  const dateLabel = document.createElement("span");
  const link = document.createElement("a");
  link.href = "https://github.com/AidanColvin/AIDANCOLVIN_aidancol_INLS_509_Mini_Search_Engine_Project_Controlled_Vocab";
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Source on GitHub";
  root.append(dateLabel, link);
  return { root, dateLabel };
}

/**
 * Takes no arguments.
 * Checks whether keyboard focus is sitting nowhere useful: on the page body, or on nothing at all.
 * Gives true when focus can safely be moved to the medication field without taking it from something the user chose.
 */
function focusIsIdle(): boolean {
  const active = document.activeElement;
  return active === null || active === document.body || active === document.documentElement;
}

/**
 * Takes the medication input element.
 * Puts the cursor in it on load, whenever the tab or window comes back into view with focus idle, and whenever a printable key is typed while focus is idle.
 * Gives nothing; the listeners live for the life of the page.
 */
function keepMedicationFieldReady(input: HTMLInputElement): void {
  const focusIfIdle = (): void => {
    if (focusIsIdle()) {
      input.focus({ preventScroll: true });
    }
  };
  input.focus({ preventScroll: true });
  requestAnimationFrame(focusIfIdle);
  window.addEventListener("pageshow", focusIfIdle);
  window.addEventListener("focus", focusIfIdle);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      focusIfIdle();
    }
  });
  document.addEventListener("keydown", (domEvent) => {
    const printable = domEvent.key.length === 1 && !domEvent.metaKey && !domEvent.ctrlKey && !domEvent.altKey;
    if (printable && focusIsIdle()) {
      input.focus({ preventScroll: true });
    }
  });
}

/**
 * Takes no arguments.
 * Builds the app, mounts it, and wires every DOM event to a state update and a re-render.
 * Gives nothing.
 */
function main(): void {
  const appRoot = document.getElementById("app");
  if (appRoot === null) {
    throw new Error("missing #app root element");
  }
  const footer = buildFooter();
  const page = document.createElement("main");
  page.className = "page";

  const render = (): void => {
    updateInteractionsView(interactionsRefs, state, interactionsCallbacks);
    footer.root.hidden = state.buildDate === null;
    footer.dateLabel.textContent = state.buildDate === null ? "" : `FDA label data as of ${formatBuildDate(state.buildDate)}`;
  };
  const interactionsCallbacks: InteractionsCallbacks = {
    onAddMedication: (text) => {
      const newLines = splitEnteredText(text);
      if (newLines.length === 0) {
        return;
      }
      state = withState(state, { medicationLines: [...state.medicationLines, ...newLines] });
      scheduleCheck(render);
      render();
      interactionsRefs.medicationInput.focus();
    },
    onRemoveMedication: (line) => {
      const index = state.medicationLines.indexOf(line);
      if (index === -1) {
        return;
      }
      const newLines = [...state.medicationLines];
      newLines.splice(index, 1);
      state = withState(state, {
        medicationLines: newLines,
        expandedRows: state.expandedRows.filter((expandedLine) => expandedLine !== line),
      });
      scheduleCheck(render);
      render();
      interactionsRefs.medicationInput.focus();
    },
    onClearAll: () => {
      cancelPendingCheck();
      startLookups([], render);
      state = withState(state, {
        medicationLines: [],
        checkResponse: null,
        checkLoading: false,
        checkError: null,
        expandedRows: [],
        expandedAlerts: [],
      });
      render();
      interactionsRefs.medicationInput.focus();
    },
    onChooseCandidate: (line, candidate) => {
      const index = state.medicationLines.indexOf(line);
      if (index === -1) {
        return;
      }
      const newLines = [...state.medicationLines];
      newLines[index] = replaceNameKeepingDose(line, candidate);
      state = withState(state, { medicationLines: newLines });
      scheduleCheck(render);
      render();
      interactionsRefs.medicationInput.focus();
    },
    onEditUnresolved: (line) => {
      const index = state.medicationLines.indexOf(line);
      if (index === -1) {
        return;
      }
      const newLines = [...state.medicationLines];
      newLines.splice(index, 1);
      state = withState(state, { medicationLines: newLines });
      scheduleCheck(render);
      render();
      interactionsRefs.medicationInput.value = line;
      interactionsRefs.medicationInput.focus();
    },
    onToggleRowExpanded: (line) => {
      const expanded = state.expandedRows.includes(line);
      state = withState(state, {
        expandedRows: expanded ? state.expandedRows.filter((expandedLine) => expandedLine !== line) : [...state.expandedRows, line],
      });
      render();
    },
    onToggleAlertExpanded: (alertIndex) => {
      const expanded = state.expandedAlerts.includes(alertIndex);
      state = withState(state, {
        expandedAlerts: expanded ? state.expandedAlerts.filter((index) => index !== alertIndex) : [...state.expandedAlerts, alertIndex],
      });
      render();
    },
    onRetryCheck: () => {
      scheduleCheck(render);
      render();
    },
  };

  const interactionsRefs = mountInteractionsView(interactionsCallbacks);
  page.append(interactionsRefs.root);
  appRoot.append(renderHeader(), page, footer.root);

  render();
  keepMedicationFieldReady(interactionsRefs.medicationInput);

  void fetchTermsOnly().then((response) => {
    state = withState(state, {
      availableTerms: response.available_terms,
      buildDate: state.buildDate ?? response.build_date,
    });
    render();
  });
}

main();
