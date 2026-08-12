import "dotenv/config";
import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chat, isConfigured, getModel } from "./src/grokClient.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json({ limit: "1mb" }));
app.use(express.static(path.join(__dirname, "public")));

app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
    configured: isConfigured(),
    mode: isConfigured() ? "live" : "demo",
    model: isConfigured() ? getModel() : "demo",
  });
});

app.post("/api/chat", async (req, res) => {
  try {
    const body = req.body || {};
    let messages = body.messages;

    if (!Array.isArray(messages)) {
      if (typeof body.message === "string") {
        messages = [{ role: "user", content: body.message }];
      } else {
        return res
          .status(400)
          .json({ error: "Request must include a `messages` array or a `message` string." });
      }
    }

    const cleaned = messages
      .filter((m) => m && typeof m.content === "string")
      .map((m) => ({
        role: ["system", "user", "assistant"].includes(m.role) ? m.role : "user",
        content: m.content,
      }));

    if (cleaned.length === 0) {
      return res.status(400).json({ error: "No valid messages provided." });
    }

    const result = await chat(cleaned);
    res.json(result);
  } catch (err) {
    console.error("[/api/chat] error:", err.message);
    res.status(502).json({ error: `Failed to get a response: ${err.message}` });
  }
});

app.listen(PORT, () => {
  const mode = isConfigured() ? `live (model: ${getModel()})` : "demo (no XAI_API_KEY set)";
  console.log(`Grok Bot listening on http://localhost:${PORT} — mode: ${mode}`);
});
