import React, { useState, useEffect, useRef } from "react";
import { Client } from "@gradio/client";
import ReactMarkdown from "react-markdown";
import "./Chatbot.css";

/*
  Notes:
  - This file preserves history, timestamps, loading UI, scroll, and error handling.
  - To switch backend source, edit GRADIO_CONNECT_MODE below.
    - "space" uses Client.connect("username/project")
    - "url" uses Client.connect("https://host:port") (useful for local/Codespaces forwarded ports)
*/

const GRADIO_CONNECT_MODE = "auto"; // "auto" | "space" | "url"
const GRADIO_SPACE_NAME = "akhawattushar/askrgipt"; // change to your space if needed
// If you want to force a URL (local or forwarded), set it here (example: https://your-codespace-7860.app.github.dev)
const GRADIO_URL = ""; // example: "http://127.0.0.1:7860" or "https://friendly-fishstick-7860.app.github.dev"

export default function Chatbot() {
  const [messages, setMessages] = useState([
    {
      id: Date.now(),
      type: "bot",
      text: "Hi! 👋 I'm **AskRGIPT**. Ask me anything about RGIPT!",
      ts: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);
  const messagesEndRef = useRef(null);

  // scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // load saved history from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem("askrgipt_history");
      if (saved) setHistory(JSON.parse(saved));
    } catch (e) {
      console.warn("Failed to load history:", e);
    }
  }, []);

  // helper to persist history (keep last 20)
  const persistHistory = (arr) => {
    const clipped = arr.slice(-20);
    setHistory(clipped);
    try {
      localStorage.setItem("askrgipt_history", JSON.stringify(clipped));
    } catch (e) {
      console.warn("Failed to save history:", e);
    }
  };

  // build the client connection depending on chosen mode
  const connectClient = async () => {
    if (GRADIO_CONNECT_MODE === "space") {
      return await Client.connect(GRADIO_SPACE_NAME);
    } else if (GRADIO_CONNECT_MODE === "url") {
      if (!GRADIO_URL) throw new Error("GRADIO_URL is empty.");
      return await Client.connect(GRADIO_URL);
    } else {
      // auto: try space first, fallback to URL if provided
      try {
        return await Client.connect(GRADIO_SPACE_NAME);
      } catch (e) {
        if (GRADIO_URL) return await Client.connect(GRADIO_URL);
        throw e;
      }
    }
  };

  // send message to backend and update UI
  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMessage = input.trim();
    const userEntry = {
      id: Date.now() + Math.random(),
      type: "user",
      text: userMessage,
      ts: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userEntry]);
    setInput("");
    setLoading(true);

    // update and persist history
    const newHistory = [...history, { question: userMessage, ts: new Date().toISOString() }];
    persistHistory(newHistory);

    try {
      const client = await connectClient();

      // Gradio interface defined with single text input: send it appropriately.
      // We use named payload first; fallback to list if the server expects that.
      let result;
      try {
        result = await client.predict("/predict", { question: userMessage });
      } catch (err) {
        // some Gradio setups expect array form: data: [userMessage]
        result = await client.predict("/predict", [userMessage]);
      }

      // result.data can be string or array. Normalize:
      let botReply = "";
      if (!result) {
        botReply = "No response from server.";
      } else if (Array.isArray(result.data)) {
        botReply = result.data[0] ?? String(result.data);
      } else if (typeof result.data === "string") {
        botReply = result.data;
      } else if (result.data && result.data.output_text) {
        botReply = result.data.output_text;
      } else {
        botReply = JSON.stringify(result.data).slice(0, 1000);
      }

      const botEntry = { id: Date.now() + Math.random(), type: "bot", text: botReply, ts: new Date().toISOString() };
      setMessages((prev) => [...prev, botEntry]);
    } catch (e) {
      console.error("Send error:", e);
      const errEntry = { id: Date.now() + Math.random(), type: "bot", text: "❌ Error: Could not connect to backend. Check console.", ts: new Date().toISOString() };
      setMessages((prev) => [...prev, errEntry]);
    } finally {
      setLoading(false);
    }
  };

  const loadHistoryItem = (question) => {
    setInput(question);
    setShowHistory(false);
  };

  const clearHistory = () => {
    setHistory([]);
    try {
      localStorage.removeItem("askrgipt_history");
    } catch (e) {}
  };

  // helper to render a message item
  const renderMessage = (msg) => {
    return (
      <div className={`message ${msg.type}`} key={msg.id}>
        <div className="message-body">
          <ReactMarkdown>{msg.text}</ReactMarkdown>
        </div>
        <div className="message-meta">{new Date(msg.ts).toLocaleTimeString()}</div>
      </div>
    );
  };

  return (
    <div className="chatbot">
      <div className="header">
        <div>
          <h1>RGIPT Chatbot</h1>
          <p>Your AI Assistant for RGIPT</p>
        </div>
        <div>
          <button className="history-btn" onClick={() => setShowHistory(!showHistory)}>📜 History</button>
        </div>
      </div>

      {showHistory && (
        <div className="history-panel">
          <div className="history-header">
            <h3>Recent Questions</h3>
            <div>
              <button onClick={() => { navigator.clipboard?.writeText(JSON.stringify(history.slice(-10))); }}>Copy</button>
              <button onClick={clearHistory}>Clear</button>
            </div>
          </div>
          {history.length === 0 ? (
            <p className="empty-history">No history yet</p>
          ) : (
            history.slice().reverse().map((h, idx) => (
              <div key={idx} className="history-item" onClick={() => loadHistoryItem(h.question)}>
                <div className="history-q">💬 {h.question}</div>
                <div className="history-ts">{new Date(h.ts).toLocaleString()}</div>
              </div>
            ))
          )}
        </div>
      )}

      <div className="messages" role="log" aria-live="polite">
        {messages.map(renderMessage)}
        {loading && (
          <div className="message bot loading">
            <div className="message-body">Thinking<span className="dots">...</span></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") sendMessage(); }}
          placeholder="Ask about admissions, exams, library rules..."
          aria-label="Message input"
        />
        <button onClick={sendMessage} disabled={loading}>Send</button>
      </div>
    </div>
  );
}
