/**
 * Takes no arguments.
 * Builds the page's quiet top bar: the logo mark alone, since the title below already names the product and the whole app is one page.
 * Gives nothing; every exported function is called for the HTMLElement it returns.
 */

/**
 * Takes no arguments.
 * Builds the header element: the logo mark, linking back to the top of the page.
 * Gives the header HTMLElement, ready to mount at the top of the page.
 */
export function renderHeader(): HTMLElement {
  const header = document.createElement("header");
  header.className = "app-header";

  const homeLink = document.createElement("a");
  homeLink.href = "#";
  homeLink.className = "app-header__home";
  homeLink.setAttribute("aria-label", "Drug Interaction Screen, back to top");
  const logo = document.createElement("img");
  logo.src = "/brand/logo.svg";
  logo.alt = "";
  logo.width = 24;
  logo.height = 24;
  homeLink.append(logo);
  homeLink.addEventListener("click", (domEvent) => {
    domEvent.preventDefault();
    window.scrollTo({ top: 0, behavior: "smooth" });
    document.getElementById("add-med")?.focus({ preventScroll: true });
  });

  header.append(homeLink);
  return header;
}
