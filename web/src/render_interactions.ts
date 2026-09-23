/**
 * Takes no arguments.
 * Builds the one-page report: the medication field, the alert cards graded worst first, and the medication cards beside them, from state and callbacks only.
 * Gives nothing; the exported mount and update functions are called for the DOM nodes and side effects they produce.
 */

import {
  additionalEvidenceMembers,
  alertDrugNames,
  alertExplanation,
  alertGrade,
  alertIconKey,
  GRADES,
  gradeCounts,
  primaryEvidenceMember,
  sortAlerts,
} from "./alerts.js";
import { formatDailyTotal, pluralizeCount, sectionDisplayName } from "./format.js";
import {
  candidateChoices,
  countResolvedRows,
  formatFrequency,
  releaseForm,
  resolvedNames,
  rowHeadlineName,
  statusForLine,
  usefulChoices,
} from "./meds.js";
import { alertIcon, chevronDownIcon, chevronIcon, externalLinkIcon, plusIcon, removeIcon } from "./render_icons.js";
import { buildLookupBlock } from "./render_lookup.js";
import type { AlertMember, AlertRecord, AppState, LabelLookup, LabelNote, MedicationRow, PdlaTag, UnresolvedEntry } from "./records.js";

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
  readonly report: HTMLElement;
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
const DAILYMED_URL_PREFIX = "https://dailymed.nlm.nih.gov/";

/**
 * Takes the Interactions view's callbacks.
 * Builds the view's static shell once: the title, lede, the medication form with its status line, and the two-column report with the alerts column and the medications column.
 * Gives the InteractionsViewRefs, so the caller can update the dynamic parts and keep the medication field's identity stable across renders.
 */
