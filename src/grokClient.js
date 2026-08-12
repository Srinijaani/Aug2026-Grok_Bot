const XAI_API_BASE = process.env.XAI_API_BASE || "https://api.x.ai/v1";
const DEFAULT_MODEL = process.env.GROK_MODEL || "grok-4";
const SYSTEM_PROMPT =
  process.env.GROK_SYSTEM_PROMPT ||
  "You are Grok, a helpful, witty, and maximally truthful AI assistant built by xAI.";

export function isConfigured() {
  return Boolean(process.env.XAI_API_KEY);
}

export function getModel() {
  return DEFAULT_MODEL;
}

/**
 * Produce a deterministic, offline reply so the app is fully usable end-to-end
 * without an API key. This keeps the chat flow demonstrable while clearly
 * signalling that responses are not coming from the real model.
 */
function demoReply(messages) {
  const lastUser = [...messages].reverse().find((m) => m.role === "user");
  const text = (lastUser?.content || "").trim();
  const lower = text.toLowerCase();

  if (/^(hi|hey|hello|yo|good (morning|afternoon|evening))\b/.test(lower)) {
    return "Hey there! I'm Grok, running in offline demo mode. Set an XAI_API_KEY to talk to the real model. What can I help you with?";
  }
  if (lower.includes("who are you") || lower.includes("what are you")) {
    return "I'm a Grok Bot demo. Right now I'm echoing canned replies because no XAI_API_KEY is configured. Add one to get genuine Grok answers.";
  }
  if (text.length === 0) {
    return "You sent an empty message. Try asking me something!";
  }
  return `Demo mode reply: I received your message ("${
    text.length > 160 ? text.slice(0, 157) + "..." : text
  }"). Configure XAI_API_KEY to get a real Grok response.`;
}

/**
 * Send a conversation to the Grok chat-completions endpoint.
 * Falls back to an offline demo reply when no API key is set.
 *
 * @param {Array<{role: string, content: string}>} messages
 * @returns {Promise<{reply: string, model: string, demo: boolean}>}
 */
export async function chat(messages) {
  const normalized = Array.isArray(messages) ? messages : [];

  if (!isConfigured()) {
    return { reply: demoReply(normalized), model: "demo", demo: true };
  }

  const payload = {
    model: DEFAULT_MODEL,
    messages: [{ role: "system", content: SYSTEM_PROMPT }, ...normalized],
    stream: false,
  };

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60_000);

  try {
    const res = await fetch(`${XAI_API_BASE}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.XAI_API_KEY}`,
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => "");
      throw new Error(
        `xAI API returned ${res.status} ${res.statusText}${detail ? `: ${detail}` : ""}`
      );
    }

    const data = await res.json();
    const reply = data?.choices?.[0]?.message?.content?.trim();
    if (!reply) {
      throw new Error("xAI API returned an empty response.");
    }
    return { reply, model: data.model || DEFAULT_MODEL, demo: false };
  } finally {
    clearTimeout(timeout);
  }
}
