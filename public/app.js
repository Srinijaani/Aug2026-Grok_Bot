const messagesEl = document.getElementById("messages");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const modeBadge = document.getElementById("mode-badge");

// Conversation history sent to the backend on each request (Chat Completions
// is stateless, so we resend the full history).
const history = [];

function addMessage(role, content, { error = false } = {}) {
  const wrap = document.createElement("div");
  wrap.className = `message message--${role === "user" ? "user" : "bot"}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "🧑" : "✦";

  const bubble = document.createElement("div");
  bubble.className = "bubble" + (error ? " error" : "");
  bubble.textContent = content;

  wrap.append(avatar, bubble);
  messagesEl.append(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}

function addTyping() {
  const wrap = document.createElement("div");
  wrap.className = "message message--bot";
  wrap.innerHTML =
    '<div class="avatar">✦</div><div class="bubble"><span class="typing"><span></span><span></span><span></span></span></div>';
  messagesEl.append(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

async function refreshMode() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (data.mode === "live") {
      modeBadge.textContent = `Live · ${data.model}`;
      modeBadge.className = "badge badge--live";
    } else {
      modeBadge.textContent = "Demo mode";
      modeBadge.className = "badge badge--demo";
    }
  } catch {
    modeBadge.textContent = "offline";
    modeBadge.className = "badge badge--muted";
  }
}

async function sendMessage(text) {
  history.push({ role: "user", content: text });
  addMessage("user", text);

  const typing = addTyping();
  sendBtn.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history }),
    });
    const data = await res.json();
    typing.remove();

    if (!res.ok) {
      addMessage("bot", data.error || "Something went wrong.", { error: true });
      return;
    }

    history.push({ role: "assistant", content: data.reply });
    addMessage("bot", data.reply);
  } catch (err) {
    typing.remove();
    addMessage("bot", `Network error: ${err.message}`, { error: true });
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  input.style.height = "auto";
  sendMessage(text);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

refreshMode();
input.focus();
