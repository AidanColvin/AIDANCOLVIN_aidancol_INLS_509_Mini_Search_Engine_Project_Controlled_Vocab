/**
 * Takes no arguments.
 * Builds the app's state, mounts the header and both sections on one page, and wires every event to a state change and a re-render.
 * Gives nothing; this module runs once when the page loads.
 */

import { ApiHttpError, ApiShapeError, fetchCheck, fetchSearch, fetchTermsOnly, maxMedicationTextChars } from "./api.js";
import { formatBuildDate } from "./format.js";
import { isWithinLengthLimit, joinMedicationLines, replaceNameKeepingDose, splitEnteredText } from "./meds.js";
import { renderHeader } from "./render_header.js";
import {
  mountInteractionsView,
  updateInteractionsView,
  type InteractionsCallbacks,
} from "./render_interactions.js";
import { mountSearchView, updateSearchView, type SearchCallbacks } from "./render_search.js";
import { createInitialState, withState, type AppState, type CheckErrorState } from "./records.js";

const CHECK_DEBOUNCE_MS = 300;
const SEARCH_LIMIT = 20;
const USE_RXNORM = true;

let state: AppState = createInitialState();
let checkAbortController: AbortController | null = null;
let checkDebounceHandle: ReturnType<typeof setTimeout> | undefined;
let searchAbortController: AbortController | null = null;

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
  } catch (err: unknown) {
    if (isAbortError(err)) {
      return;
    }
    state = withState(state, { checkLoading: false, checkError: describeRequestError(err) });
    render();
  }
}

/**
 * Takes the render callback.
 * Cancels any in-flight search request.
 * Gives nothing.
 */
function cancelPendingSearch(): void {
  searchAbortController?.abort();
  searchAbortController = null;
}

/**
 * Takes the render callback.
 * Runs GET /api/search for the current query, filters, and operator, or clears the results when there is nothing to search for.
 * Gives nothing.
 */
function runSearch(render: () => void): void {
  cancelPendingSearch();
  const trimmedQuery = state.searchQuery.trim();
  if (trimmedQuery.length === 0 && state.searchFilters.length === 0) {
    state = withState(state, { searchResponse: null, searchLoading: false, searchError: null });
    render();
    return;
  }
  const controller = new AbortController();
  searchAbortController = controller;
  state = withState(state, { searchLoading: true, searchError: null });
  render();
  void fetchSearch({ q: trimmedQuery, terms: state.searchFilters, operator: state.searchOperator, limit: SEARCH_LIMIT }, controller.signal)
    .then((response) => {
      if (controller.signal.aborted) {
        return;
      }
      state = withState(state, {
        searchResponse: response,
        searchLoading: false,
        searchError: null,
        buildDate: state.buildDate ?? response.build_date,
      });
      render();
    })
    .catch((err: unknown) => {
      if (isAbortError(err)) {
        return;
      }
      state = withState(state, { searchLoading: false, searchError: describeRequestError(err) });
      render();
    });
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
 * Builds the app, mounts both sections on one page, and wires every DOM event to a state update and a re-render.
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
    updateSearchView(searchRefs, state, searchCallbacks);
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

  const searchCallbacks: SearchCallbacks = {
    onQueryChange: (query) => {
      state = withState(state, { searchQuery: query });
      runSearch(render);
    },
    onClearQuery: () => {
      state = withState(state, { searchQuery: "" });
      runSearch(render);
      searchRefs.queryInput.focus();
    },
    onToggleFilter: (termId) => {
      const active = state.searchFilters.includes(termId);
      state = withState(state, {
        searchFilters: active ? state.searchFilters.filter((id) => id !== termId) : [...state.searchFilters, termId],
      });
      runSearch(render);
    },
    onClearFilters: () => {
      state = withState(state, { searchFilters: [] });
      runSearch(render);
    },
    onSetOperator: (operator) => {
      state = withState(state, { searchOperator: operator });
      runSearch(render);
    },
    onRetry: () => {
      runSearch(render);
    },
  };

  const interactionsRefs = mountInteractionsView(interactionsCallbacks);
  const searchRefs = mountSearchView(searchCallbacks);
  page.append(interactionsRefs.root, searchRefs.root);
  appRoot.append(renderHeader(), page, footer.root);

  render();
  keepMedicationFieldReady(interactionsRefs.medicationInput);
  if (location.hash === "#search") {
    searchRefs.root.scrollIntoView();
  }

  void fetchTermsOnly().then((response) => {
    state = withState(state, {
      availableTerms: response.available_terms,
      buildDate: state.buildDate ?? response.build_date,
    });
    render();
  });
}

main();
