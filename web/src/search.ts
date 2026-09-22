/**
 * Takes no arguments.
 * Splits a snippet into bolded and plain segments, groups and orders vocabulary terms, and picks a hit's title; touches no fetch call and no DOM node.
 * Gives nothing; every exported function is called for its return value.
 */

import type { SearchHit, TermInfo } from "./records.js";

// Narrower-term hierarchy from MiniVocab_Aidan_Colvin_aidancol.md Section 1:
// T10 (Schedule II Controlled Substance) narrows T07 (Controlled Substance);
// T06 (Renal Dose Adjustment) and T12 (Hepatic Dose Adjustment) narrow T11
// (Organ Impairment Dose Adjustment); T14-T17 (the four interaction-risk
// terms) narrow T13 (Interaction Risk). /api/search?terms_only=1 does not
// carry this hierarchy, so BUILD_PROMPT.md Section 6 asks for it to live in
// one constant here.
const TERM_PARENT: Readonly<Record<string, string>> = {
  T10: "T07",
  T06: "T11",
  T12: "T11",
  T14: "T13",
  T15: "T13",
  T16: "T13",
  T17: "T13",
};

/**
 * Takes a term id.
 * Looks up whether it narrows another term.
 * Gives 1 when it is a narrower term that should be indented, 0 otherwise.
 */
export function termIndentLevel(termId: string): number {
  return TERM_PARENT[termId] !== undefined ? 1 : 0;
}

/**
 * Takes the terms already grouped into one property group, in API order.
 * Reorders them so each narrower term sits immediately after the broader term it narrows, within this group.
 * Gives the reordered terms; a narrower term whose broader term is not in this group keeps its original position.
 */
export function orderTermsWithinGroup(terms: readonly TermInfo[]): readonly TermInfo[] {
  const idsInGroup = new Set(terms.map((term) => term.term_id));
  const isNarrowedHere = (term: TermInfo): boolean => {
    const parent = TERM_PARENT[term.term_id];
    return parent !== undefined && idsInGroup.has(parent);
  };
  const roots = terms.filter((term) => !isNarrowedHere(term));
  const ordered: TermInfo[] = [];
  for (const root of roots) {
    ordered.push(root);
    for (const term of terms) {
      if (TERM_PARENT[term.term_id] === root.term_id) {
        ordered.push(term);
      }
    }
  }
  return ordered;
}

export interface TermGroup {
  readonly propertyGroup: string;
  readonly terms: readonly TermInfo[];
}

/**
 * Takes the available terms from /api/search?terms_only=1, in API order.
 * Groups them by property_group, ordered by each group's first appearance, and orders each group's terms with narrower terms after their broader term.
 * Gives the tuple of term groups, empty when there are no terms.
 */
export function groupTermsByPropertyGroup(terms: readonly TermInfo[]): readonly TermGroup[] {
  const order: string[] = [];
  const buckets = new Map<string, TermInfo[]>();
  for (const term of terms) {
    let bucket = buckets.get(term.property_group);
    if (bucket === undefined) {
      bucket = [];
      buckets.set(term.property_group, bucket);
      order.push(term.property_group);
    }
    bucket.push(term);
  }
  return order.map((propertyGroup) => ({
    propertyGroup,
    terms: orderTermsWithinGroup(buckets.get(propertyGroup) ?? []),
  }));
}

/**
 * Takes the available terms.
 * Builds a lookup from term id to its full TermInfo.
 * Gives the map, empty when there are no terms.
 */
export function termsById(terms: readonly TermInfo[]): ReadonlyMap<string, TermInfo> {
  return new Map(terms.map((term) => [term.term_id, term]));
}

export interface TagDisplay {
  readonly termId: string;
  readonly name: string;
}

/**
 * Takes one hit's tag ids and the term id-to-info lookup.
 * Resolves each tag id to its display name.
 * Gives the tuple of TagDisplay, falling back to the raw id when a tag id is not in the lookup.
 */
export function resolveTagNames(tags: readonly string[], byId: ReadonlyMap<string, TermInfo>): readonly TagDisplay[] {
  return tags.map((termId) => ({ termId, name: byId.get(termId)?.name ?? termId }));
}

export interface SplitTags {
  readonly matching: readonly TagDisplay[];
  readonly rest: readonly TagDisplay[];
}

/**
 * Takes one hit's resolved tags and the currently active filter term ids.
 * Splits them into the ones matching an active filter and the rest.
 * Gives {matching, rest}, with every tag in rest when no filter is active.
 */
export function splitTagsByActiveFilters(tags: readonly TagDisplay[], activeFilters: readonly string[]): SplitTags {
  const active = new Set(activeFilters);
  return {
    matching: tags.filter((tag) => active.has(tag.termId)),
    rest: tags.filter((tag) => !active.has(tag.termId)),
  };
}

/**
 * Takes a search query string.
 * Splits it into lowercase whitespace-separated words.
 * Gives the tuple of query words, empty for a blank query.
 */
export function queryWordsFromQuery(query: string): readonly string[] {
  return query
    .split(/\s+/)
    .map((word) => word.trim().toLowerCase())
    .filter((word) => word.length > 0);
}

export interface SnippetSegment {
  readonly text: string;
  readonly bold: boolean;
}

const WORD_SPLIT = /([A-Za-z0-9]+)/;

/**
 * Takes one hit's snippet text and the search query it came from.
 * Splits the snippet into segments, marking a segment bold when it is one of the query's words.
 * Gives the tuple of segments in order; a query with no words gives the whole snippet as one plain segment.
 */
export function splitSnippetIntoSegments(snippet: string, query: string): readonly SnippetSegment[] {
  const queryWords = new Set(queryWordsFromQuery(query));
  if (queryWords.size === 0) {
    return snippet.length === 0 ? [] : [{ text: snippet, bold: false }];
  }
  return snippet
    .split(WORD_SPLIT)
    .filter((piece) => piece.length > 0)
    .map((piece) => ({ text: piece, bold: queryWords.has(piece.toLowerCase()) }));
}

export interface HitTitle {
  readonly primary: string;
  readonly primaryIsGeneric: boolean;
  readonly secondaryGeneric: string | null;
}

/**
 * Takes one search hit.
 * Picks its title per Section 6: the brand name, or the lowercase generic name when the brand is empty or matches the generic ignoring case.
 * Gives the HitTitle, with secondaryGeneric set only when the brand is shown as the primary title.
 */
export function hitTitle(hit: SearchHit): HitTitle {
  const brand = hit.brand_name.trim();
  const generic = hit.generic_name.trim();
  if (brand === "" || brand.toLowerCase() === generic.toLowerCase()) {
    return { primary: generic.toLowerCase(), primaryIsGeneric: true, secondaryGeneric: null };
  }
  return { primary: brand, primaryIsGeneric: false, secondaryGeneric: generic === "" ? null : generic };
}
