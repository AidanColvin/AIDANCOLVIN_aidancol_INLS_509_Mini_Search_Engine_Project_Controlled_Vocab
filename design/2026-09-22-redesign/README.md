# Drug Interaction Screen redesign, 2026-09-22

Approved design boards for the public front end. They are mockups from a design tool, not runnable pages: read them for layout, spacing, colors, type sizes, and copy. The tool markup (`<x-dc>`, `support.js`, `data-props`) is not part of the site.

| Board | Shows |
| :--- | :--- |
| `Start.dc.html` | First visit: title and an auto-focused medication field |
| `Main.dc.html` | Results on desktop: medication list, inline match choice, alert cards |
| `Mobile.dc.html` | The same results on a phone, dark mode |
| `Search.dc.html` | Label search with grouped vocabulary filters |
| `Tiers.dc.html` | Alert card for each tier, plus duplicate therapy |
| `EdgeStates.dc.html` | No-warning result and the error state |

Drug data on the boards is real output from this repo's checker and search code, run offline on the openFDA fixture labels in `tests/fixtures` (build date 2026-09-21). Bracketed text marks placeholders for alert types the fixtures cannot produce.
