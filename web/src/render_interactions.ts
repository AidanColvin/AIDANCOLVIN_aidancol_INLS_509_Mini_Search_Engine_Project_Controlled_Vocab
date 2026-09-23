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
import { candidateChoices, countResolvedRows, isSpellingCorrected, resolvedNames, rowHeadlineName, statusForLine, usefulChoices } from "./meds.js";
import { alertIcon, chevronDownIcon, chevronIcon, externalLinkIcon, plusIcon, removeIcon } from "./render_icons.js";
import { buildLookupBlock } from "./render_lookup.js";
import type { AlertMember, AlertRecord, AppState, LabelLookup, MedicationRow, PdlaTag, UnresolvedEntry } from "./records.js";

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
  readonly addButton: HTMLButtonElement;
  readonly checkStatus: HTMLElement;
  readonly listHeader: HTMLElement;
  readonly listCountLabel: HTMLElement;
  readonly clearAllButton: HTMLButtonElement;
  readonly listSection: HTMLElement;
  readonly resultsSection: HTMLElement;
  readonly liveRegion: HTMLElement;
}

const PLACEHOLDER_FIRST = "warfarin 5 mg daily";
const PLACEHOLDER_NEXT = "Add another medication";
const CHECKING_TEXT = "Checking…";

/**
 * Takes the Interactions view's callbacks.
 * Builds the view's static shell once: greeting, lede, the medication form with its status line, list header, empty list and results containers.
 * Gives the InteractionsViewRefs, so the caller can update the dynamic parts and keep the medication field's identity stable across renders.
 */
