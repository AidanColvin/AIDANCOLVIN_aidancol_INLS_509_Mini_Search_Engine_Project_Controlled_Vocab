/**
 * Takes no arguments.
 * Builds the Interactions view: the medication field and list, and the results section, from state and callbacks only.
 * Gives nothing; the exported mount and update functions are called for the DOM nodes and side effects they produce.
 */

import {
  additionalEvidenceMembers,
  alertDisplayTierName,
  alertDrugNames,
  alertIconKey,
  primaryEvidenceMember,
  sortAlerts,
} from "./alerts.js";
import { formatDailyTotal, pluralizeCount, sectionDisplayName } from "./format.js";
import { candidateLabel, countResolvedRows, isSpellingCorrected, rowHeadlineName, statusForLine } from "./meds.js";
import { alertIcon, chevronDownIcon, chevronIcon, externalLinkIcon, plusIcon, removeIcon } from "./render_icons.js";
import type { AlertMember, AlertRecord, AppState, MedicationRow, UnresolvedEntry } from "./records.js";

export interface InteractionsCallbacks {
  readonly onAddMedication: (text: string) => void;
  readonly onRemoveMedication: (line: string) => void;
  readonly onClearAll: () => void;
  readonly onChooseCandidate: (line: string, candidateName: string) => void;
  readonly onEditUnresolved: (line: string) => void;
  readonly onToggleRowExpanded: (line: string) => void;
  readonly onToggleAlertExpanded: (alertIndex: number) => void;
  readonly onRetryCheck: () => void;
}

export interface InteractionsViewRefs {
  readonly root: HTMLElement;
  readonly medicationInput: HTMLInputElement;
  readonly hint: HTMLElement;
  readonly listHeader: HTMLElement;
  readonly listCountLabel: HTMLElement;
  readonly clearAllButton: HTMLButtonElement;
  readonly listSection: HTMLElement;
  readonly resultsSection: HTMLElement;
  readonly liveRegion: HTMLElement;
}

/**
 * Takes the Interactions view's callbacks.
 * Builds the view's static shell once: title, medication field, hint, list header, empty list and results containers.
 * Gives the InteractionsViewRefs, so the caller can update the dynamic parts and keep the medication field's identity stable across renders.
 */
export function mountInteractionsView(callbacks: InteractionsCallbacks): InteractionsViewRefs {
  const root = document.createElement("main");
  root.className = "interactions-view";

  const title = document.createElement("h1");
  title.className = "page-title";
  title.textContent = "Check drug to drug interactions";

  const fieldWrap = document.createElement("div");
  fieldWrap.className = "med-field";
  const label = document.createElement("label");
  label.className = "visually-hidden";
  label.htmlFor = "add-med";
  label.textContent = "Add a medication";
  const medicationInput = document.createElement("input");
  medicationInput.type = "text";
  medicationInput.id = "add-med";
  medicationInput.autocomplete = "off";
  medicationInput.className = "med-field__input";
  medicationInput.placeholder = "Add a medication";
  const addButton = document.createElement("button");
  addButton.type = "button";
  addButton.className = "med-field__add";
  addButton.setAttribute("aria-label", "Add medication");
  addButton.append(plusIcon(20));
  fieldWrap.append(label, medicationInput, addButton);

  const hint = document.createElement("p");
  hint.className = "med-hint";
  hint.textContent = "Press Return to add. Paste a list to add many at once.";

  const listHeader = document.createElement("div");
  listHeader.className = "list-header";
  const listCountLabel = document.createElement("span");
  listCountLabel.className = "list-header__count";
  const clearAllButton = document.createElement("button");
  clearAllButton.type = "button";
  clearAllButton.className = "list-header__clear";
  clearAllButton.textContent = "Clear all";
  listHeader.append(listCountLabel, clearAllButton);

  const listSection = document.createElement("section");
  listSection.className = "med-list";
  listSection.setAttribute("aria-label", "Medication list");

  const resultsSection = document.createElement("section");
  resultsSection.className = "results";
  resultsSection.setAttribute("aria-live", "polite");

  const liveRegion = document.createElement("div");
  liveRegion.className = "visually-hidden";
  liveRegion.setAttribute("aria-live", "polite");
  liveRegion.setAttribute("role", "status");

  root.append(title, fieldWrap, hint, listHeader, listSection, resultsSection, liveRegion);

  addButton.addEventListener("click", () => {
    submitInputValue(medicationInput, callbacks);
  });
  medicationInput.addEventListener("keydown", (domEvent) => {
    if (domEvent.key === "Enter") {
      domEvent.preventDefault();
      submitInputValue(medicationInput, callbacks);
    }
  });
  medicationInput.addEventListener("paste", (domEvent) => {
    const text = domEvent.clipboardData?.getData("text") ?? "";
    if (/[,;\n]/.test(text)) {
      domEvent.preventDefault();
      callbacks.onAddMedication(text);
      medicationInput.value = "";
    }
  });
  clearAllButton.addEventListener("click", () => {
    callbacks.onClearAll();
  });

  return { root, medicationInput, hint, listHeader, listCountLabel, clearAllButton, listSection, resultsSection, liveRegion };
}

