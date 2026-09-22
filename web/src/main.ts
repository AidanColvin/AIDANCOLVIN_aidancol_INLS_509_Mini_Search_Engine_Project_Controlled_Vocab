/**
 * Takes no arguments.
 * Builds the app's state, mounts the header and both views, and wires every event to a state change and a re-render.
 * Gives nothing; this module runs once when the page loads.
 */

import { ApiHttpError, ApiShapeError, fetchCheck, fetchSearch, fetchTermsOnly, maxMedicationTextChars } from "./api.js";
import { formatBuildDate } from "./format.js";
import { isWithinLengthLimit, joinMedicationLines, splitPastedText } from "./meds.js";
import { renderHeader } from "./render_header.js";
import {
  mountInteractionsView,
  updateInteractionsView,
  type InteractionsCallbacks,
  type InteractionsViewRefs,
} from "./render_interactions.js";
import { mountSearchView, updateSearchView, type SearchCallbacks, type SearchViewRefs } from "./render_search.js";
import { createInitialState, withState, type AppState, type CheckErrorState, type ViewName } from "./records.js";

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
 * Picks a one-line message and a detail line, distinguishing an unbuilt checker, a rejected request, an unreadable response, and a network failure.
 * Gives the CheckErrorState to show in the error card.
 */
function describeRequestError(err: unknown): CheckErrorState {
  if (err instanceof ApiHttpError) {
    if (err.status === 503) {
      return { message: "Checker data isn't ready yet.", detail: err.apiMessage };
    }
    return { message: "The server rejected the request.", detail: err.apiMessage };
  }
  if (err instanceof ApiShapeError) {
    return { message: "Could not read the server's response.", detail: err.message };
  }
  if (err instanceof SyntaxError) {
    return { message: "Could not read the server's response.", detail: err.message };
  }
  if (err instanceof TypeError) {
    return { message: "Could not reach the server.", detail: err.message };
  }
  return { message: "Something went wrong.", detail: "An unknown error occurred." };
}

/**
 * Takes the app's DOM roots for the header, the Interactions view, and the Label search view.
 * Shows the view matching the current state and hides the other, and re-renders the header's active link.
 * Gives nothing.
 */
function renderShell(
  headerContainer: HTMLElement,
  interactionsRefs: InteractionsViewRefs,
  searchRefs: SearchViewRefs,
  onNavigate: (view: ViewName) => void,
): void {
  headerContainer.replaceChildren(renderHeader(state.view, { onNavigate }));
  interactionsRefs.root.hidden = state.view !== "interactions";
  searchRefs.root.hidden = state.view !== "search";
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
 * Debounces a run of /api/check for the current medication list, applying the length limit and updating state as it settles.
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
      checkError: { message: "The list is too long. Remove some medications and try again.", detail: `Limit is ${maxMedicationTextChars()} characters.` },
    });
    render();
    return;
  }
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
  link.textContent = "Open source on GitHub";
  root.append(dateLabel, link);
  return { root, dateLabel };
}

/**
 * Takes no arguments.
 * Builds the app, mounts every view, and wires every DOM event to a state update and a re-render.
 * Gives nothing.
 */
function main(): void {
  const appRoot = document.getElementById("app");
  if (appRoot === null) {
    throw new Error("missing #app root element");
  }
  const headerContainer = document.createElement("div");
  const footer = buildFooter();
  appRoot.append(headerContainer);

  const render = (): void => {
    renderShell(headerContainer, interactionsRefs, searchRefs, onNavigate);
    updateInteractionsView(interactionsRefs, state, interactionsCallbacks);
    updateSearchView(searchRefs, state, searchCallbacks);
    footer.root.hidden = state.buildDate === null;
    footer.dateLabel.textContent = state.buildDate === null ? "" : `FDA label data as of ${formatBuildDate(state.buildDate)}`;
  };

  const onNavigate = (view: ViewName): void => {
    if (state.view === view) {
      return;
    }
    location.hash = view === "search" ? "#search" : "#interactions";
  };

  const interactionsCallbacks: InteractionsCallbacks = {
    onAddMedication: (text) => {
      const newLines = splitPastedText(text);
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
      const chosenName = candidate.split("→")[0]?.trim() ?? candidate;
      const newLines = [...state.medicationLines];
      newLines[index] = chosenName;
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
  appRoot.append(interactionsRefs.root, searchRefs.root, footer.root);

  window.addEventListener("hashchange", () => {
    state = withState(state, { view: hashToView(location.hash) });
    render();
  });

  state = withState(state, { view: hashToView(location.hash) });
  render();
  interactionsRefs.medicationInput.focus();

  void fetchTermsOnly().then((response) => {
    state = withState(state, {
      availableTerms: response.available_terms,
      buildDate: state.buildDate ?? response.build_date,
    });
    render();
  });
}

/**
 * Takes the current location hash.
 * Maps "#search" to the search view and everything else to the interactions view.
 * Gives the ViewName.
 */
function hashToView(hash: string): ViewName {
  return hash === "#search" ? "search" : "interactions";
}

main();