export function mountInteractionsView(callbacks: InteractionsCallbacks): InteractionsViewRefs {
  const root = document.createElement("section");
  root.className = "interactions-view";
  root.setAttribute("aria-labelledby", "hello-title");

  const title = document.createElement("h1");
  title.className = "hello";
  title.id = "hello-title";
  title.textContent = "Hello.";

  const lede = document.createElement("p");
  lede.className = "hello-lede";
  lede.textContent = "Type the medications, brand or generic, and I'll check their FDA labels for interactions.";

  const form = document.createElement("form");
  form.className = "med-form narrow";
  form.setAttribute("aria-label", "Medications to check");
  form.noValidate = true;
  const fieldWrap = document.createElement("div");
  fieldWrap.className = "med-field";
  const label = document.createElement("label");
  label.className = "visually-hidden";
  label.htmlFor = "add-med";
  label.textContent = "Medication, with dose if you know it";
  const medicationInput = document.createElement("input");
  medicationInput.type = "text";
  medicationInput.id = "add-med";
  medicationInput.autocomplete = "off";
  medicationInput.autofocus = true;
  medicationInput.spellcheck = false;
  medicationInput.enterKeyHint = "done";
  medicationInput.className = "med-field__input";
  medicationInput.placeholder = PLACEHOLDER_FIRST;
  const addButton = document.createElement("button");
  addButton.type = "submit";
  addButton.className = "med-field__add";
  addButton.setAttribute("aria-label", "Add medication");
  addButton.append(plusIcon(20));
  fieldWrap.append(label, medicationInput, addButton);

  const checkStatus = document.createElement("p");
  checkStatus.className = "med-status";
  checkStatus.setAttribute("role", "status");

  const hint = document.createElement("p");
  hint.className = "med-hint";
  hint.textContent = "Misspellings are fine. A word like grapefruit gets looked up in the labels instead.";

  form.append(fieldWrap, checkStatus, hint);

  const listHeader = document.createElement("div");
  listHeader.className = "list-header narrow";
  const listCountLabel = document.createElement("span");
  listCountLabel.className = "caption";
  const clearAllButton = document.createElement("button");
  clearAllButton.type = "button";
  clearAllButton.className = "btn btn--small";
  clearAllButton.textContent = "Clear all";
  listHeader.append(listCountLabel, clearAllButton);

  const listSection = document.createElement("ul");
  listSection.className = "med-list narrow";
  listSection.setAttribute("aria-label", "Medications to check");

  const resultsSection = document.createElement("section");
  resultsSection.className = "results";
  resultsSection.setAttribute("aria-label", "Results");
  resultsSection.setAttribute("aria-live", "polite");

  const liveRegion = document.createElement("div");
  liveRegion.className = "visually-hidden";
  liveRegion.setAttribute("aria-live", "polite");
  liveRegion.setAttribute("role", "status");

  root.append(title, lede, form, listHeader, listSection, resultsSection, liveRegion);

  form.addEventListener("submit", (domEvent) => {
    domEvent.preventDefault();
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

  return { root, medicationInput, addButton, checkStatus, listHeader, listCountLabel, clearAllButton, listSection, resultsSection, liveRegion };
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
 * Updates the field's placeholder, the status line, the add button's disabled state, and rebuilds the list and results sections from the current state.
 * Gives nothing; the medication input element itself is never replaced.
 */
export function updateInteractionsView(refs: InteractionsViewRefs, state: AppState, callbacks: InteractionsCallbacks): void {
  const hasEntries = state.medicationLines.length > 0;
  refs.medicationInput.placeholder = hasEntries ? PLACEHOLDER_NEXT : PLACEHOLDER_FIRST;
  refs.addButton.disabled = state.checkLoading;
  refs.checkStatus.textContent = state.checkLoading ? CHECKING_TEXT : "";
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
 * Builds one list item per medication line, in list order.
 * Gives the array of row elements, empty when the list is empty.
 */
function buildMedicationRows(state: AppState, callbacks: InteractionsCallbacks): readonly HTMLElement[] {
  return state.medicationLines.map((line) => {
    const status = statusForLine(line, state.checkResponse);
    if ("row" in status) {
      return buildResolvedRow(line, status.row, state.expandedRows.includes(line), callbacks);
    }
    if ("unresolved" in status) {
      const lookup = state.lookups.find((candidate) => candidate.line === line);
      return buildUnresolvedRow(line, status.unresolved, lookup, resolvedNames(state.checkResponse), callbacks);
    }
    return buildPendingRow(line, state.checkError === null, callbacks);
  });
}

/**
 * Takes one medication line, whether a check is still expected for it, and the Interactions callbacks.
 * Builds the row shown while its check result has not arrived, dimmed only while a result is still on its way rather than after a failed check.
 * Gives the list item element.
 */
function buildPendingRow(line: string, awaitingResult: boolean, callbacks: InteractionsCallbacks): HTMLElement {
  const row = document.createElement("li");
  row.className = awaitingResult ? "med-row med-row--static med-row--pending" : "med-row med-row--static";
  const textCol = document.createElement("span");
  textCol.className = "med-row__text";
  const headline = document.createElement("span");
  headline.className = "med-row__headline";
  headline.textContent = line;
  textCol.append(headline);
  row.append(textCol, buildRemoveButton(line, line, callbacks));
  return row;
}

/**
 * Takes one medication line, its resolved row, whether its detail is expanded, and the Interactions callbacks.
 * Builds the resolved row: a button showing the headline name, entered text, dose, DEA badge, and chevron, a remove button, and the detail panel when expanded.
 * Gives the list item element.
 */
function buildResolvedRow(line: string, row: MedicationRow, expanded: boolean, callbacks: InteractionsCallbacks): HTMLElement {
  const wrap = document.createElement("li");
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
    tag.className = "pill";
    tag.textContent = "Spelling corrected";
    secondaryLine.append(tag);
  }
  textCol.append(headline, secondaryLine);
  const tags = labelTags(row.pdla_tags);
  if (tags.length > 0) {
    const tagsRow = document.createElement("span");
    tagsRow.className = "med-row__tags";
    for (const tag of tags) {
      const pill = document.createElement("span");
      pill.className = "pill";
      pill.textContent = tag.name;
      tagsRow.append(pill);
    }
    textCol.append(tagsRow);
  }

  const dose = document.createElement("span");
  dose.className = "med-row__dose";
  dose.textContent = formatDailyTotal(row.daily_total, row.daily_total_unit);

  button.append(textCol, dose);
  if (row.dea_schedule !== null) {
    const badge = document.createElement("span");
    badge.className = "dea-badge";
    badge.textContent = `C-${row.dea_schedule}`;
    badge.setAttribute("aria-label", `DEA schedule ${row.dea_schedule}`);
    button.append(badge);
  }
  const chevron = document.createElement("span");
  chevron.className = "med-row__chevron";
  chevron.append(chevronIcon(16));
  button.append(chevron);
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

// Label terms worth showing on a medication row. Route, product form, the
// patient-guide flag, and the DEA terms (the C-II badge already covers those)
// are noise next to a drug name; the safety, dosing, and interaction terms are not.
const ROW_TAG_TERM_IDS: ReadonlySet<string> = new Set(["T01", "T03", "T04", "T06", "T11", "T12", "T14", "T15", "T16", "T17"]);

/**
 * Takes a resolved row's PDLA tags.
 * Keeps the safety, dosing, and interaction-risk terms and drops route, form, guide, and DEA terms.
 * Gives the tags to show on the row, in the API's order.
 */
function labelTags(tags: readonly PdlaTag[]): readonly PdlaTag[] {
  return tags.filter((tag) => ROW_TAG_TERM_IDS.has(tag.term_id));
}

/**
 * Takes one unresolved entry and whether it has any choice worth offering.
 * Writes the plain-English line that says what happened and what to do next for it.
 * Gives "More than one label matches. Choose one:" for a real ambiguity, the "Did you mean" line when there are other names to try, or "Not a medication name we know." when the label lookup below says the rest.
 */
function unresolvedExplanation(entry: UnresolvedEntry, hasChoices: boolean): string {
  if (!hasChoices) {
    return "Not a medication name we know.";
  }
  return entry.status === "needs_confirmation" ? "More than one label matches. Choose one:" : "Not found in the FDA labels. Did you mean:";
}

/**
 * Takes one medication line, its unresolved entry, its label lookup when one has started, the names on the list, and the Interactions callbacks.
 * Builds the row that says the entry was not checked and why, with candidate buttons when any would help, the label lookup block once it has started, plus Edit and remove buttons.
 * Gives the list item element.
 */
function buildUnresolvedRow(
  line: string,
  entry: UnresolvedEntry,
  lookup: LabelLookup | undefined,
  namesOnList: readonly string[],
  callbacks: InteractionsCallbacks,
): HTMLElement {
  const wrap = document.createElement("li");
  wrap.className = "med-row";

  const top = document.createElement("div");
  top.className = "med-row--static";
  const textCol = document.createElement("span");
  textCol.className = "med-row__text";
  const headline = document.createElement("span");
  headline.className = "med-row__headline";
  headline.textContent = line;
  const choices = usefulChoices(line, candidateChoices(entry.candidates));
  const explanation = document.createElement("span");
  explanation.className = "med-row__secondary";
  explanation.textContent = unresolvedExplanation(entry, choices.length > 0);
  textCol.append(headline, explanation);

  const actions = document.createElement("span");
  actions.className = "med-row__actions";
  const edit = document.createElement("button");
  edit.type = "button";
  edit.className = "btn btn--small";
  edit.textContent = "Edit";
  edit.setAttribute("aria-label", `Edit ${line}`);
  edit.addEventListener("click", () => {
    callbacks.onEditUnresolved(line);
  });
  actions.append(edit, buildRemoveButton(line, line, callbacks));
  top.append(textCol, actions);
  wrap.append(top);

  if (choices.length > 0) {
    const pills = document.createElement("div");
    pills.className = "candidate-pills";
    for (const choice of choices) {
      const pill = document.createElement("button");
      pill.type = "button";
      pill.className = "btn btn--small";
      pill.textContent = choice.label;
      pill.addEventListener("click", () => {
        callbacks.onChooseCandidate(line, choice.entryText);
      });
      pills.append(pill);
    }
    wrap.append(pills);
  }
  if (lookup !== undefined) {
    wrap.append(buildLookupBlock(lookup, namesOnList));
  }
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
  button.className = "btn btn--icon";
  button.setAttribute("aria-label", `Remove ${visibleLabel}`);
  button.append(removeIcon(20));
  button.addEventListener("click", () => {
    callbacks.onRemoveMedication(line);
  });
  return button;
}

/**
 * Takes the current AppState and the Interactions callbacks.
 * Builds the results: the error card, or the heading, checked count, the entries that were not checked, the notice, and the alert cards.
 * Gives the array of elements to append to the results section, empty while a first check is still loading.
 */
function buildResultsSection(state: AppState, callbacks: InteractionsCallbacks): readonly HTMLElement[] {
  if (state.checkError !== null) {
    return [buildErrorCard(state.checkError.message, state.checkError.detail, callbacks)];
  }
  if (state.checkResponse === null) {
    return [];
  }
  const wrap = document.createElement("div");
  wrap.className = state.checkLoading ? "results__body results__body--loading" : "results__body";

  const heading = document.createElement("h2");
  heading.className = "results__heading";
  heading.textContent = state.checkResponse.alerts.length === 0 ? state.checkResponse.no_warning_text : pluralizeCount(state.checkResponse.alerts.length, "alert");

  const checkedCount = document.createElement("p");
  checkedCount.className = "results__checked-count";
  checkedCount.textContent = `${countResolvedRows(state.checkResponse.medication_table)} of ${pluralizeCount(state.medicationLines.length, "medication")} checked`;

  wrap.append(heading, checkedCount);
  if (state.checkResponse.unresolved_entries.length > 0) {
    wrap.append(buildUncheckedList(state.checkResponse.unresolved_entries));
  }

  const notice = document.createElement("p");
  notice.className = "results__notice";
  notice.textContent = state.checkResponse.notice;
  wrap.append(notice);

  if (state.checkResponse.alerts.length > 0) {
    const list = document.createElement("ol");
    list.className = "alerts";
    for (const alert of sortAlerts(state.checkResponse.alerts)) {
      const originalIndex = state.checkResponse.alerts.indexOf(alert);
      list.append(buildAlertCard(alert, originalIndex, state.expandedAlerts.includes(originalIndex), callbacks));
    }
    wrap.append(list);
  }
  return [wrap];
}

/**
 * Takes one unresolved entry.
 * Writes the one-line reason it was left out of the check and what fixes it, for the results' "Not checked" list.
 * Gives the sentence, naming the entry first.
 */
function uncheckedReason(entry: UnresolvedEntry): string {
  if (entry.status === "needs_confirmation") {
    return `${entry.raw_text}: more than one label matches. Choose one in the list above.`;
  }
  if (usefulChoices(entry.raw_text, candidateChoices(entry.candidates)).length === 0) {
    return `${entry.raw_text}: not a medication name, so it was looked up in the labels instead. See the list above.`;
  }
  return `${entry.raw_text}: not found. Edit it in the list above, or remove it.`;
}

/**
 * Takes the unresolved entries from a check response.
 * Builds the "Not checked" block so a partial result never hides which entries were skipped.
 * Gives the block HTMLElement.
 */
function buildUncheckedList(entries: readonly UnresolvedEntry[]): HTMLElement {
  const block = document.createElement("div");
  const title = document.createElement("p");
  title.className = "unchecked__title";
  title.textContent = "Not checked";
  const list = document.createElement("ul");
  list.className = "unchecked";
  for (const entry of entries) {
    const item = document.createElement("li");
    item.textContent = uncheckedReason(entry);
    list.append(item);
  }
  block.append(title, list);
  return block;
}

/**
 * Takes one alert, its index in the API's own order, whether its extra evidence is expanded, and the Interactions callbacks.
 * Builds the alert card: drug names, tier line, the primary label sentence as a quotation with its source, and the "Show N more" expansion.
 * Gives the list item element.
 */
function buildAlertCard(alert: AlertRecord, alertIndex: number, expanded: boolean, callbacks: InteractionsCallbacks): HTMLElement {
  const card = document.createElement("li");
  card.className = `alert alert--${alertIconKey(alert)}`;

  const drugs = document.createElement("h3");
  drugs.className = "alert__drugs";
  drugs.textContent = alertDrugNames(alert.members);

  const tierLine = document.createElement("p");
  tierLine.className = "alert__tier";
  tierLine.append(alertIcon(alertIconKey(alert), 14));
  const tierName = document.createElement("span");
  tierName.className = "alert__tier-name";
  tierName.textContent = alertDisplayTierName(alert);
  const alertTitle = document.createElement("span");
  alertTitle.textContent = alert.title;
  tierLine.append(tierName, alertTitle);

  card.append(drugs, tierLine);

  const primary = primaryEvidenceMember(alert.members);
  if (primary === undefined) {
    return card;
  }
  card.append(...buildEvidenceBlock(primary));

  const more = additionalEvidenceMembers(alert.members, primary);
  if (more.length > 0) {
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "btn btn--small alert__more";
    toggle.setAttribute("aria-expanded", String(expanded));
    toggle.append(
      document.createTextNode(expanded ? "Show fewer label sentences" : `Show ${pluralizeCount(more.length, "more label sentence")}`),
      chevronDownIcon(14),
    );
    toggle.addEventListener("click", () => {
      callbacks.onToggleAlertExpanded(alertIndex);
    });
    card.append(toggle);
    if (expanded) {
      const extra = document.createElement("div");
      extra.className = "alert__additional";
      for (const member of more) {
        extra.append(...buildEvidenceBlock(member));
      }
      card.append(extra);
    }
  }
  return card;
}

/**
 * Takes one alert member with evidence.
 * Builds its label sentence as a blockquote and, under it, the source drug and section with the DailyMed link.
 * Gives the pair of elements, quote first.
 */
function buildEvidenceBlock(member: AlertMember): readonly [HTMLElement, HTMLElement] {
  const quote = document.createElement("blockquote");
  quote.className = "alert__quote";
  quote.textContent = member.sentence;

  const source = document.createElement("p");
  source.className = "alert__source";
  const sourceText = document.createElement("span");
  sourceText.textContent = `From the ${member.drug_name} label, ${sectionDisplayName(member.section)} section.`;
  const link = document.createElement("a");
  link.href = safeDailymedUrl(member.dailymed_url);
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.className = "alert__dailymed";
  link.setAttribute("aria-label", `Open the ${member.drug_name} label on DailyMed (new tab)`);
  link.append(document.createTextNode("Open on DailyMed"), externalLinkIcon(11));
  source.append(sourceText, link);
  return [quote, source];
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
 * Takes the error's one-line message, the line saying what to do about it, and the retry callback.
 * Builds the error card: what happened, what to do, and a "Try again" button.
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
  retry.className = "btn btn--primary error-card__retry";
  retry.textContent = "Try again";
  retry.addEventListener("click", () => {
    callbacks.onRetryCheck();
  });
  card.append(textCol, retry);
  return card;
}
