/**
 * Takes no arguments.
 * Builds the page's quiet top bar: the logo and the product name, with no navigation, since the whole app is one page.
 * Gives nothing; every exported function is called for the HTMLElement it returns.
 */

/**
 * Takes no arguments.
 * Builds the header element: the logo and product name, linking back to the top of the page.
 * Gives the header HTMLElement, ready to mount at the top of the page.
 */
export function renderHeader(): HTMLElement {
  const header = document.createElement("header");
  header.className = "app-header";

  const homeLink = document.createElement("a");
  homeLink.href = "#";
  homeLink.className = "app-header__home";
  const logo = document.createElement("img");
  logo.src = "/brand/logo.svg";
  logo.alt = "";
  logo.width = 24;
  logo.height = 24;
  const name = document.createElement("span");
  name.className = "app-header__name";
  name.textContent = "Drug Interaction Screen";
  homeLink.append(logo, name);
  homeLink.addEventListener("click", (domEvent) => {
    domEvent.preventDefault();
    window.scrollTo({ top: 0, behavior: "smooth" });
    document.getElementById("add-med")?.focus({ preventScroll: true });
  });

  header.append(homeLink);
  return header;
}
