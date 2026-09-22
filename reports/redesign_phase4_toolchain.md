# Redesign run, 2026-09-22 — Phase 4: front-end toolchain

## What was built

- `web/package.json`: `typescript` (pinned `7.0.2`, the verified current stable release) as the only production dev dependency, plus `@types/node` (pinned `26.6.2`, types only, needed so `tsc` recognizes `node:test`/`node:assert/strict`).
- `web/tsconfig.json` (compiles `src/` and `tests/` to `web/out/` for local test runs) and `web/tsconfig.site.json` (compiles only `src/` to `../public/js/`, the deployed bundle), both with `strict`, `useUnknownInCatchVariables`, `noUnusedLocals`, `noUnusedParameters`, `noImplicitReturns`, `lib: ["ES2022", "DOM", "DOM.Iterable"]`, and `NodeNext` module/resolution so relative imports use `.js` extensions.
- `web/tests/style.test.ts`: enforces Section 8.2's style rules from the TypeScript compiler API, not ESLint. See "TypeScript 7's API" below — this could not be the classic `createSourceFile`/`forEachChild` API the prompt assumed, so it is built on the real compiler's scanner (`typescript/unstable/ast`'s `createScanner`) instead.
- A CI step in `.github/workflows/rebuild.yml`, before `vercel build`: `actions/setup-node@v4` (Node 22), `npm ci`, `npm test` (type-check + run the web tests), `npm run build` (produces `public/js/`).
- `.vercelignore`: added `web/node_modules`, `web/out`, and `design` (the reference boards/images have no reason to ship).

## TypeScript 7's API — a real, verified surprise

Section 8.2 item 15 assumes the classic synchronous TypeScript compiler API
(`ts.createSourceFile`, `ts.forEachChild`, `ts.SyntaxKind`) is available from
`import ts from "typescript"`. It is not, as of the version Section 8.2 item 1
itself asks to pin. Verified:

- `npm dist-tag ls typescript` — `latest: 7.0.2` is genuinely current, not a preview.
- `typescript`'s own `package.json` `"exports"` maps `"."` to `./lib/version.cjs`, a version-only stub.
- The real parser now lives behind the native (Go-ported) compiler's Program/Project API under `typescript/unstable/sync`; its only documented construction path is an LSP connection, and even a bare `new API()` returns opaque `NodeHandle`s, not a plain walkable tree.
- What does work standalone — confirmed against every file `style.test.ts` checks — is the real lexer, `createScanner`, from `typescript/unstable/ast`, with a changed argument order from classic TS and some renamed enum members (`SyntaxKind.EndOfFile`, not `EndOfFileToken`).

`style.test.ts` is built on that scanner: it tokenizes each file (handling the
two real disambiguation hazards a raw scanner has — regex-vs-divide and
template-literal substitutions — with the scanner's own `reScanSlashToken`/
`reScanTemplateToken`) and walks the token stream to find top-level `function`
declarations and, in `tests/`, top-level `test(...)` calls, checking each for
a three-line comment, explicit parameter and return types, and no shadowed
parameter name. A separate full-token-stream pass checks for `any` used as a
type (not as a `.any(`/`.catch(` property or method name — the scanner
tokenizes `any` and `catch` as full reserved words even when used that way,
verified directly, and the checks guard against it) and for every `catch`
clause typed `unknown`. Full account in `reports/OPEN_QUESTIONS.md`.

Running the real checker against the real source caught three genuine
violations before this phase closed: two `async function` declarations whose
modifier defeated the first version's comment lookup (fixed the lookup to
step back over `async` as well as `export`), and one function
(`maxMedicationTextChars`) whose comment was actually only two lines, missing
the "Does" line (fixed the comment itself). All three are now correct.

## Commands run and results

- `npx tsc -p tsconfig.json --noEmit`: clean.
- `npm test` (`tsc -p tsconfig.json && node --test "out/tests/**/*.test.js"`): 101 passed (grows to 103 by the end of Phase 5 as two more tests were added; see that report for the final count).
- `npx tsc -p tsconfig.site.json`: builds `public/js/main.js` and every other module.
- `python -m pytest -q`: 289 passed, unaffected.

## What I should check by hand

- Nothing yet — no deploy from this phase alone.

## Open questions

See `reports/OPEN_QUESTIONS.md` for the TypeScript 7 API judgment call and the `@types/node` justification.
