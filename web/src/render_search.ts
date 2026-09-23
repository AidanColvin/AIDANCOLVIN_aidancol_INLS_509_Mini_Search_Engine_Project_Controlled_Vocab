/**
 * Takes no arguments.
 * Builds the "Have a question?" section: the search field, suggestions, vocabulary filter chips, and the results list, from state and callbacks only.
 * Gives nothing; the exported mount and update functions are called for the DOM nodes and side effects they produce.
 */

import {
  groupTermsByPropertyGroup,
  hitTitle,
  resolveTagNames,
  splitSnippetIntoSegments,
  splitTagsByActiveFilters,
  termsById,
} from "./search.js";
import { checkmarkIcon, externalLinkIcon, removeIcon, searchIcon } from "./render_icons.js";
import type { AppState, SearchHit, TermInfo } from "./records.js";

const SEARCH_RESULT_LIMIT = 20;

export interface SearchCallbacks {
  readonly onQueryChange: (query: string) => void;
  readonly onClearQuery: () => void;
  readonly onToggleFilter: (termId: string) => void;
  readonly onClearFilters: () => void;
  readonly onSetOperator: (operator: "AND" | "OR") => void;
  readonly onRetry: () => void;
}

export interface SearchViewRefs {
  readonly root: HTMLElement;
  readonly queryInput: HTMLInputElement;
  readonly clearButton: HTMLButtonElement;
  readonly filtersRow: HTMLElement;
  readonly resultsSection: HTMLElement;
}

// One-tap starting points, so nobody has to invent a query from nothing.
const SUGGESTED_QUERIES: readonly string[] = ["grapefruit", "drowsiness", "pregnancy", "alcohol", "kidney"];

/**
 * Takes the Label search view's callbacks.
 * Builds the section's static shell once: heading, lede, search field, suggestions, a filters row, and an empty results section.
 * Gives the SearchViewRefs, so the caller can update the dynamic parts and keep the search field's identity stable across renders.
 */
export function mountSearchView(callbacks: SearchCallbacks): SearchViewRefs {
  const root = document.createElement("section");
  root.className = "search-view";
  root.id = "look-up";
  root.setAttribute("aria-labelledby", "look-up-title");

  const title = document.createElement("h2");
  title.className = "section-title";
  title.id = "look-up-title";
  title.textContent = "Have a question?";

  const lede = document.createElement("p");
  lede.className = "section-lede";
  lede.textContent = "Search what the FDA prescribing information says about side effects, food, pregnancy, and more.";

  const fieldWrap = document.createElement("div");
  fieldWrap.setAttribute("role", "search");
  fieldWrap.className = "search-field narrow";
  const label = document.createElement("label");
  label.className = "visually-hidden";
  label.htmlFor = "search-q";
  label.textContent = "Search prescribing information";
  const iconSpan = document.createElement("span");
  iconSpan.className = "search-field__icon";
  iconSpan.append(searchIcon(20));
  const queryInput = document.createElement("input");
  queryInput.type = "search";
  queryInput.id = "search-q";
  queryInput.className = "search-field__input";
  queryInput.placeholder = "Search anything";
  queryInput.enterKeyHint = "search";
  const clearButton = document.createElement("button");
  clearButton.type = "button";
  clearButton.className = "btn btn--icon search-field__clear";
  clearButton.setAttribute("aria-label", "Clear search");
  clearButton.append(removeIcon(20));
  clearButton.hidden = true;
  fieldWrap.append(label, iconSpan, queryInput, clearButton);

  const suggestions = document.createElement("div");
  suggestions.className = "suggestions";
  const suggestionsLabel = document.createElement("span");
  suggestionsLabel.className = "suggestions__label";
  suggestionsLabel.textContent = "Try";
  suggestions.append(suggestionsLabel);
  for (const suggestion of SUGGESTED_QUERIES) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "btn btn--small";
    chip.textContent = suggestion;
    chip.addEventListener("click", () => {
      queryInput.value = suggestion;
      clearButton.hidden = false;
      callbacks.onQueryChange(suggestion);
    });
    suggestions.append(chip);
  }

  const filtersRow = document.createElement("div");
  filtersRow.className = "filters-row";
  filtersRow.setAttribute("role", "group");
  filtersRow.setAttribute("aria-label", "Narrow results");

  const resultsSection = document.createElement("div");
  resultsSection.className = "search-results";
  resultsSection.setAttribute("aria-live", "polite");

  root.append(title, lede, fieldWrap, suggestions, filtersRow, resultsSection);

  let debounceHandle: ReturnType<typeof setTimeout> | undefined;
  queryInput.addEventListener("input", () => {
    if (debounceHandle !== undefined) {
      clearTimeout(debounceHandle);
    }
    const value = queryInput.value;
    clearButton.hidden = value.length === 0;
    debounceHandle = setTimeout(() => {
      callbacks.onQueryChange(value);
    }, 250);
  });
  clearButton.addEventListener("click", () => {
    queryInput.value = "";
    clearButton.hidden = true;
    callbacks.onClearQuery();
  });

  return { root, queryInput, clearButton, filtersRow, resultsSection };
}

