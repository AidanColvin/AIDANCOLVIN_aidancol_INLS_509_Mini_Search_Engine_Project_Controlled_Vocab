/**
 * Takes no arguments.
 * Declares the readonly record types shared across the app, matching the /api/check and /api/search contract.
 * Gives nothing; this module has no runtime code, only types and factory functions.
 */

export interface PdlaTag {
  readonly term_id: string;
  readonly name: string;
}

export interface MedicationRow {
  readonly as_entered: string;
  readonly matched_name: readonly string[] | null;
  readonly generic: readonly string[];
  readonly base_ingredients: readonly string[];
  readonly brand: readonly string[];
  readonly fda_class: string;
  readonly route: readonly string[];
  readonly dea_schedule: string | null;
  readonly daily_total: number | null;
  readonly daily_total_unit: string | null;
  readonly pdla_tags: readonly PdlaTag[];
}

export interface AlertMember {
  readonly drug_name: string;
  readonly set_id: string;
  readonly effective_time: string;
  readonly section: string;
  readonly sentence: string;
  readonly dailymed_url: string;
}

export interface AlertRecord {
  readonly kind: "group" | "pair" | "duplication";
  readonly risk: string;
  readonly title: string;
  readonly tier: number | null;
  readonly tier_name: string;
  readonly members: readonly AlertMember[];
  readonly note: string;
}

export interface UnresolvedEntry {
  readonly raw_text: string;
  readonly status: "unresolved" | "needs_confirmation";
  readonly reason: string;
  readonly candidates: readonly string[];
}

export interface CheckResponse {
  readonly build_date: string;
  readonly medication_table: readonly MedicationRow[];
  readonly alerts: readonly AlertRecord[];
  readonly unresolved_entries: readonly UnresolvedEntry[];
  readonly no_warning_text: string;
  readonly notice: string;
}

export interface ApiErrorResponse {
  readonly error: string;
}

export interface SearchHit {
  readonly set_id: string;
  readonly brand_name: string;
  readonly generic_name: string;
  readonly snippet: string;
  readonly tags: readonly string[];
  readonly effective_time: string;
  readonly score: number;
}

export interface SearchResponse {
  readonly hits: readonly SearchHit[];
  readonly query: string;
  readonly operator: string;
  readonly build_date: string;
}

export interface TermInfo {
  readonly term_id: string;
  readonly name: string;
  readonly property_group: string;
}

export interface TermsOnlyResponse {
  readonly build_date: string;
  readonly available_terms: readonly TermInfo[];
}

export type ViewName = "interactions" | "search";

export interface CheckErrorState {
  readonly message: string;
  readonly detail: string;
}

export interface AppState {
  readonly view: ViewName;
  readonly medicationLines: readonly string[];
  readonly checkResponse: CheckResponse | null;
  readonly checkLoading: boolean;
  readonly checkError: CheckErrorState | null;
  readonly expandedRows: readonly string[];
  readonly expandedAlerts: readonly number[];
  readonly searchQuery: string;
  readonly searchFilters: readonly string[];
  readonly searchOperator: "AND" | "OR";
  readonly searchResponse: SearchResponse | null;
  readonly searchLoading: boolean;
  readonly searchError: CheckErrorState | null;
  readonly availableTerms: readonly TermInfo[];
  readonly buildDate: string | null;
}

/**
 * Takes no arguments.
 * Builds the app's starting state before any medication or search request has run.
 * Gives a fresh AppState with an empty medication list and no results.
 */
export function createInitialState(): AppState {
  return {
    view: "interactions",
    medicationLines: [],
    checkResponse: null,
    checkLoading: false,
    checkError: null,
    expandedRows: [],
    expandedAlerts: [],
    searchQuery: "",
    searchFilters: [],
    searchOperator: "AND",
    searchResponse: null,
    searchLoading: false,
    searchError: null,
    availableTerms: [],
    buildDate: null,
  };
}

/**
 * Takes the current AppState and a partial set of fields to change.
 * Builds a new state object with those fields replaced.
 * Gives the new AppState; the caller's original state is never mutated.
 */
export function withState(state: AppState, changes: Partial<AppState>): AppState {
  return { ...state, ...changes };
}
