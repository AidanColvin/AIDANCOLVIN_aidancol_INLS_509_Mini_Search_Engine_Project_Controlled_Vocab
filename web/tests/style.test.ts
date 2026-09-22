/**
 * Takes no arguments.
 * Tokenizes every file in web/src/ and web/tests/ with the TypeScript compiler API's scanner and enforces BUILD_PROMPT.md Section 8.2's style rules.
 * Gives nothing; each test function is run by node:test.
 */

import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { createScanner, LanguageVariant, SyntaxKind } from "typescript/unstable/ast";

// TypeScript 7's public npm package no longer exports the classic
// ts.createSourceFile / ts.forEachChild parser from its default entry
// point: "typescript"'s package.json "exports" maps "." to
// lib/version.cjs, a version-only stub, and the real parser now lives
// behind the native compiler's LSP-oriented Program/Project API under
// "typescript/unstable/sync" (its API class is only documented to be
// built from an LSP connection). What does work standalone, verified
// against every file this test checks, is the real lexer:
// typescript/unstable/ast's createScanner. This module builds a
// disciplined token-level analysis on that scanner -- still the
// TypeScript compiler API, not a hand-rolled regex parser and not
// ESLint -- handling the two real scanner disambiguation hazards
// (regex literals and template-literal substitutions) with the
// scanner's own reScanSlashToken and reScanTemplateToken. Recorded in
// reports/OPEN_QUESTIONS.md, heading "Redesign run, 2026-09-22".
//
// Scope: this checks top-level "function" declarations and top-level
// test(...) calls in tests/ only -- the substantive, named "functions,
// helpers, entry points, and tests" Section 8.2 item 4 names. It does
// not require a three-line comment or explicit types on an inline
// callback passed directly to another call (e.g. `.map((x) => ...)`,
// an addEventListener handler, or an object-literal method on a
// typed callbacks interface), since those are already fully typed
// through contextual typing under "strict": true and documenting each
// one would not serve the rule's intent.

const REPO_ROOT = path.resolve(import.meta.dirname, "..", "..", "..");
const WEB_SRC_DIR = path.join(REPO_ROOT, "web", "src");
const WEB_TESTS_DIR = path.join(REPO_ROOT, "web", "tests");

// From BUILD_PROMPT.md Section 8.2 item 10.
const BANNED_PARAMETER_NAMES: ReadonlySet<string> = new Set([
  "Array", "Object", "Map", "Set", "String", "Number", "Boolean", "Promise",
  "Error", "JSON", "Math", "Date", "RegExp", "Symbol", "globalThis", "window",
  "document", "location", "navigator", "history", "event", "name", "status",
]);

// Token kinds after which a "/" starts a regex literal rather than
// division, for the subset of contexts this codebase actually uses.
const TOKENS_BEFORE_A_REGEX: ReadonlySet<number> = new Set([
  SyntaxKind.OpenParenToken,
  SyntaxKind.OpenBraceToken,
  SyntaxKind.OpenBracketToken,
  SyntaxKind.CommaToken,
  SyntaxKind.SemicolonToken,
  SyntaxKind.ColonToken,
  SyntaxKind.ReturnKeyword,
  SyntaxKind.FirstAssignment,
  SyntaxKind.EqualsEqualsToken,
  SyntaxKind.ExclamationEqualsToken,
]);

const TRIVIA_KINDS: ReadonlySet<number> = new Set([SyntaxKind.WhitespaceTrivia, SyntaxKind.NewLineTrivia]);

interface Token {
  readonly kind: number;
  readonly text: string;
  readonly depth: number;
}

/**
 * Takes one file's source text.
 * Scans it into a token list with each token's brace-nesting depth, re-scanning a slash after a regex-starting token and a template substitution's closing brace so neither corrupts the rest of the file.
 * Gives the tuple of tokens, including comment and whitespace trivia, in source order.
 */
function tokenize(text: string): readonly Token[] {
  const scanner = createScanner(false, LanguageVariant.Standard, text);
  const tokens: Token[] = [];
  const braceStack: ("brace" | "template")[] = [];
  let depth = 0;
  for (;;) {
    let kind = scanner.scan();
    if (kind === SyntaxKind.EndOfFile) {
      break;
    }
    if (kind === SyntaxKind.SlashToken) {
      const previous = tokens[tokens.length - 1];
      if (previous === undefined || TOKENS_BEFORE_A_REGEX.has(previous.kind)) {
        kind = scanner.reScanSlashToken();
      }
    }
    if (kind === SyntaxKind.CloseBraceToken) {
      const top = braceStack.pop();
      if (top === "template") {
        kind = scanner.reScanTemplateToken(false);
        if (kind === SyntaxKind.TemplateMiddle) {
          braceStack.push("template");
        }
      } else {
        depth -= 1;
      }
      tokens.push({ kind, text: scanner.getTokenText(), depth });
      continue;
    }
    if (kind === SyntaxKind.TemplateHead) {
      braceStack.push("template");
    } else if (kind === SyntaxKind.OpenBraceToken) {
      braceStack.push("brace");
    }
    tokens.push({ kind, text: scanner.getTokenText(), depth });
    if (kind === SyntaxKind.OpenBraceToken) {
      depth += 1;
    }
  }
  return tokens;
}

