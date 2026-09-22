/**
 * Takes no arguments.
 * Builds the Label search view: the search field, the vocabulary filters, and the results list, from state and callbacks only.
 * Gives nothing; the exported mount and update functions are called for the DOM nodes and side effects they produce.
 */

import {
  groupTermsByPropertyGroup,
  hitTitle,
  resolveTagNames,
  splitSnippetIntoSegments,
  splitTagsByActiveFilters,
  termIndentLevel,
  termsById,
} from "./search.js";
import { checkmarkIcon, externalLinkIcon, searchIcon } from "./render_icons.js";
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
  readonly filtersMobileButton: HTMLButtonElement;
  readonly filtersDialog: HTMLDialogElement;
  readonly filtersSidebar: HTMLElement;
  readonly resultsSection: HTMLElement;
}

/**
 * Takes the Label search view's callbacks.
 * Builds the view's static shell once: title, search field, filters containers, and an empty results section.
 * Gives the SearchViewRefs, so the caller can update the dynamic parts and keep the search field's identity stable across renders.
 */
export function mountSearchView(callbacks: SearchCallbacks): SearchViewRefs {
  const root = document.createElement("main");
  root.className = "search-view";

  const title = document.createElement("h1");
  title.className = "page-title";
  title.textContent = "Search labels";

  const fieldWrap = document.createElement("div");
  fieldWrap.setAttribute("role", "search");
  fieldWrap.className = "search-field";
  const label = document.createElement("label");
  label.className = "visually-hidden";
  label.htmlFor = "search-q";
  label.textContent = "Search label text";
  const iconSpan = document.createElement("span");
  iconSpan.className = "search-field__icon";
  iconSpan.append(searchIcon(20));
  const queryInput = document.createElement("input");
  queryInput.type = "search";
  queryInput.id = "search-q";
  queryInput.className = "search-field__input";
  queryInput.placeholder = "Search label text";
  const clearButton = document.createElement("button");
  clearButton.type = "button";
  clearButton.className = "search-field__clear";
  clearButton.setAttribute("aria-label", "Clear search");
  clearButton.textContent = "×";
  fieldWrap.append(label, iconSpan, queryInput, clearButton);

  const filtersMobileButton = document.createElement("button");
  filtersMobileButton.type = "button";
  filtersMobileButton.className = "filters-mobile-button";
  filtersMobileButton.textContent = "Filters";

  const filtersDialog = document.createElement("dialog");
  filtersDialog.className = "filters-dialog";

  const filtersSidebar = document.createElement("aside");
  filtersSidebar.className = "filters-sidebar";
  filtersSidebar.setAttribute("aria-label", "Filters");

  const body = document.createElement("div");
  body.className = "search-view__body";
  body.append(filtersSidebar);

  const resultsSection = document.createElement("section");
  resultsSection.className = "search-results";
  resultsSection.setAttribute("aria-live", "polite");
  body.append(resultsSection);

  root.append(title, fieldWrap, filtersMobileButton, filtersDialog, body);

  let debounceHandle: ReturnType<typeof setTimeout> | undefined;
  queryInput.addEventListener("input", () => {
    if (debounceHandle !== undefined) {
      clearTimeout(debounceHandle);
    }
    const value = queryInput.value;
    debounceHandle = setTimeout(() => {
      callbacks.onQueryChange(value);
    }, 250);
  });
  clearButton.addEventListener("click", () => {
    queryInput.value = "";
    callbacks.onClearQuery();
  });
  filtersMobileButton.addEventListener("click", () => {
    filtersDialog.showModal();
  });

  return { root, queryInput, clearButton, filtersMobileButton, filtersDialog, filtersSidebar, resultsSection };
}

/**
 * Takes the view's refs, the current AppState, and the Label search callbacks.
 * Rebuilds the filters sidebar, the filters dialog's content, and the results section from the current state.
 * Gives nothing; the search field element itself is never replaced.
 */
export function updateSearchView(refs: SearchViewRefs, state: AppState, callbacks: SearchCallbacks): void {
  const groups = groupTermsByPropertyGroup(state.availableTerms);
  refs.filtersSidebar.replaceChildren(buildFilterPanel(groups, state, callbacks, false));
  refs.filtersDialog.replaceChildren(buildFilterPanel(groups, state, callbacks, true));
  refs.resultsSection.replaceChildren(...buildResultsBody(state, callbacks));
}

/**
 * Takes the grouped terms, the current AppState, the Label search callbacks, and whether this panel is the mobile dialog copy.
 * Builds the filters heading, the Match all/any toggle, and one row group per property group.
 * Gives the panel's root HTMLElement.
 */