/**
 * Takes the medication input element and the Interactions callbacks.
 * Reads the input's current text, submits it through onAddMedication when it is not blank, and clears the field.
 * Gives nothing.
 */
function submitInputValue(input: HTMLInputElement, callbacks: InteractionsCallbacks): void {
  const text = input.value.trim();
  if (text.length === 0) {
    return;
  }
  callbacks.onAddMedication(text);
  input.value = "";
}

/**
 * Takes the view's refs, the current AppState, and the Interactions callbacks.
 * Updates the field's placeholder, the hint's visibility, and rebuilds the list and results sections from the current state.
 * Gives nothing; the medication input element itself is never replaced.
 */
export function updateInteractionsView(refs: InteractionsViewRefs, state: AppState, callbacks: InteractionsCallbacks): void {
  const hasEntries = state.medicationLines.length > 0;
  refs.medicationInput.placeholder = hasEntries ? "Add another medication" : "Add a medication";
  refs.hint.hidden = hasEntries;
  refs.listCountLabel.textContent = pluralizeCount(state.medicationLines.length, "medication");
  refs.clearAllButton.hidden = !hasEntries;

  refs.listSection.replaceChildren(...buildMedicationRows(state, callbacks));
  refs.listSection.hidden = !hasEntries;
  refs.listHeader.hidden = !hasEntries;

  refs.resultsSection.replaceChildren();
  if (hasEntries) {
    refs.resultsSection.append(...buildResultsSection(state, callbacks));
  }

  const alertCount = state.checkResponse === null ? null : state.checkResponse.alerts.length;
  refs.liveRegion.textContent = alertCount === null ? "" : pluralizeCount(alertCount, "alert");
}

/**
 * Takes the current AppState and the Interactions callbacks.
 * Builds one row element per medication line, in list order.
 * Gives the array of row elements, empty when the list is empty.
 */
function buildMedicationRows(state: AppState, callbacks: InteractionsCallbacks): readonly HTMLElement[] {
  return state.medicationLines.map((line) => {
    const status = statusForLine(line, state.checkResponse);
    if ("row" in status) {
      return buildResolvedRow(line, status.row, state.expandedRows.includes(line), callbacks);
    }
    if ("unresolved" in status) {
      return buildUnresolvedRow(line, status.unresolved, callbacks);
    }
    return buildPendingRow(line, callbacks);
  });
}

/**
 * Takes one medication line and the remove callback.
 * Builds a minimal row shown while its check result has not arrived yet.
 * Gives the row HTMLElement.
 */
function buildPendingRow(line: string, callbacks: InteractionsCallbacks): HTMLElement {
  const row = document.createElement("div");
  row.className = "med-row med-row--pending";
  const name = document.createElement("span");
  name.className = "med-row__pending-text";
  name.textContent = line;
  row.append(name, buildRemoveButton(line, line, callbacks));
  return row;
}