export function mountInteractionsView(callbacks: InteractionsCallbacks): InteractionsViewRefs {
  const root = document.createElement("section");
  root.className = "interactions-view";
  root.setAttribute("aria-labelledby", "hello-title");

  const title = document.createElement("h1");
  title.className = "site-title";
  title.id = "hello-title";
  title.textContent = "Drug Interaction Screen";

  const lede = document.createElement("p");
  lede.className = "hello-lede";
  lede.textContent = "Type the medications, brand or generic. Their FDA labels are checked for interactions.";

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

  const report = document.createElement("div");
  report.className = "report";
  report.hidden = true;

  const resultsSection = document.createElement("section");
  resultsSection.className = "report__alerts";
  resultsSection.setAttribute("aria-label", "Interactions");
  resultsSection.setAttribute("aria-live", "polite");

  const medsColumn = document.createElement("section");
  medsColumn.className = "report__meds";
  medsColumn.setAttribute("aria-label", "Medications");

  const listHeader = document.createElement("div");
  listHeader.className = "list-header";
  const listCountLabel = document.createElement("h2");
  listCountLabel.className = "report__heading";
  const clearAllButton = document.createElement("button");
  clearAllButton.type = "button";
  clearAllButton.className = "btn btn--small";
  clearAllButton.textContent = "Clear all";
  listHeader.append(listCountLabel, clearAllButton);

  const listSection = document.createElement("ul");
  listSection.className = "med-list";
  listSection.setAttribute("aria-label", "Medications to check");
  medsColumn.append(listHeader, listSection);

  report.append(resultsSection, medsColumn);

  const liveRegion = document.createElement("div");
  liveRegion.className = "visually-hidden";
  liveRegion.setAttribute("aria-live", "polite");
  liveRegion.setAttribute("role", "status");

  root.append(title, lede, form, report, liveRegion);

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

  return { root, medicationInput, addButton, checkStatus, report, listHeader, listCountLabel, clearAllButton, listSection, resultsSection, liveRegion };
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
 * Updates the field's placeholder, the status line, the add button's disabled state, and rebuilds the alert and medication columns from the current state.
 * Gives nothing; the medication input element itself is never replaced.
 */
export function updateInteractionsView(refs: InteractionsViewRefs, state: AppState, callbacks: InteractionsCallbacks): void {
  const hasEntries = state.medicationLines.length > 0;
  refs.medicationInput.placeholder = hasEntries ? PLACEHOLDER_NEXT : PLACEHOLDER_FIRST;
  refs.addButton.disabled = state.checkLoading;
  refs.checkStatus.textContent = state.checkLoading ? CHECKING_TEXT : "";
  refs.report.hidden = !hasEntries;
  refs.listCountLabel.textContent = pluralizeCount(state.medicationLines.length, "medication");

  refs.listSection.replaceChildren(...buildMedicationCards(state, callbacks));
  refs.resultsSection.replaceChildren(...buildAlertsColumn(state, callbacks));

  const alertCount = state.checkResponse === null ? null : state.checkResponse.alerts.length;
  refs.liveRegion.textContent = alertCount === null ? "" : pluralizeCount(alertCount, "alert");
}

/**
 * Takes the current AppState and the Interactions callbacks.
 * Builds one card per medication line, in list order.
 * Gives the array of card elements, empty when the list is empty.
 */
function buildMedicationCards(state: AppState, callbacks: InteractionsCallbacks): readonly HTMLElement[] {
  return state.medicationLines.map((line) => {
    const status = statusForLine(line, state.checkResponse);
    if ("row" in status) {
      return buildResolvedCard(line, status.row, state.expandedRows.includes(line), callbacks);
    }
    if ("unresolved" in status) {
      const lookup = state.lookups.find((candidate) => candidate.line === line);
      return buildUnresolvedCard(line, status.unresolved, lookup, resolvedNames(state.checkResponse), callbacks);
    }
    return buildPendingCard(line, state.checkError === null, callbacks);
  });
}

/**
 * Takes one medication line, whether a check is still expected for it, and the Interactions callbacks.
 * Builds the card shown while its check result has not arrived, dimmed only while a result is still on its way rather than after a failed check.
 * Gives the list item element.
 */
function buildPendingCard(line: string, awaitingResult: boolean, callbacks: InteractionsCallbacks): HTMLElement {
  const card = document.createElement("li");
  card.className = awaitingResult ? "med-card med-card--pending" : "med-card";
  const top = document.createElement("div");
  top.className = "med-card__top";
  const names = document.createElement("div");
  names.className = "med-card__names";
  const headline = document.createElement("span");
  headline.className = "med-card__brand";
  headline.textContent = line;
  names.append(headline);
  top.append(names, buildRemoveButton(line, line, callbacks));
  card.append(top);
  return card;
}

/**
 * Takes one resolved row.
 * Writes the generic line for its card: the base ingredients when the label lists them, otherwise the generic headline.
 * Gives the lowercase generic text.
 */
function cardGenericLine(row: MedicationRow): string {
  if (row.base_ingredients.length > 0) {
    return row.base_ingredients.join(", ").toLowerCase();
  }
  return rowHeadlineName(row);
}

/**
 * Takes one resolved row.
 * Picks the name to lead the card with: the brand the user typed when the match chain starts with one, else the label's own brand, else the generic.
 * Gives the headline text, and whether it is a brand rather than the generic.
 */
function cardBrandLine(row: MedicationRow): { readonly text: string; readonly isBrand: boolean } {
  const generic = cardGenericLine(row);
  const typed = row.matched_name?.[0]?.trim() ?? "";
  if (typed.length > 0 && typed.toLowerCase() !== generic && !row.base_ingredients.includes(typed.toLowerCase()) && typed.toLowerCase() !== rowHeadlineName(row)) {
    return { text: typed, isBrand: true };
  }
  const brand = row.brand[0]?.trim() ?? "";
  if (brand.length > 0 && brand.toLowerCase() !== generic && brand.toLowerCase() !== rowHeadlineName(row)) {
    return { text: brand, isBrand: true };
  }
  return { text: generic, isBrand: false };
}

/**
 * Takes one resolved row.
 * Writes the dose line: strength, frequency, and daily total, whichever the parser read.
 * Gives the parts joined with " · ", or "" when nothing was read.
 */
function doseLine(row: MedicationRow): string {
  const parts: string[] = [];
  if (row.strength !== null) {
    parts.push(row.daily_total_unit === null ? `${row.strength}` : `${row.strength} ${row.daily_total_unit}`);
  }
  const frequency = formatFrequency(row.times_per_day);
  if (frequency.length > 0) {
    parts.push(frequency);
  }
  const total = formatDailyTotal(row.daily_total, row.daily_total_unit);
  if (total.length > 0) {
    parts.push(`${total} total`);
  }
  return parts.join(" · ");
}

/**
 * Takes a DEA schedule string such as "II" or null.
 * Writes the schedule for a card: the word, the numeral, and the C-II style abbreviation.
 * Gives "Schedule II (C-II)", or null when the drug is not scheduled.
 */
function scheduleLabel(schedule: string | null): string | null {
  if (schedule === null || schedule.trim().length === 0) {
    return null;
  }
  return `Schedule ${schedule} (C-${schedule})`;
}

/**
 * Takes one medication line, its resolved row, whether its detail is expanded, and the Interactions callbacks.
 * Builds the medication card: brand and generic names, the dose line, the drug class, schedule, release form, and label terms, with the label's own sentences shown when expanded.
 * Gives the list item element.
 */
function buildResolvedCard(line: string, row: MedicationRow, expanded: boolean, callbacks: InteractionsCallbacks): HTMLElement {
  const card = document.createElement("li");
  card.className = "med-card";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "med-card__button";
  button.setAttribute("aria-expanded", String(expanded));

  const names = document.createElement("span");
  names.className = "med-card__names";
  const brandLine = cardBrandLine(row);
  const brand = document.createElement("span");
  brand.className = "med-card__brand";
  brand.textContent = brandLine.text;
  names.append(brand);
  if (brandLine.isBrand) {
    const generic = document.createElement("span");
    generic.className = "med-card__generic";
    generic.textContent = cardGenericLine(row);
    names.append(generic);
  }
  const dose = document.createElement("span");
  dose.className = "med-card__dose";
  dose.textContent = doseLine(row);
  names.append(dose);

  const chevron = document.createElement("span");
  chevron.className = "med-card__chevron";
  chevron.append(chevronIcon(16));
  button.append(names, chevron);
  button.addEventListener("click", () => {
    callbacks.onToggleRowExpanded(line);
  });

  const top = document.createElement("div");
  top.className = "med-card__top";
  top.append(button, buildRemoveButton(line, row.as_entered, callbacks));
  card.append(top);

  card.append(buildFactsRow(line, row));
  if (expanded) {
    card.append(buildCardDetail(row));
  }
  return card;
}

// Label terms worth showing on a medication card. Route, product form, the
// patient-guide flag, and the DEA terms (the schedule line already covers
// those) are noise next to a drug name; the safety, dosing, and interaction
// terms are not.
const CARD_TAG_TERM_IDS: ReadonlySet<string> = new Set(["T01", "T03", "T04", "T06", "T11", "T12", "T14", "T15", "T16", "T17"]);

/**
 * Takes a resolved row's PDLA tags.
 * Keeps the safety, dosing, and interaction-risk terms and drops route, form, guide, and DEA terms.
 * Gives the tags to show on the card, in the API's order.
 */
function cardTags(tags: readonly PdlaTag[]): readonly PdlaTag[] {
  return tags.filter((tag) => CARD_TAG_TERM_IDS.has(tag.term_id));
}

/**
 * Takes one medication line and its resolved row.
 * Builds the facts row under the names: release form, FDA pharmacologic class, DEA schedule, and the label terms.
 * Gives the row element, which may be empty when the label states none of these.
 */
function buildFactsRow(line: string, row: MedicationRow): HTMLElement {
  const facts = document.createElement("div");
  facts.className = "med-card__facts";
  const form = releaseForm(line);
  if (form !== null) {
    facts.append(fact(form));
  }
  if (row.fda_class !== "Not listed on label." && row.fda_class.trim().length > 0) {
    facts.append(fact(row.fda_class));
  }
  const schedule = scheduleLabel(row.dea_schedule);
  if (schedule !== null) {
    facts.append(fact(schedule, "pill--strong"));
  }
  for (const tag of cardTags(row.pdla_tags)) {
    facts.append(fact(tag.name));
  }
  return facts;
}

/**
 * Takes the text of one fact and an optional extra class.
 * Builds the small pill that shows it.
 * Gives the pill element.
 */
function fact(text: string, extraClass: string = ""): HTMLElement {
  const pill = document.createElement("span");
  pill.className = extraClass.length > 0 ? `pill ${extraClass}` : "pill";
  pill.textContent = text;
  return pill;
}

/**
 * Takes one resolved row.
 * Builds its expanded detail: the label's own sentences (boxed warning, most frequent adverse reaction, dose adjustments, interaction warnings) each with its section, then route and the matched name chain.
 * Gives the detail element.
 */
function buildCardDetail(row: MedicationRow): HTMLElement {
  const detail = document.createElement("div");
  detail.className = "med-card__detail";
  if (row.label_notes.length === 0) {
    const none = document.createElement("p");
    none.className = "med-card__detail-empty";
    none.textContent = "The label carries no boxed warning, dose adjustment, or interaction warning that this tool tracks.";
    detail.append(none);
  }
  for (const note of row.label_notes) {
    detail.append(buildLabelNote(note));
  }
  const meta = document.createElement("p");
  meta.className = "med-card__meta";
  const chain = row.matched_name === null ? "" : row.matched_name.join(" → ");
  const route = row.route.length > 0 ? `Route: ${row.route.join(", ").toLowerCase()}.` : "";
  meta.textContent = [route, chain.length > 0 ? `Matched as ${chain}.` : ""].filter((part) => part.length > 0).join(" ");
  if (meta.textContent.length > 0) {
    detail.append(meta);
  }
  return detail;
}

/**
 * Takes one label note.
 * Builds it as a small heading, the label sentence, and the section it came from.
 * Gives the note element.
 */
function buildLabelNote(note: LabelNote): HTMLElement {
  const wrap = document.createElement("div");
  wrap.className = "label-note";
  const heading = document.createElement("p");
  heading.className = "label-note__name";
  heading.textContent = noteHeading(note);
  const sentence = document.createElement("blockquote");
  sentence.className = "label-note__sentence";
  sentence.textContent = note.sentence;
  const source = document.createElement("p");
  source.className = "label-note__source";
  source.textContent = `From the ${sectionDisplayName(note.field_name)} section of the label.`;
  wrap.append(heading, sentence, source);
  return wrap;
}

/**
 * Takes one label note.
 * Names it for a reader: "Boxed warning", the 10%-or-more adverse reaction, or the term's own name.
 * Gives the heading text.
 */
function noteHeading(note: LabelNote): string {
  if (note.term_id === "T01") {
    return "Boxed warning";
  }
  if (note.term_id === "T04") {
    return "Adverse reaction reported in 10% or more of patients";
  }
  return note.name;
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
 * Builds the card that says the entry was not checked and why, with candidate buttons when any would help, the label lookup block once it has started, plus Edit and remove buttons.
 * Gives the list item element.
 */
function buildUnresolvedCard(
  line: string,
  entry: UnresolvedEntry,
  lookup: LabelLookup | undefined,
  namesOnList: readonly string[],
  callbacks: InteractionsCallbacks,
): HTMLElement {
  const card = document.createElement("li");
  card.className = "med-card med-card--unresolved";

  const top = document.createElement("div");
  top.className = "med-card__top";
  const names = document.createElement("div");
  names.className = "med-card__names";
  const headline = document.createElement("span");
  headline.className = "med-card__brand";
  headline.textContent = line;
  const choices = usefulChoices(line, candidateChoices(entry.candidates));
  const explanation = document.createElement("span");
  explanation.className = "med-card__generic";
  explanation.textContent = unresolvedExplanation(entry, choices.length > 0);
  names.append(headline, explanation);

  const actions = document.createElement("span");
  actions.className = "med-card__actions";
  const edit = document.createElement("button");
  edit.type = "button";
  edit.className = "btn btn--small";
  edit.textContent = "Edit";
  edit.setAttribute("aria-label", `Edit ${line}`);
  edit.addEventListener("click", () => {
    callbacks.onEditUnresolved(line);
  });
  actions.append(edit, buildRemoveButton(line, line, callbacks));
  top.append(names, actions);
  card.append(top);

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
    card.append(pills);
  }
  if (lookup !== undefined) {
    card.append(buildLookupBlock(lookup, namesOnList));
  }
  return card;
}

/**
 * Takes the medication line to remove, its visible label for the button's name, and the Interactions callbacks.
 * Builds the remove ("x") button for one card.
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
 * Builds the alerts column: the error card, or the heading, checked count, the entries that were not checked, the alert cards worst first, and the notice.
 * Gives the array of elements for the column, with only the heading while a first check is still loading.
 */
function buildAlertsColumn(state: AppState, callbacks: InteractionsCallbacks): readonly HTMLElement[] {
  if (state.checkError !== null) {
    return [buildErrorCard(state.checkError.message, state.checkError.detail, callbacks)];
  }
  if (state.checkResponse === null) {
    const waiting = document.createElement("h2");
    waiting.className = "report__heading";
    waiting.textContent = "Interactions";
    return [waiting];
  }
  const wrap = document.createElement("div");
  wrap.className = state.checkLoading ? "results__body results__body--loading" : "results__body";

  const heading = document.createElement("h2");
  heading.className = "report__heading";
  heading.textContent = state.checkResponse.alerts.length === 0 ? "Interactions" : pluralizeCount(state.checkResponse.alerts.length, "interaction");

  const checkedCount = document.createElement("p");
  checkedCount.className = "results__checked-count";
  checkedCount.textContent = `${countResolvedRows(state.checkResponse.medication_table)} of ${pluralizeCount(state.medicationLines.length, "medication")} checked`;
  wrap.append(heading, checkedCount);

  if (state.checkResponse.unresolved_entries.length > 0) {
    wrap.append(buildUncheckedList(state.checkResponse.unresolved_entries));
  }

  wrap.append(buildSeverityStrip(state.checkResponse.alerts));

  if (state.checkResponse.alerts.length === 0) {
    const none = document.createElement("p");
    none.className = "results__none";
    none.textContent = state.checkResponse.no_warning_text;
    wrap.append(none);
  } else {
    const list = document.createElement("ol");
    list.className = "alerts";
    for (const alert of sortAlerts(state.checkResponse.alerts)) {
      const originalIndex = state.checkResponse.alerts.indexOf(alert);
      list.append(buildAlertCard(alert, originalIndex, state.expandedAlerts.includes(originalIndex), callbacks));
    }
    wrap.append(list);
  }

  const notice = document.createElement("p");
  notice.className = "results__notice";
  notice.textContent = state.checkResponse.notice;
  wrap.append(notice);
  return [wrap];
}

/**
 * Takes the alerts from a check response.
 * Builds the A-to-E severity strip, worst grade first, marking each grade that has alerts with its count and the most severe one as the headline.
 * Gives the strip element, with every cell empty when there are no alerts.
 */
function buildSeverityStrip(alerts: readonly AlertRecord[]): HTMLElement {
  const counts = gradeCounts(alerts);
  const worst = GRADES.find((grade) => counts[grade.letter] > 0);
  const figure = document.createElement("figure");
  figure.className = "severity";
  figure.setAttribute("aria-label", worst === undefined ? "No graded interactions" : `Most severe grade: ${worst.letter}, ${worst.name}`);
  const scale = document.createElement("ol");
  scale.className = "severity__scale";
  for (const grade of GRADES) {
    const count = counts[grade.letter];
    const cell = document.createElement("li");
    const classes = ["severity__cell", `severity__cell--${grade.letter.toLowerCase()}`];
    if (count > 0) {
      classes.push("severity__cell--on");
    }
    if (worst !== undefined && grade.letter === worst.letter) {
      classes.push("severity__cell--worst");
    }
    cell.className = classes.join(" ");
    const letter = document.createElement("span");
    letter.className = "severity__letter";
    letter.textContent = grade.letter;
    const name = document.createElement("span");
    name.className = "severity__name";
    name.textContent = grade.name;
    const tally = document.createElement("span");
    tally.className = "severity__count";
    tally.textContent = count === 0 ? "–" : String(count);
    cell.append(letter, name, tally);
    scale.append(cell);
  }
  const caption = document.createElement("figcaption");
  caption.className = "severity__caption";
  caption.textContent = worst === undefined
    ? "No graded interaction found in the labels checked."
    : `Most severe: ${worst.letter}, ${worst.name}. ${worst.meaning}`;
  figure.append(scale, caption);
  return figure;
}

/**
 * Takes one unresolved entry.
 * Writes the one-line reason it was left out of the check and what fixes it, for the "Not checked" list.
 * Gives the sentence, naming the entry first.
 */
function uncheckedReason(entry: UnresolvedEntry): string {
  if (entry.status === "needs_confirmation") {
    return `${entry.raw_text}: more than one label matches. Choose one in the list.`;
  }
  if (usefulChoices(entry.raw_text, candidateChoices(entry.candidates)).length === 0) {
    return `${entry.raw_text}: not a medication name, so it was looked up in the labels instead.`;
  }
  return `${entry.raw_text}: not found. Edit it in the list, or remove it.`;
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
 * Builds the alert card: the grade, the drugs, the rule, the label sentence with its source, what the risk means with a public source, and the "Show N more" expansion.
 * Gives the list item element.
 */
function buildAlertCard(alert: AlertRecord, alertIndex: number, expanded: boolean, callbacks: InteractionsCallbacks): HTMLElement {
  const grade = alertGrade(alert);
  const card = document.createElement("li");
  card.className = `alert alert--${alertIconKey(alert)} alert--grade-${grade.letter.toLowerCase()}`;

  const head = document.createElement("div");
  head.className = "alert__head";
  const badge = document.createElement("span");
  badge.className = "grade";
  badge.setAttribute("aria-label", `Grade ${grade.letter}`);
  badge.textContent = grade.letter;
  const gradeText = document.createElement("span");
  gradeText.className = "alert__grade-text";
  const gradeName = document.createElement("strong");
  gradeName.textContent = grade.name;
  gradeText.append(gradeName, document.createTextNode(` — ${grade.meaning}`));
  head.append(badge, gradeText);

  const drugs = document.createElement("h3");
  drugs.className = "alert__drugs";
  drugs.textContent = alertDrugNames(alert.members);

  const ruleLine = document.createElement("p");
  ruleLine.className = "alert__tier";
  ruleLine.append(alertIcon(alertIconKey(alert), 14));
  const ruleText = document.createElement("span");
  ruleText.textContent = alert.title;
  ruleLine.append(ruleText);

  card.append(head, drugs, ruleLine);

  if (alert.grade_basis !== null && alert.grade_basis.length > 0) {
    const basis = document.createElement("p");
    basis.className = "alert__basis";
    const label = document.createElement("strong");
    label.textContent = `Why ${grade.letter}: `;
    basis.append(label, document.createTextNode(alert.grade_basis));
    card.append(basis);
  }

  const primary = primaryEvidenceMember(alert.members);
  if (primary !== undefined) {
    card.append(...buildEvidenceBlock(primary));
  }

  const explanation = alertExplanation(alert);
  if (explanation !== null) {
    card.append(buildExplanation(explanation.title, explanation.text, explanation.sourceName, explanation.sourceUrl));
  }

  if (primary === undefined) {
    return card;
  }
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
 * Takes an explanation's title, text, and optional source name and URL.
 * Builds the "What this means" block with its source link when there is one.
 * Gives the block element.
 */
function buildExplanation(title: string, text: string, sourceName: string | null, sourceUrl: string | null): HTMLElement {
  const block = document.createElement("div");
  block.className = "alert__why";
  const heading = document.createElement("p");
  heading.className = "alert__why-title";
  heading.textContent = `What this means: ${title}`;
  const body = document.createElement("p");
  body.className = "alert__why-text";
  body.textContent = text;
  block.append(heading, body);
  if (sourceName !== null && sourceUrl !== null) {
    const source = document.createElement("p");
    source.className = "alert__why-source";
    const link = document.createElement("a");
    link.href = sourceUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.append(document.createTextNode(sourceName), externalLinkIcon(11));
    source.append(document.createTextNode("Source: "), link);
    block.append(source);
  }
  return block;
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
