/**
 * Takes no arguments.
 * Builds the header shared by every view: the home logo and the Interactions / Label search segmented control.
 * Gives nothing; every exported function is called for the HTMLElement it returns.
 */

import type { ViewName } from "./records.js";

export interface HeaderCallbacks {
  readonly onNavigate: (view: ViewName) => void;
}

/**
 * Takes the view currently shown and the header's navigation callback.
 * Builds the header element: a home link to the Interactions view, the product name, and the segmented view control.
 * Gives the header HTMLElement, ready to mount at the top of the page.
 */
export function renderHeader(currentView: ViewName, callbacks: HeaderCallbacks): HTMLElement {
  const header = document.createElement("header");
  header.className = "app-header";

  const homeLink = document.createElement("a");
  homeLink.href = "#interactions";
  homeLink.className = "app-header__home";
  homeLink.setAttribute("aria-label", "Home");
  const logo = document.createElement("img");
  logo.src = "/brand/logo.svg";
  logo.alt = "";
  logo.width = 28;
  logo.height = 28;
  homeLink.append(logo);
  homeLink.addEventListener("click", (domEvent) => {
    domEvent.preventDefault();
    callbacks.onNavigate("interactions");
  });

  const bar = document.createElement("div");
  bar.className = "app-header__bar";

  const nameGroup = document.createElement("div");
  nameGroup.className = "app-header__name-group";
  const name = document.createElement("span");
  name.className = "app-header__name";
  name.textContent = "Drug Interaction Screen";
  nameGroup.append(name);

  const nav = document.createElement("nav");
  nav.className = "app-header__nav";
  nav.setAttribute("aria-label", "Views");
  nav.append(
    renderNavLink("interactions", "Interactions", currentView, callbacks),
    renderNavLink("search", "Label search", currentView, callbacks),
  );

  const spacer = document.createElement("div");
  spacer.className = "app-header__spacer";

  bar.append(nameGroup, nav, spacer);
  header.append(homeLink, bar);
  return header;
}

/**
 * Takes the view a link should navigate to, its label text, the currently active view, and the header's navigation callback.
 * Builds one segmented-control link, marked current when it matches the active view.
 * Gives the anchor HTMLElement.
 */
function renderNavLink(view: ViewName, label: string, currentView: ViewName, callbacks: HeaderCallbacks): HTMLAnchorElement {
  const link = document.createElement("a");
  link.href = `#${view}`;
  link.className = view === currentView ? "app-header__nav-link app-header__nav-link--active" : "app-header__nav-link";
  link.textContent = label;
  if (view === currentView) {
    link.setAttribute("aria-current", "page");
  }
  link.addEventListener("click", (domEvent) => {
    domEvent.preventDefault();
    callbacks.onNavigate(view);
  });
  return link;
}