function buildFilterPanel(
  groups: ReturnType<typeof groupTermsByPropertyGroup>,
  state: AppState,
  callbacks: SearchCallbacks,
  isDialogCopy: boolean,
): HTMLElement {
  const panel = document.createElement("div");
  panel.className = "filters-panel";

  const headingRow = document.createElement("div");
  headingRow.className = "filters-panel__heading-row";
  const heading = document.createElement("h2");
  heading.className = "filters-panel__heading";
  heading.textContent = "Filters";
  headingRow.append(heading);
  if (state.searchFilters.length > 0) {
    const clear = document.createElement("button");
    clear.type = "button";
    clear.className = "filters-panel__clear";
    clear.textContent = "Clear";
    clear.addEventListener("click", () => {
      callbacks.onClearFilters();
    });
    headingRow.append(clear);
  }
  panel.append(headingRow);

  if (isDialogCopy) {
    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.className = "filters-panel__close";
    closeButton.textContent = "Done";
    closeButton.addEventListener("click", () => {
      closeButton.closest("dialog")?.close();
    });
    panel.append(closeButton);
  }

  if (state.searchFilters.length >= 2) {
    panel.append(buildOperatorToggle(state.searchOperator, callbacks));
  }

  for (const group of groups) {
    panel.append(buildFilterGroup(group.propertyGroup, group.terms, state.searchFilters, callbacks));
  }

  return panel;
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
  matchAll.className = operator === "AND" ? "operator-toggle__option operator-toggle__option--active" : "operator-toggle__option";
  matchAll.setAttribute("aria-pressed", String(operator === "AND"));
  matchAll.textContent = "Match all";
  matchAll.addEventListener("click", () => callbacks.onSetOperator("AND"));
  const matchAny = document.createElement("button");
  matchAny.type = "button";
  matchAny.className = operator === "OR" ? "operator-toggle__option operator-toggle__option--active" : "operator-toggle__option";
  matchAny.setAttribute("aria-pressed", String(operator === "OR"));
  matchAny.textContent = "Match any";
  matchAny.addEventListener("click", () => callbacks.onSetOperator("OR"));
  group.append(matchAll, matchAny);
  return group;
}

/**
 * Takes one property group's name and terms, the currently selected filter ids, and the Label search callbacks.
 * Builds the group's heading and its list of filter row buttons.
 * Gives the group wrapper HTMLElement.
 */
function buildFilterGroup(propertyGroup: string, terms: readonly TermInfo[], selected: readonly string[], callbacks: SearchCallbacks): HTMLElement {
  const wrap = document.createElement("div");
  wrap.className = "filter-group";
  const heading = document.createElement("h3");
  heading.className = "filter-group__heading";
  heading.textContent = propertyGroup;
  const list = document.createElement("div");
  list.className = "filter-group__list";
  for (const term of terms) {
    list.append(buildFilterRow(term, selected.includes(term.term_id), callbacks));
  }
  wrap.append(heading, list);
  return wrap;
}

/**
 * Takes one term, whether it is currently selected, and the Label search callbacks.
 * Builds the term's filter row button, indented when it narrows a broader term.
 * Gives the row button HTMLElement.
 */
function buildFilterRow(term: TermInfo, selected: boolean, callbacks: SearchCallbacks): HTMLButtonElement {
  const row = document.createElement("button");
  row.type = "button";
  const indentClass = termIndentLevel(term.term_id) === 1 ? " filter-row--indented" : "";
  row.className = selected ? `filter-row filter-row--selected${indentClass}` : `filter-row${indentClass}`;
  row.setAttribute("aria-pressed", String(selected));
  const name = document.createElement("span");
  name.textContent = term.name;
  const id = document.createElement("span");
  id.className = "filter-row__id";
  id.textContent = term.term_id;
  row.append(name, id);
  if (selected) {
    const check = document.createElement("span");
    check.className = "filter-row__check";
    check.append(checkmarkIcon(16));
    row.append(check);
  }
  row.addEventListener("click", () => {
    callbacks.onToggleFilter(term.term_id);
  });
  return row;
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
    empty.textContent = "No labels match. Try fewer filters or Match any.";
    return [empty];
  }
  const heading = document.createElement("h2");
  heading.className = "search-results__heading";
  heading.textContent = `${state.searchResponse.hits.length} results`;

  const list = document.createElement("div");
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
 * Gives the hit's article HTMLElement.
 */
function buildHitRow(hit: SearchHit, query: string, activeFilters: readonly string[], byId: ReturnType<typeof termsById>): HTMLElement {
  const article = document.createElement("article");
  article.className = "hit-row";

  const headRow = document.createElement("div");
  headRow.className = "hit-row__head";
  const title = hitTitle(hit);
  const titleGroup = document.createElement("div");
  titleGroup.className = "hit-row__title-group";
  const titleEl = document.createElement("h3");
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
    pill.className = "pill pill--accent";
    pill.textContent = tag.name;
    tagsRow.append(pill);
  }
  if (rest.length > 0) {
    const more = document.createElement("button");
    more.type = "button";
    more.className = "hit-row__more-tags";
    more.setAttribute("aria-expanded", "false");
    more.textContent = `+${rest.length} more`;
    more.addEventListener("click", () => {
      more.remove();
      for (const tag of rest) {
        const pill = document.createElement("span");
        pill.className = "pill pill--accent";
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
  retry.className = "error-card__retry";
  retry.textContent = "Try again";
  retry.addEventListener("click", () => {
    callbacks.onRetry();
  });
  card.append(textCol, retry);
  return card;
}
