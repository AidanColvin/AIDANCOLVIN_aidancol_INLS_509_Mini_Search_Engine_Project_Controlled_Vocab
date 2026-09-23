/**
 * Takes no arguments.
 * Builds the label lookup block shown under an entry that is not a medication name: what the FDA label text says about that word, with labels for drugs already on the list first.
 * Gives nothing; the exported function is called for the HTMLElement it returns.
 */

import { externalLinkIcon } from "./render_icons.js";
import { hitTitle, splitSnippetIntoSegments } from "./search.js";
import type { LabelLookup, SearchHit } from "./records.js";

const SHOWN_AT_FIRST = 4;
const DAILYMED_URL_PREFIX = "https://dailymed.nlm.nih.gov/";

/**
 * Takes one label lookup and the lowercase names of every medication resolved on the list.
 * Builds the block for it: a waiting line, an error line, a "nothing mentions it" line, or the heading and hit rows with the list's own drugs first.
 * Gives the block HTMLElement.
 */
export function buildLookupBlock(lookup: LabelLookup, listNames: readonly string[]): HTMLElement {
  const block = document.createElement("div");
  block.className = "lookup";
  if (lookup.loading) {
    block.append(captionLine("Looking it up in the labels…"));
    return block;
  }
  if (lookup.error !== null) {
    block.append(captionLine(`${lookup.error.message} ${lookup.error.detail}`));
    return block;
  }
  if (lookup.response === null || lookup.response.hits.length === 0) {
    block.append(captionLine("Not a medication name we know, and no label mentions it. Check the spelling, or remove it."));
    return block;
  }
  const ordered = hitsWithListDrugsFirst(lookup.response.hits, listNames);
  const heading = document.createElement("p");
  heading.className = "lookup__heading";
  heading.textContent = `What the labels say about “${lookup.line}”`;
  const list = document.createElement("ul");
  list.className = "lookup__list";
  const rows = ordered.map((hit) => buildHitRow(hit, lookup.line, isOnList(hit, listNames)));
  for (const row of rows.slice(0, SHOWN_AT_FIRST)) {
    list.append(row);
  }
  block.append(heading, list);
  const rest = rows.slice(SHOWN_AT_FIRST);
  if (rest.length > 0) {
    const more = document.createElement("button");
    more.type = "button";
    more.className = "btn btn--small lookup__more";
    more.textContent = `Show ${rest.length} more`;
    more.addEventListener("click", () => {
      list.append(...rest);
      more.remove();
    });
    block.append(more);
  }
  return block;
}

/**
 * Takes a sentence.
 * Wraps it in the caption paragraph used for a lookup's waiting, error, and empty states.
 * Gives the paragraph element.
 */
function captionLine(text: string): HTMLElement {
  const line = document.createElement("p");
  line.className = "lookup__caption";
  line.textContent = text;
  return line;
}

/**
 * Takes one search hit and the lowercase names of the medications on the list.
 * Checks whether the hit's brand or generic name matches one of those medications.
 * Gives true when the label belongs to a drug already on the list.
 */
function isOnList(hit: SearchHit, listNames: readonly string[]): boolean {
  const own = [hit.brand_name, hit.generic_name].map((value) => value.trim().toLowerCase()).filter((value) => value.length > 0);
  return own.some((candidate) => listNames.some((listed) => listed === candidate || candidate.startsWith(`${listed} `) || listed.startsWith(`${candidate} `)));
}

/**
 * Takes the search hits and the lowercase names of the medications on the list.
 * Reorders the hits so labels for drugs on the list come first, keeping the API's order within each group.
 * Gives the reordered tuple.
 */
function hitsWithListDrugsFirst(hits: readonly SearchHit[], listNames: readonly string[]): readonly SearchHit[] {
  return [...hits.filter((hit) => isOnList(hit, listNames)), ...hits.filter((hit) => !isOnList(hit, listNames))];
}

/**
 * Takes one hit, the word looked up, and whether the hit's drug is on the list.
 * Builds the hit row: the drug name with an "On your list" mark when it applies, the label sentence with the looked-up word in bold, and the DailyMed link.
 * Gives the list item element.
 */
function buildHitRow(hit: SearchHit, query: string, onList: boolean): HTMLElement {
  const item = document.createElement("li");
  item.className = onList ? "lookup__hit lookup__hit--on-list" : "lookup__hit";

  const head = document.createElement("div");
  head.className = "lookup__head";
  const title = hitTitle(hit);
  const nameEl = document.createElement("span");
  nameEl.className = "lookup__name";
  nameEl.textContent = title.primary;
  head.append(nameEl);
  if (title.secondaryGeneric !== null) {
    const secondary = document.createElement("span");
    secondary.className = "lookup__generic";
    secondary.textContent = title.secondaryGeneric.toLowerCase();
    head.append(secondary);
  }
  if (onList) {
    const mark = document.createElement("span");
    mark.className = "pill pill--on-list";
    mark.textContent = "On your list";
    head.append(mark);
  }

  const snippet = document.createElement("p");
  snippet.className = "lookup__snippet";
  for (const segment of splitSnippetIntoSegments(hit.snippet, query)) {
    if (segment.bold) {
      const strong = document.createElement("strong");
      strong.textContent = segment.text;
      snippet.append(strong);
    } else {
      snippet.append(document.createTextNode(segment.text));
    }
  }

  const link = document.createElement("a");
  link.href = safeDailymedUrl(`${DAILYMED_URL_PREFIX}dailymed/drugInfo.cfm?setid=${encodeURIComponent(hit.set_id)}`);
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.className = "lookup__dailymed";
  link.setAttribute("aria-label", `Open the ${title.primary} label on DailyMed (new tab)`);
  link.append(document.createTextNode("Open on DailyMed"), externalLinkIcon(11));

  item.append(head, snippet, link);
  return item;
}

/**
 * Takes a DailyMed URL built from a hit's set id.
 * Checks it starts with the DailyMed origin, per Section 5's safe-rendering rule.
 * Gives the URL unchanged when safe, or "#" when it is not.
 */
function safeDailymedUrl(url: string): string {
  return url.startsWith(DAILYMED_URL_PREFIX) ? url : "#";
}
