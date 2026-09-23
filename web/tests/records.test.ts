/**
 * Takes no arguments.
 * Tests the state factory functions in src/records.ts.
 * Gives nothing; each test function is run by node:test.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { createInitialState, withState } from "../src/records.js";

/**
 * Takes no arguments.
 * Builds the initial state.
 * Gives nothing; asserts every field starts empty, null, or at its documented default.
 */
test("createInitialState starts with an empty medication list and no results", () => {
  const state = createInitialState();
  assert.deepEqual(state.medicationLines, []);
  assert.equal(state.checkResponse, null);
  assert.equal(state.checkLoading, false);
  assert.equal(state.checkError, null);
  assert.deepEqual(state.expandedRows, []);
  assert.deepEqual(state.lookups, []);
  assert.equal(state.buildDate, null);
});

/**
 * Takes no arguments.
 * Applies a partial change to a state object.
 * Gives nothing; asserts the changed fields update, the rest are untouched, and the original object is not mutated.
 */
test("withState replaces only the given fields and never mutates the input", () => {
  const original = createInitialState();
  const next = withState(original, { medicationLines: ["warfarin"], checkLoading: true });
  assert.deepEqual(next.medicationLines, ["warfarin"]);
  assert.equal(next.checkLoading, true);
  assert.deepEqual(next.lookups, []);
  assert.deepEqual(original.medicationLines, []);
  assert.equal(original.checkLoading, false);
});
