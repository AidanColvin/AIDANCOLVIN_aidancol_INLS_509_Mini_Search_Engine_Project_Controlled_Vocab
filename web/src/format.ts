/**
 * Takes no arguments.
 * Formats names, doses, section labels, and counts; touches no fetch call and no DOM node.
 * Gives nothing; every exported function is called for its return value.
 */

const SECTION_DISPLAY_NAMES: Readonly<Record<string, string>> = {
  contraindications: "Contraindications",
  boxed_warning: "Boxed Warning",
  warnings_and_cautions: "Warnings and Precautions",
  warnings: "Warnings",
  precautions: "Precautions",
  drug_interactions: "Drug Interactions",
  description: "Description",
};

/**
 * Takes an API section field value such as "warnings_and_cautions".
 * Looks up its display name from the fixed Section 4.2 table.
 * Gives the display name, or the raw value unchanged when it is not in the table.
 */
export function sectionDisplayName(section: string): string {
  return SECTION_DISPLAY_NAMES[section] ?? section;
}

/**
 * Takes a daily total value and its unit, either of which may be missing.
 * Formats the total with no trailing ".0" and the unit appended.
 * Gives "{total} {unit}/day", or an empty string when the total is missing.
 */
export function formatDailyTotal(total: number | null, unit: string | null): string {
  if (total === null) {
    return "";
  }
  return unit === null ? `${total}/day` : `${total} ${unit}/day`;
}

/**
 * Takes a count and the singular form of a noun.
 * Pluralizes the noun for any count other than exactly one.
 * Gives "{count} {noun}" with the noun pluralized by adding "s" when count is not 1.
 */
export function pluralizeCount(count: number, singular: string): string {
  return count === 1 ? `${count} ${singular}` : `${count} ${singular}s`;
}

const MONTH_ABBREVIATIONS: readonly string[] = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/**
 * Takes a build date in "YYYY-MM-DD" form.
 * Formats it as "Mon D, YYYY" for the footer.
 * Gives the formatted date, or the input unchanged when it is not in that form.
 */
export function formatBuildDate(buildDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(buildDate);
  if (match === null) {
    return buildDate;
  }
  const [, year, monthText, dayText] = match;
  const monthIndex = Number(monthText) - 1;
  const month = MONTH_ABBREVIATIONS[monthIndex];
  if (month === undefined) {
    return buildDate;
  }
  return `${month} ${Number(dayText)}, ${year}`;
}

/**
 * Takes the matched chain from a row's expanded detail, in resolution order.
 * Joins the chain with the arrow separator Section 4.1 specifies.
 * Gives the joined string, empty when the chain is empty.
 */
export function formatMatchedChain(chain: readonly string[]): string {
  return chain.join(" → ");
}
