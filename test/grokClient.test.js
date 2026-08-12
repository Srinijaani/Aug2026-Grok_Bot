import { test } from "node:test";
import assert from "node:assert/strict";

// Ensure demo mode is active for these tests regardless of environment.
delete process.env.XAI_API_KEY;

const { chat, isConfigured, getModel } = await import("../src/grokClient.js");

test("isConfigured is false without an API key", () => {
  assert.equal(isConfigured(), false);
});

test("getModel returns a non-empty model name", () => {
  assert.ok(typeof getModel() === "string" && getModel().length > 0);
});

test("chat returns a demo reply when unconfigured", async () => {
  const result = await chat([{ role: "user", content: "hello" }]);
  assert.equal(result.demo, true);
  assert.equal(result.model, "demo");
  assert.ok(result.reply.length > 0);
});

test("chat echoes the user's message content in demo mode", async () => {
  const result = await chat([{ role: "user", content: "banana bread recipe" }]);
  assert.ok(result.reply.toLowerCase().includes("banana bread"));
});