/**
 * Takes a token list.
 * Drops whitespace and newline trivia, keeping comments and every real token.
 * Gives the filtered tuple.
 */
function withoutWhitespace(tokens: readonly Token[]): readonly Token[] {
  return tokens.filter((token) => !TRIVIA_KINDS.has(token.kind));
}

/**
 * Takes a token's index in a token list and the list itself.
 * Walks backward over whitespace and newline trivia only, to the position just before this declaration.
 * Gives the index of the nearest non-trivia token before it, or -1 when there is none.
 */
function indexOfPrecedingNonTrivia(tokens: readonly Token[], index: number): number {
  let cursor = index - 1;
  while (cursor >= 0 && TRIVIA_KINDS.has((tokens[cursor] as Token).kind)) {
    cursor -= 1;
  }
  return cursor;
}

const DECLARATION_MODIFIER_KINDS: ReadonlySet<number> = new Set([SyntaxKind.ExportKeyword, SyntaxKind.AsyncKeyword]);

/**
 * Takes the full token list and the index of a top-level FunctionKeyword token.
 * Finds the JSDoc comment that should document it, stepping back over any leading "export" and "async" modifiers first.
 * Gives the index of that comment token, or -1 when nothing precedes the declaration.
 */
function jsDocIndexBeforeFunction(tokens: readonly Token[], functionKeywordIndex: number): number {
  let cursor = indexOfPrecedingNonTrivia(tokens, functionKeywordIndex);
  while (cursor !== -1 && DECLARATION_MODIFIER_KINDS.has((tokens[cursor] as Token).kind)) {
    cursor = indexOfPrecedingNonTrivia(tokens, cursor);
  }
  return cursor;
}

/**
 * Takes a raw JSDoc comment token's text, including its "/**" and "*​/" markers.
 * Splits it into non-empty content lines, stripped of a leading "*" marker and surrounding whitespace.
 * Gives the tuple of content lines, empty when the comment has no text.
 */
function jsDocContentLines(commentText: string): readonly string[] {
  return commentText
    .split("\n")
    .map((line) => line.replace(/^\s*\/?\*+\/?\s?/, "").replace(/\*\/\s*$/, "").trim())
    .filter((line) => line.length > 0);
}

/**
 * Takes a label for the failure message and the token just before a declaration, when there is one.
 * Checks it is a JSDoc-style comment with exactly three content lines, the first starting with "Takes" and the last with "Gives".
 * Gives nothing; throws with a message naming the label when the comment is missing or malformed.
 */
function assertThreeLineComment(label: string, precedingToken: Token | undefined): void {
  assert.ok(precedingToken !== undefined, `${label} must be preceded by a three-line JSDoc comment`);
  const token = precedingToken as Token;
  assert.equal(token.kind, SyntaxKind.MultiLineCommentTrivia, `${label} must be preceded by a /** */ comment, found ${SyntaxKind[token.kind]}`);
  assert.ok(token.text.startsWith("/**"), `${label}'s comment must start with "/**"`);
  const lines = jsDocContentLines(token.text);
  assert.equal(lines.length, 3, `${label}'s comment must have exactly three lines, found ${lines.length}: ${JSON.stringify(lines)}`);
  assert.match(lines[0] as string, /^Takes/, `${label}'s first comment line must start with "Takes"`);
  assert.match(lines[2] as string, /^Gives/, `${label}'s third comment line must start with "Gives"`);
}

interface FunctionSignature {
  readonly name: string;
  readonly declarationStart: number;
  readonly parameterSegments: readonly (readonly Token[])[];
  readonly hasReturnType: boolean;
}

/**
 * Takes the full token list and the index of a top-level FunctionKeyword token.
 * Reads the function's name, the index its comment search should start from, each parameter's tokens, and whether a return type follows the parameter list.
 * Gives the FunctionSignature.
 */