/**
 * Takes one medication line, its resolved row, whether its detail is expanded, and the Interactions callbacks.
 * Builds the resolved row: a button showing the headline name, entered text, dose, DEA badge, and chevron, with the detail panel appended when expanded.
 * Gives the row HTMLElement.
 */
function buildResolvedRow(line: string, row: MedicationRow, expanded: boolean, callbacks: InteractionsCallbacks): HTMLElement {
  const wrap = document.createElement("div");
  wrap.className = "med-row";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "med-row__button";
  button.setAttribute("aria-expanded", String(expanded));

  const textCol = document.createElement("span");
  textCol.className = "med-row__text";
  const headline = document.createElement("span");
  headline.className = "med-row__headline";
  headline.textContent = rowHeadlineName(row);
  const secondaryLine = document.createElement("span");
  secondaryLine.className = "med-row__secondary";
  secondaryLine.append(document.createTextNode(row.as_entered));
  if (isSpellingCorrected(row)) {
    const tag = document.createElement("span");
    tag.className = "pill pill--muted";
    tag.textContent = "Spelling corrected";
    secondaryLine.append(tag);
  }
  textCol.append(headline, secondaryLine);

  const dose = document.createElement("span");
  dose.className = "med-row__dose";
  dose.textContent = formatDailyTotal(row.daily_total, row.daily_total_unit);

  const badge = document.createElement("span");
  badge.className = "med-row__badge";
  if (row.dea_schedule !== null) {
    const badgeText = document.createElement("span");
    badgeText.className = "dea-badge";
    badgeText.textContent = `C-${row.dea_schedule}`;
    badge.append(badgeText);
  }

  const chevron = document.createElement("span");
  chevron.className = "med-row__chevron";
  chevron.append(chevronIcon(16));

  button.append(textCol, dose, badge, chevron);
  button.addEventListener("click", () => {
    callbacks.onToggleRowExpanded(line);
  });

  const rowTop = document.createElement("div");
  rowTop.className = "med-row__top";
  rowTop.append(button, buildRemoveButton(line, row.as_entered, callbacks));

  wrap.append(rowTop);
  if (expanded) {
    wrap.append(buildRowDetail(row));
  }
  return wrap;
}

/**
 * Takes one resolved row.
 * Builds its expanded detail panel: FDA class, route, base ingredients, the matched chain, and label terms by name.
 * Gives the detail HTMLElement.
 */
function buildRowDetail(row: MedicationRow): HTMLElement {
  const detail = document.createElement("div");
  detail.className = "med-row__detail";
  const entries: ReadonlyArray<readonly [string, string]> = [
    ["FDA class", row.fda_class],
    ["Route", row.route.join(", ") || "—"],
    ["Base ingredients", row.base_ingredients.join(", ") || "—"],
    ["Matched", row.matched_name === null ? "—" : row.matched_name.join(" → ")],
    ["Label terms", row.pdla_tags.map((tag) => tag.name).join(", ") || "—"],
  ];
  for (const [label, value] of entries) {
    const line = document.createElement("div");
    line.className = "med-row__detail-line";
    const term = document.createElement("span");
    term.className = "med-row__detail-label";
    term.textContent = label;
    const definition = document.createElement("span");
    definition.textContent = value;
    line.append(term, definition);
    detail.append(line);
  }
  return detail;
}

/**
 * Takes one medication line, its unresolved entry, and the Interactions callbacks.
 * Builds the row for a "Which one?" candidate choice, or a "Not found" editable row when it has no candidates.
 * Gives the row HTMLElement.
 */