/**
 * Takes the view's refs, the current AppState, and the Label search callbacks.
 * Rebuilds the filter chips, shown only once a search has run, and the results section from the current state.
 * Gives nothing; the search field element itself is never replaced.
 */
export function updateSearchView(refs: SearchViewRefs, state: AppState, callbacks: SearchCallbacks): void {
  const groups = groupTermsByPropertyGroup(state.availableTerms);
  refs.filtersRow.replaceChildren(...buildFilterChips(groups, state, callbacks));
  const hasSearched = state.searchResponse !== null || state.searchFilters.length > 0;
  refs.filtersRow.hidden = groups.length === 0 || !hasSearched;
  refs.resultsSection.replaceChildren(...buildResultsBody(state, callbacks));
}

/**
 * Takes the grouped terms, the current AppState, and the Label search callbacks.
 * Builds one toggle chip per vocabulary term in group order, then the Match all/any toggle and a Clear link when filters are on.
 * Gives the tuple of elements for the filters row.
 */
function buildFilterChips(
  groups: ReturnType<typeof groupTermsByPropertyGroup>,
  state: AppState,
  callbacks: SearchCallbacks,
): readonly HTMLElement[] {
  const elements: HTMLElement[] = [];
  for (const group of groups) {
    for (const term of group.terms) {
      elements.push(buildFilterChip(term, group.propertyGroup, state.searchFilters.includes(term.term_id), callbacks));
    }
  }
  if (state.searchFilters.length >= 2) {
    elements.push(buildOperatorToggle(state.searchOperator, callbacks));
  }
  if (state.searchFilters.length > 0) {
    const clear = document.createElement("button");
    clear.type = "button";
    clear.className = "btn btn--small";
    clear.textContent = "Clear filters";
    clear.addEventListener("click", () => {
      callbacks.onClearFilters();
    });
    elements.push(clear);
  }
  return elements;
}

/**
 * Takes the current match operator and the Label search callbacks.
 * Builds the "Match all | Match any" segmented control.
 * Gives the control HTMLElement.
 */
function buildOperatorToggle(operator: "AND" | "OR", callbacks: SearchCallbacks): HTMLElement {
  const group = document.createElement("div");
  group.className = "operator-toggle";
  group.setAttribute("role", "group");
  group.setAttribute("aria-label", "Match mode");
  const matchAll = document.createElement("button");
  matchAll.type = "button";
  matchAll.className = operator === "AND" ? "btn btn--small btn--selected" : "btn btn--small";
  matchAll.setAttribute("aria-pressed", String(operator === "AND"));
  matchAll.textContent = "Match all";
  matchAll.addEventListener("click", () => callbacks.onSetOperator("AND"));
  const matchAny = document.createElement("button");
  matchAny.type = "button";
  matchAny.className = operator === "OR" ? "btn btn--small btn--selected" : "btn btn--small";
  matchAny.setAttribute("aria-pressed", String(operator === "OR"));
  matchAny.textContent = "Match any";
  matchAny.addEventListener("click", () => callbacks.onSetOperator("OR"));
  group.append(matchAll, matchAny);
  return group;
}

/**
 * Takes one term, the name of its property group, whether it is currently selected, and the Label search callbacks.
 * Builds the term's toggle chip, showing only its plain name, with its group and id kept for the tooltip.
 * Gives the chip button HTMLElement.
 */
function buildFilterChip(term: TermInfo, propertyGroup: string, selected: boolean, callbacks: SearchCallbacks): HTMLButtonElement {
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = selected ? "btn btn--small btn--selected" : "btn btn--small";
  chip.setAttribute("aria-pressed", String(selected));
  chip.title = `${propertyGroup} · ${term.term_id}`;
  if (selected) {
    chip.append(checkmarkIcon(14));
  }
  chip.append(document.createTextNode(term.name));
  chip.addEventListener("click", () => {
    callbacks.onToggleFilter(term.term_id);
  });
  return chip;
}

/**
 * Takes the current AppState and the Label search callbacks.
 * Builds the error card, the empty state, the result count heading, or the list of hit rows.
 * Gives the array of elements to append to the results section.
 */
function buildResultsBody(state: AppState, callbacks: SearchCallbacks): readonly HTMLElement[] {
  if (state.searchError !== null) {
    return [buildSearchErrorCard(state.searchError.message, state.searchError.detail, callbacks)];
  }
  if (state.searchResponse === null) {
    return [];
  }
  if (state.searchResponse.hits.length === 0) {
    const empty = document.createElement("p");
    empty.className = "search-results__empty";
    empty.textContent = "Nothing matched. Try a different word, or fewer filters.";
    return [empty];
  }
  const heading = document.createElement("h3");
  heading.className = "search-results__heading";
  heading.textContent = `${state.searchResponse.hits.length} results`;

  const list = document.createElement("ul");
  list.className = "search-results__list";
  const byId = termsById(state.availableTerms);
  for (const hit of state.searchResponse.hits) {
    list.append(buildHitRow(hit, state.searchQuery, state.searchFilters, byId));
  }

  const elements: HTMLElement[] = [heading, list];
  if (state.searchResponse.hits.length === SEARCH_RESULT_LIMIT) {
    const cap = document.createElement("p");
    cap.className = "search-results__cap-note";
    cap.textContent = "Showing the top 20";
    elements.push(cap);
  }
  return elements;
}