function readFunctionSignature(tokens: readonly Token[], functionKeywordIndex: number): FunctionSignature {
  const significant = withoutWhitespaceKeepingIndex(tokens);
  const ownIndex = significant.findIndex((entry) => entry.index === functionKeywordIndex);
  const nameEntry = significant[ownIndex + 1] as { readonly token: Token; readonly index: number };
  const name = nameEntry.token.text;

  let cursor = ownIndex + 2;
  if ((significant[cursor] as { readonly token: Token }).token.kind === SyntaxKind.LessThanToken) {
    let angleDepth = 0;
    for (; cursor < significant.length; cursor += 1) {
      const kind = (significant[cursor] as { readonly token: Token }).token.kind;
      if (kind === SyntaxKind.LessThanToken) angleDepth += 1;
      if (kind === SyntaxKind.GreaterThanToken) angleDepth -= 1;
      if (angleDepth === 0) {
        cursor += 1;
        break;
      }
    }
  }

  cursor += 1; // past OpenParenToken
  const parameterTokens: Token[] = [];
  let parenDepth = 1;
  for (; cursor < significant.length && parenDepth > 0; cursor += 1) {
    const token = (significant[cursor] as { readonly token: Token }).token;
    if (token.kind === SyntaxKind.OpenParenToken) parenDepth += 1;
    if (token.kind === SyntaxKind.CloseParenToken) {
      parenDepth -= 1;
      if (parenDepth === 0) break;
    }
    parameterTokens.push(token);
  }
  const parameterSegments = splitTopLevelCommaSegments(parameterTokens);

  const afterParenIndex = cursor + 1;
  const afterParen = significant[afterParenIndex] as { readonly token: Token } | undefined;
  const hasReturnType = afterParen !== undefined && afterParen.token.kind === SyntaxKind.ColonToken;

  return { name, declarationStart: functionKeywordIndex, parameterSegments, hasReturnType };
}

/**
 * Takes a token list.
 * Pairs each token with its original index, dropping whitespace and newline trivia.
 * Gives the tuple of {token, index} pairs.
 */
function withoutWhitespaceKeepingIndex(tokens: readonly Token[]): readonly { readonly token: Token; readonly index: number }[] {
  const result: { readonly token: Token; readonly index: number }[] = [];
  tokens.forEach((token, index) => {
    if (!TRIVIA_KINDS.has(token.kind)) {
      result.push({ token, index });
    }
  });
  return result;
}

/**
 * Takes a flat list of parameter-list tokens.
 * Splits it at top-level commas, treating nested parens, braces, brackets, and angle brackets as one unit.
 * Gives the tuple of parameter segments, empty for an empty parameter list.
 */
function splitTopLevelCommaSegments(tokens: readonly Token[]): readonly (readonly Token[])[] {
  const segments: Token[][] = [];
  let current: Token[] = [];
  let depth = 0;
  for (const token of tokens) {
    if (
      token.kind === SyntaxKind.OpenParenToken ||
      token.kind === SyntaxKind.OpenBraceToken ||
      token.kind === SyntaxKind.OpenBracketToken ||
      token.kind === SyntaxKind.LessThanToken
    ) {
      depth += 1;
    }
    if (
      token.kind === SyntaxKind.CloseParenToken ||
      token.kind === SyntaxKind.CloseBraceToken ||
      token.kind === SyntaxKind.CloseBracketToken ||
      token.kind === SyntaxKind.GreaterThanToken
    ) {
      depth -= 1;
    }
    if (token.kind === SyntaxKind.CommaToken && depth === 0) {
      segments.push(current);
      current = [];
      continue;
    }
    current.push(token);
  }
  if (current.length > 0) {
    segments.push(current);
  }
  return segments.filter((segment) => segment.length > 0);
}

/**
 * Takes one parameter's token segment.
 * Checks it has a top-level colon (an explicit type annotation) and, when it starts with a plain identifier, that the identifier is not a banned name.
 * Gives nothing; throws with a message identifying the parameter when either check fails.
 */
function assertParameterSegmentIsTypedAndUnshadowed(label: string, segment: readonly Token[]): void {
  const significant = segment.filter((token) => !TRIVIA_KINDS.has(token.kind));
  const hasTopLevelColon = significant.some((token) => token.kind === SyntaxKind.ColonToken);
  assert.ok(hasTopLevelColon, `${label} must have an explicit type`);
  const first = significant[0];
  if (first !== undefined && first.kind === SyntaxKind.Identifier) {
    assert.ok(!BANNED_PARAMETER_NAMES.has(first.text), `${label}'s parameter "${first.text}" shadows a banned global name`);
  }
}

/**
 * Takes no arguments.
 * Lists every ".ts" file directly inside web/src/ and web/tests/, skipping declaration files.
 * Gives the tuple of absolute file paths.
 */