function buildUnresolvedRow(line: string, entry: UnresolvedEntry, callbacks: InteractionsCallbacks): HTMLElement {
  if (entry.candidates.length === 0) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "med-row med-row--not-found";
    const text = document.createElement("span");
    text.className = "med-row__not-found-text";
    text.textContent = `${line} — Not found. Tap to edit.`;
    row.append(text);
    row.addEventListener("click", () => {
      callbacks.onEditUnresolved(line);
    });
    return row;
  }

  const wrap = document.createElement("div");
  wrap.className = "med-row med-row--which-one";
  const top = document.createElement("div");
  top.className = "med-row__top";
  const textCol = document.createElement("span");
  textCol.className = "med-row__text";
  const headline = document.createElement("span");
  headline.className = "med-row__headline";
  headline.textContent = line;
  const which = document.createElement("span");
  which.className = "med-row__which-one";
  which.textContent = "Which one?";
  textCol.append(headline, which);
  top.append(textCol, buildRemoveButton(line, line, callbacks));

  const pills = document.createElement("div");
  pills.className = "candidate-pills";
  for (const candidate of entry.candidates) {
    const pill = document.createElement("button");
    pill.type = "button";
    pill.className = "candidate-pill";
    pill.textContent = candidateLabel(candidate);
    pill.addEventListener("click", () => {
      callbacks.onChooseCandidate(line, candidate);
    });
    pills.append(pill);
  }

  wrap.append(top, pills);
  return wrap;
}

/**
 * Takes the medication line to remove, its visible label for the button's name, and the Interactions callbacks.
 * Builds the remove ("x") button for one row.
 * Gives the button HTMLElement.
 */
function buildRemoveButton(line: string, visibleLabel: string, callbacks: InteractionsCallbacks): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "med-row__remove";
  button.setAttribute("aria-label", `Remove ${visibleLabel}`);
  button.append(removeIcon(18));
  button.addEventListener("click", () => {
    callbacks.onRemoveMedication(line);
  });
  return button;
}

/**
 * Takes the current AppState and the Interactions callbacks.
 * Builds the results heading, checked count, notice, error card, and alert cards.
 * Gives the array of elements to append to the results section, empty while a check is loading with no prior response.
 */
function buildResultsSection(state: AppState, callbacks: InteractionsCallbacks): readonly HTMLElement[] {
  if (state.checkError !== null) {
    return [buildErrorCard(state.checkError.message, state.checkError.detail, callbacks)];
  }
  if (state.checkResponse === null) {
    return [];
  }
  const elements: HTMLElement[] = [];
  const wrap = document.createElement("div");
  wrap.className = state.checkLoading ? "results__body results__body--loading" : "results__body";

  const headingRow = document.createElement("div");
  headingRow.className = "results__heading-row";
  const heading = document.createElement("h2");
  heading.className = "results__heading";
  heading.textContent = state.checkResponse.alerts.length === 0 ? state.checkResponse.no_warning_text : pluralizeCount(state.checkResponse.alerts.length, "alert");
  headingRow.append(heading);
  if (state.checkLoading) {
    const spinner = document.createElement("span");
    spinner.className = "spinner";
    spinner.setAttribute("aria-hidden", "true");
    headingRow.append(spinner);
  }

  const checkedCount = document.createElement("p");
  checkedCount.className = "results__checked-count";
  checkedCount.textContent = `${countResolvedRows(state.checkResponse.medication_table)} of ${state.medicationLines.length} medications checked`;

  const notice = document.createElement("p");
  notice.className = "results__notice";
  notice.textContent = state.checkResponse.notice;

  wrap.append(headingRow, checkedCount, notice);
  for (const alert of sortAlerts(state.checkResponse.alerts)) {
    const originalIndex = state.checkResponse.alerts.indexOf(alert);
    wrap.append(buildAlertCard(alert, originalIndex, state.expandedAlerts.includes(originalIndex), callbacks));
  }
  elements.push(wrap);
  return elements;
}

/**
 * Takes one alert, its index in the API's own order, whether its extra evidence is expanded, and the Interactions callbacks.
 * Builds the alert card: tier line, title, drug names, primary evidence quote, and the "Show N more" expansion.
 * Gives the article HTMLElement.
 */