/**
 * Takes one search hit, the current query, the active filter ids, and the term id-to-info lookup.
 * Builds the hit's title, snippet, tag pills, and DailyMed link.
 * Gives the hit's list item element.
 */
function buildHitRow(hit: SearchHit, query: string, activeFilters: readonly string[], byId: ReturnType<typeof termsById>): HTMLElement {
  const article = document.createElement("li");
  article.className = "hit-row";

  const headRow = document.createElement("div");
  headRow.className = "hit-row__head";
  const title = hitTitle(hit);
  const titleGroup = document.createElement("div");
  titleGroup.className = "hit-row__title-group";
  const titleEl = document.createElement("h4");
  titleEl.className = "hit-row__title";
  titleEl.textContent = title.primary;
  titleGroup.append(titleEl);
  if (title.secondaryGeneric !== null) {
    const secondary = document.createElement("span");
    secondary.className = "hit-row__secondary";
    secondary.textContent = title.secondaryGeneric;
    titleGroup.append(secondary);
  }
  const link = document.createElement("a");
  link.href = safeDailymedUrl(dailymedUrlFor(hit.set_id));
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.className = "hit-row__dailymed";
  link.setAttribute("aria-label", `Open the ${title.primary} label on DailyMed (new tab)`);
  link.append(document.createTextNode("DailyMed"), externalLinkIcon(11));
  headRow.append(titleGroup, link);

  const snippet = document.createElement("p");
  snippet.className = "hit-row__snippet";
  for (const segment of splitSnippetIntoSegments(hit.snippet, query)) {
    if (segment.bold) {
      const strong = document.createElement("strong");
      strong.textContent = segment.text;
      snippet.append(strong);
    } else {
      snippet.append(document.createTextNode(segment.text));
    }
  }

  const tagsRow = document.createElement("div");
  tagsRow.className = "hit-row__tags";
  const resolved = resolveTagNames(hit.tags, byId);
  const { matching, rest } = splitTagsByActiveFilters(resolved, activeFilters);
  for (const tag of matching) {
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = tag.name;
    tagsRow.append(pill);
  }
  if (rest.length > 0) {
    const more = document.createElement("button");
    more.type = "button";
    more.className = "btn btn--small";
    more.setAttribute("aria-expanded", "false");
    more.textContent = `${rest.length} more ${rest.length === 1 ? "term" : "terms"}`;
    more.addEventListener("click", () => {
      more.remove();
      for (const tag of rest) {
        const pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = tag.name;
        tagsRow.append(pill);
      }
    });
    tagsRow.append(more);
  }

  article.append(headRow, snippet, tagsRow);
  return article;
}

const DAILYMED_URL_PREFIX = "https://dailymed.nlm.nih.gov/";

/**
 * Takes an SPL set id.
 * Builds the DailyMed label page URL, matching interactions/evidence.py's template.
 * Gives the URL string.
 */
function dailymedUrlFor(setId: string): string {
  return `${DAILYMED_URL_PREFIX}dailymed/drugInfo.cfm?setid=${encodeURIComponent(setId)}`;
}

/**
 * Takes a DailyMed URL built from a hit's set id.
 * Checks it starts with the DailyMed origin, per Section 5's safe-rendering rule.
 * Gives the URL unchanged when safe, or "#" when it is not.
 */
function safeDailymedUrl(url: string): string {
  return url.startsWith(DAILYMED_URL_PREFIX) ? url : "#";
}

/**
 * Takes the error's one-line message, the API's own error detail text, and the retry callback.
 * Builds the search view's error card, in the same shape as the Interactions view's.
 * Gives the card HTMLElement.
 */
function buildSearchErrorCard(message: string, detail: string, callbacks: SearchCallbacks): HTMLElement {
  const card = document.createElement("div");
  card.className = "error-card";
  card.setAttribute("role", "alert");
  const textCol = document.createElement("div");
  textCol.className = "error-card__text";
  const messageEl = document.createElement("p");
  messageEl.className = "error-card__message";
  messageEl.textContent = message;
  const detailEl = document.createElement("p");
  detailEl.className = "error-card__detail";
  detailEl.textContent = detail;
  textCol.append(messageEl, detailEl);
  const retry = document.createElement("button");
  retry.type = "button";
  retry.className = "btn btn--primary error-card__retry";
  retry.textContent = "Try again";
  retry.addEventListener("click", () => {
    callbacks.onRetry();
  });
  card.append(textCol, retry);
  return card;
}