function allCheckedFiles(): readonly string[] {
  const listDir = (dir: string): readonly string[] =>
    readdirSync(dir)
      .filter((entry) => entry.endsWith(".ts") && !entry.endsWith(".d.ts"))
      .map((entry) => path.join(dir, entry));
  return [...listDir(WEB_SRC_DIR), ...listDir(WEB_TESTS_DIR)];
}

for (const filePath of allCheckedFiles()) {
  const relativePath = path.relative(REPO_ROOT, filePath);
  const isTestFile = filePath.startsWith(WEB_TESTS_DIR);

  test(`${relativePath}: every top-level function is documented, typed, and unshadowed`, () => {
    const tokens = tokenize(readFileSync(filePath, "utf8"));
    tokens.forEach((token, index) => {
      if (token.kind !== SyntaxKind.FunctionKeyword || token.depth !== 0) {
        return;
      }
      const commentIndex = jsDocIndexBeforeFunction(tokens, index);
      const signature = readFunctionSignature(tokens, index);
      const label = `${relativePath}: ${signature.name}`;
      assertThreeLineComment(label, commentIndex >= 0 ? tokens[commentIndex] : undefined);
      for (const segment of signature.parameterSegments) {
        assertParameterSegmentIsTypedAndUnshadowed(`${label}'s parameter list`, segment);
      }
      assert.ok(signature.hasReturnType, `${label} must have an explicit return type`);
    });
  });

  if (isTestFile) {
    test(`${relativePath}: every top-level test(...) call is documented`, () => {
      const tokens = tokenize(readFileSync(filePath, "utf8"));
      tokens.forEach((token, index) => {
        if (token.kind !== SyntaxKind.Identifier || token.text !== "test" || token.depth !== 0) {
          return;
        }
        const nextIndex = indexOfNextNonTrivia(tokens, index);
        if (nextIndex === -1 || (tokens[nextIndex] as Token).kind !== SyntaxKind.OpenParenToken) {
          return;
        }
        const commentIndex = indexOfPrecedingNonTrivia(tokens, index);
        assertThreeLineComment(`${relativePath}: test() call at token ${index}`, commentIndex >= 0 ? tokens[commentIndex] : undefined);
      });
    });
  }

  test(`${relativePath}: never uses "any" as a type`, () => {
    const tokens = tokenize(readFileSync(filePath, "utf8"));
    const offenders = tokens.filter((token, index) => {
      if (token.kind !== SyntaxKind.AnyKeyword) {
        return false;
      }
      const precedingIndex = indexOfPrecedingNonTrivia(tokens, index);
      const preceding = precedingIndex >= 0 ? tokens[precedingIndex] : undefined;
      return preceding === undefined || preceding.kind !== SyntaxKind.DotToken;
    });
    assert.equal(offenders.length, 0, `${relativePath} uses "any" ${offenders.length} time(s)`);
  });

  test(`${relativePath}: every catch variable is typed "unknown"`, () => {
    const tokens = tokenize(readFileSync(filePath, "utf8"));
    const significant = withoutWhitespace(tokens);
    let offenderCount = 0;
    significant.forEach((token, index) => {
      if (token.kind !== SyntaxKind.CatchKeyword) {
        return;
      }
      const previous = significant[index - 1];
      if (previous !== undefined && previous.kind === SyntaxKind.DotToken) {
        return; // a ".catch(" promise method call, not a catch clause
      }
      const openParen = significant[index + 1];
      if (openParen === undefined || openParen.kind !== SyntaxKind.OpenParenToken) {
        return; // a bare "catch {" with no variable
      }
      const colonOrClose = significant[index + 3];
      if (colonOrClose === undefined) {
        return;
      }
      if (colonOrClose.kind === SyntaxKind.CloseParenToken) {
        offenderCount += 1; // catch (err) with no type annotation
        return;
      }
      const typeToken = significant[index + 4];
      if (colonOrClose.kind !== SyntaxKind.ColonToken || typeToken === undefined || typeToken.kind !== SyntaxKind.UnknownKeyword) {
        offenderCount += 1;
      }
    });
    assert.equal(offenderCount, 0, `${relativePath} has ${offenderCount} catch clause(s) not typed "catch (err: unknown)"`);
  });
}

/**
 * Takes a token list and an index within it.
 * Walks forward over whitespace and newline trivia only.
 * Gives the index of the nearest non-trivia token after it, or -1 when there is none.
 */
function indexOfNextNonTrivia(tokens: readonly Token[], index: number): number {
  let cursor = index + 1;
  while (cursor < tokens.length && TRIVIA_KINDS.has((tokens[cursor] as Token).kind)) {
    cursor += 1;
  }
  return cursor < tokens.length ? cursor : -1;
}
