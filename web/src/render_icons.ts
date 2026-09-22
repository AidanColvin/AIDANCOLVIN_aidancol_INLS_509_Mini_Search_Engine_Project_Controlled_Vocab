/**
 * Takes no arguments.
 * Builds the inline stroke SVG icons Section 4.2 and Section 6 name, from DOM APIs only.
 * Gives nothing; every exported function is called for the SVGSVGElement it returns.
 */

import type { AlertIconKey } from "./alerts.js";

const SVG_NS = "http://www.w3.org/2000/svg";

/**
 * Takes an SVG tag name and its attributes.
 * Creates that SVG element with each attribute set.
 * Gives the created element.
 */
function svgEl<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Readonly<Record<string, string>>): SVGElementTagNameMap[K] {
  const element = document.createElementNS(SVG_NS, tag);
  for (const [attrName, value] of Object.entries(attrs)) {
    element.setAttribute(attrName, value);
  }
  return element;
}

/**
 * Takes a viewBox size and a stroke width.
 * Creates the root <svg> element shared by every icon, marked decorative.
 * Gives the created SVGSVGElement, with its children still to be appended.
 */
function iconRoot(size: number, strokeWidth: string): SVGSVGElement {
  const svg = svgEl("svg", {
    width: String(size),
    height: String(size),
    viewBox: `0 0 20 20`,
    fill: "none",
    stroke: "currentColor",
    "stroke-width": strokeWidth,
  });
  svg.setAttribute("aria-hidden", "true");
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the tier 1 icon: a circle with a slash, for Contraindicated.
 * Gives the SVGSVGElement.
 */
export function contraindicatedIcon(size: number): SVGSVGElement {
  const svg = iconRoot(size, "1.8");
  svg.append(
    svgEl("circle", { cx: "10", cy: "10", r: "7.5" }),
    svgEl("path", { d: "M4.7 15.3L15.3 4.7" }),
  );
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the tier 2 icon: a square, for Boxed warning.
 * Gives the SVGSVGElement.
 */
export function boxedWarningIcon(size: number): SVGSVGElement {
  const svg = iconRoot(size, "2");
  svg.append(svgEl("rect", { x: "2", y: "2", width: "12", height: "12" }));
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the tier 3 icon: a triangle, for Warning.
 * Gives the SVGSVGElement.
 */
export function warningIcon(size: number): SVGSVGElement {
  const svg = iconRoot(size, "1.8");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("stroke-linecap", "round");
  svg.append(
    svgEl("path", { d: "M10 2.8l8 14H2l8-14z" }),
    svgEl("path", { d: "M10 8.2v4" }),
  );
  const dot = svgEl("circle", { cx: "10", cy: "14.6", r: "0.6" });
  dot.setAttribute("fill", "currentColor");
  svg.append(dot);
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the tier 4 icon: two linked circles, for Interaction note.
 * Gives the SVGSVGElement.
 */
export function interactionNoteIcon(size: number): SVGSVGElement {
  const svg = iconRoot(size, "1.6");
  svg.append(
    svgEl("circle", { cx: "7.5", cy: "10", r: "5" }),
    svgEl("circle", { cx: "12.5", cy: "10", r: "5" }),
  );
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the duplicate-therapy icon: two overlapping squares.
 * Gives the SVGSVGElement.
 */
export function duplicateTherapyIcon(size: number): SVGSVGElement {
  const svg = iconRoot(size, "1.6");
  svg.setAttribute("stroke-linejoin", "round");
  svg.append(
    svgEl("rect", { x: "2.5", y: "2.5", width: "10", height: "10", rx: "2" }),
    svgEl("rect", { x: "7.5", y: "7.5", width: "10", height: "10", rx: "2" }),
  );
  return svg;
}

/**
 * Takes an alert's icon key and an icon pixel size.
 * Picks and builds the matching tier or duplication icon.
 * Gives the SVGSVGElement for that key.
 */
export function alertIcon(key: AlertIconKey, size: number): SVGSVGElement {
  switch (key) {
    case "tier-1":
      return contraindicatedIcon(size);
    case "tier-2":
      return boxedWarningIcon(size);
    case "tier-3":
      return warningIcon(size);
    case "tier-4":
      return interactionNoteIcon(size);
    case "duplication":
      return duplicateTherapyIcon(size);
  }
}

/**
 * Takes an icon pixel size.
 * Builds the right-pointing chevron used on a collapsed medication row.
 * Gives the SVGSVGElement.
 */
export function chevronIcon(size: number): SVGSVGElement {
  const svg = svgEl("svg", {
    width: String(size),
    height: String(size),
    viewBox: "0 0 16 16",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "1.75",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  });
  svg.setAttribute("aria-hidden", "true");
  svg.append(svgEl("path", { d: "M6 3.5l4.5 4.5L6 12.5" }));
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the down-pointing chevron used on an expanded "Show more" button.
 * Gives the SVGSVGElement.
 */
export function chevronDownIcon(size: number): SVGSVGElement {
  const svg = svgEl("svg", {
    width: String(size),
    height: String(size),
    viewBox: "0 0 16 16",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "1.75",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  });
  svg.setAttribute("aria-hidden", "true");
  svg.append(svgEl("path", { d: "M4 6l4 4 4-4" }));
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the remove ("x" in a circle) icon.
 * Gives the SVGSVGElement.
 */
export function removeIcon(size: number): SVGSVGElement {
  const svg = svgEl("svg", {
    width: String(size),
    height: String(size),
    viewBox: "0 0 20 20",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "1.5",
    "stroke-linecap": "round",
  });
  svg.setAttribute("aria-hidden", "true");
  svg.append(
    svgEl("circle", { cx: "10", cy: "10", r: "7.5" }),
    svgEl("path", { d: "M7.4 7.4l5.2 5.2M12.6 7.4l-5.2 5.2" }),
  );
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the plus icon for the add-medication button.
 * Gives the SVGSVGElement.
 */
export function plusIcon(size: number): SVGSVGElement {
  const svg = svgEl("svg", {
    width: String(size),
    height: String(size),
    viewBox: "0 0 20 20",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "2",
    "stroke-linecap": "round",
  });
  svg.setAttribute("aria-hidden", "true");
  svg.append(svgEl("path", { d: "M10 4v12M4 10h12" }));
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the external-link icon used next to "DailyMed" links.
 * Gives the SVGSVGElement.
 */
export function externalLinkIcon(size: number): SVGSVGElement {
  const svg = svgEl("svg", {
    width: String(size),
    height: String(size),
    viewBox: "0 0 12 12",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "1.5",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  });
  svg.setAttribute("aria-hidden", "true");
  svg.append(svgEl("path", { d: "M4.5 2.5h5v5M9.5 2.5L3 9" }));
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the magnifying-glass search icon.
 * Gives the SVGSVGElement.
 */
export function searchIcon(size: number): SVGSVGElement {
  const svg = svgEl("svg", {
    width: String(size),
    height: String(size),
    viewBox: "0 0 20 20",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "1.8",
    "stroke-linecap": "round",
  });
  svg.setAttribute("aria-hidden", "true");
  svg.append(
    svgEl("circle", { cx: "8.5", cy: "8.5", r: "5.5" }),
    svgEl("path", { d: "M12.6 12.6L17 17" }),
  );
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the checkmark icon shown on a selected filter row.
 * Gives the SVGSVGElement.
 */
export function checkmarkIcon(size: number): SVGSVGElement {
  const svg = svgEl("svg", {
    width: String(size),
    height: String(size),
    viewBox: "0 0 20 20",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "2.2",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  });
  svg.setAttribute("aria-hidden", "true");
  svg.append(svgEl("path", { d: "M4.5 10.5l3.8 3.8L15.5 6" }));
  return svg;
}

/**
 * Takes an icon pixel size.
 * Builds the circled-question error icon shown on the check-error card.
 * Gives the SVGSVGElement.
 */
export function errorIcon(size: number): SVGSVGElement {
  const svg = svgEl("svg", {
    width: String(size),
    height: String(size),
    viewBox: "0 0 20 20",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "1.5",
    "stroke-linecap": "round",
  });
  svg.setAttribute("aria-hidden", "true");
  const dot = svgEl("circle", { cx: "10", cy: "13.8", r: "0.9" });
  dot.setAttribute("fill", "currentColor");
  dot.setAttribute("stroke", "none");
  svg.append(
    svgEl("circle", { cx: "10", cy: "10", r: "7.5" }),
    svgEl("path", { d: "M10 6v5" }),
    dot,
  );
  return svg;
}