function buildAlertCard(alert: AlertRecord, alertIndex: number, expanded: boolean, callbacks: InteractionsCallbacks): HTMLElement {
  const iconKey = alertIconKey(alert);
  const card = document.createElement("article");
  card.className = `alert-card alert-card--${iconKey}`;

  const tierLine = document.createElement("div");
  tierLine.className = "alert-card__tier-line";
  tierLine.append(alertIcon(iconKey, 14));
  const tierText = document.createElement("span");
  tierText.textContent = alertDisplayTierName(alert);
  tierLine.append(tierText);

  const title = document.createElement("h3");
  title.className = "alert-card__title";
  title.textContent = alert.title;

  const drugs = document.createElement("p");
  drugs.className = "alert-card__drugs";
  drugs.textContent = alertDrugNames(alert.members);

  card.append(tierLine, title, drugs);

  const primary = primaryEvidenceMember(alert.members);
  if (primary !== undefined) {
    const quote = document.createElement("blockquote");
    quote.className = "alert-card__quote";
    quote.textContent = primary.sentence;

    const meta = document.createElement("div");
    meta.className = "alert-card__meta";
    const metaText = document.createElement("span");
    metaText.textContent = `${primary.drug_name}, ${sectionDisplayName(primary.section)} section`;
    const link = document.createElement("a");
    link.href = safeDailymedUrl(primary.dailymed_url);
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.className = "alert-card__dailymed";
    link.setAttribute("aria-label", `Open the ${primary.drug_name} label on DailyMed (new tab)`);
    link.append(document.createTextNode("DailyMed"), externalLinkIcon(11));
    meta.append(metaText, link);
    card.append(quote, meta);

    const more = additionalEvidenceMembers(alert.members, primary);
    if (more.length > 0) {
      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "alert-card__more-toggle";
      toggle.setAttribute("aria-expanded", String(expanded));
      toggle.append(
        document.createTextNode(expanded ? "Show fewer label sentences" : `Show ${more.length} more label sentences`),
        chevronDownIcon(14),
      );
      toggle.addEventListener("click", () => {
        callbacks.onToggleAlertExpanded(alertIndex);
      });
      card.append(toggle);
      if (expanded) {
        for (const member of more) {
          card.append(buildAdditionalEvidenceBlock(member));
        }
      }
    }
  }

  return card;
}

/**
 * Takes one additional alert member with evidence.
 * Builds its quote and meta line in the same shape as the primary evidence.
 * Gives the wrapper HTMLElement.
 */
function buildAdditionalEvidenceBlock(member: AlertMember): HTMLElement {
  const wrap = document.createElement("div");
  wrap.className = "alert-card__additional";
  const quote = document.createElement("blockquote");
  quote.className = "alert-card__quote";
  quote.textContent = member.sentence;
  const meta = document.createElement("div");
  meta.className = "alert-card__meta";
  const metaText = document.createElement("span");
  metaText.textContent = `${member.drug_name}, ${sectionDisplayName(member.section)} section`;
  const link = document.createElement("a");
  link.href = safeDailymedUrl(member.dailymed_url);
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.className = "alert-card__dailymed";
  link.setAttribute("aria-label", `Open the ${member.drug_name} label on DailyMed (new tab)`);
  link.append(document.createTextNode("DailyMed"), externalLinkIcon(11));
  meta.append(metaText, link);
  wrap.append(quote, meta);
  return wrap;
}

const DAILYMED_URL_PREFIX = "https://dailymed.nlm.nih.gov/";

/**
 * Takes a DailyMed URL from the API.
 * Checks it starts with the DailyMed origin, per Section 5's safe-rendering rule.
 * Gives the URL unchanged when safe, or "#" when it is not, so a malformed link never navigates anywhere.
 */
function safeDailymedUrl(url: string): string {
  return url.startsWith(DAILYMED_URL_PREFIX) ? url : "#";
}

/**
 * Takes the error's one-line message, the API's own error detail text, and the retry callback.
 * Builds the error card Section 4.3 describes: message, detail, and a "Try again" button.
 * Gives the card HTMLElement.
 */
function buildErrorCard(message: string, detail: string, callbacks: InteractionsCallbacks): HTMLElement {
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
    callbacks.onRetryCheck();
  });
  card.append(textCol, retry);
  return card;
}
