import React, { useState, useEffect, useRef } from "react";
import { Client } from "@gradio/client";
import ReactMarkdown from "react-markdown";
import "./Chatbot.css";

const GRADIO_CONNECT_MODE = "auto";
const GRADIO_SPACE_NAME = "akhawattushar/askrgipt";
const GRADIO_URL = "";

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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("askrgipt_history");
      if (saved) setHistory(JSON.parse(saved));
    } catch (e) {
      console.warn("Failed to load history:", e);
    }
  }, []);

  const persistHistory = (arr) => {
    const clipped = arr.slice(-20);
    setHistory(clipped);
    try {
      localStorage.setItem("askrgipt_history", JSON.stringify(clipped));
    } catch (e) {
      console.warn("Failed to save history:", e);
    }
  };

  const connectClient = async () => {
    if (GRADIO_CONNECT_MODE === "space") {
      return await Client.connect(GRADIO_SPACE_NAME);
    } else if (GRADIO_CONNECT_MODE === "url") {
      if (!GRADIO_URL) throw new Error("GRADIO_URL is empty.");
      return await Client.connect(GRADIO_URL);
    } else {
      try {
        return await Client.connect(GRADIO_SPACE_NAME);
      } catch (e) {
        if (GRADIO_URL) return await Client.connect(GRADIO_URL);
        throw e;
      }
    }
  };

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

    const newHistory = [
      ...history,
      { question: userMessage, ts: new Date().toISOString() },
    ];
    persistHistory(newHistory);

    try {
      const client = await connectClient();
      let result;
      try {
        result = await client.predict("/predict", { question: userMessage });
      } catch (err) {
        result = await client.predict("/predict", [userMessage]);
      }

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
        botReply = JSON.stringify(result.data).slice(0, 2000);
      }

      const botEntry = {
        id: Date.now() + Math.random(),
        type: "bot",
        text: botReply,
        ts: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, botEntry]);
    } catch (e) {
      console.error("Send error:", e);
      const errEntry = {
        id: Date.now() + Math.random(),
        type: "bot",
        text: "❌ Error: Could not connect to backend. Check console.",
        ts: new Date().toISOString(),
      };
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

  const renderMessage = (msg) => {
    return (
      <div className={`message ${msg.type}`} key={msg.id}>
        <div className="text">
          <ReactMarkdown>{msg.text}</ReactMarkdown>
        </div>
        <div className="message-meta">{new Date(msg.ts).toLocaleTimeString()}</div>
      </div>
    );
  };

  return (
    <div className="chatbot">
      <div className="header">
        {/* MODIFIED HEADER START */}
        <div className="title-area">
          {/* Using an emoji as a placeholder for the logo */}
          <span className="app-logo">🎓</span> 
          <h1>AskRGIPT</h1> {/* Changed title */}
          <p>Your AI Assistant for RGIPT</p>
        </div>
        {/* MODIFIED HEADER END */}
        <div>
          <button
            className="history-btn"
            onClick={() => setShowHistory(!showHistory)}
          >
            📜 History
          </button>
        </div>
      </div>

      {showHistory && (
        <div className="history-panel">
          <div className="history-header">
            <h3>Recent Questions</h3>
            <div>
              <button
                onClick={() => {
                  navigator.clipboard?.writeText(JSON.stringify(history.slice(-10)));
                }}
              >
                Copy
              </button>
              <button onClick={clearHistory}>Clear</button>
            </div>
          </div>
          {history.length === 0 ? (
            <p className="empty-history">No history yet</p>
          ) : (
            history
              .slice()
              .reverse()
              .map((h, idx) => (
                <div
                  key={idx}
                  className="history-item"
                  onClick={() => loadHistoryItem(h.question)}
                >
                  <div>💬 {h.question}</div>
                  <div className="history-ts">
                    {new Date(h.ts).toLocaleString()}
                  </div>
                </div>
              ))
          )}
        </div>
      )}

      <div className="messages" role="log" aria-live="polite">
        {messages.map(renderMessage)}
        {loading && (
          <div className="message bot loading">
            <div className="text">
              Thinking<span className="loading-dots"><span></span><span></span><span></span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") sendMessage();
          }}
          placeholder="Ask about admissions, exams, library rules..."
          aria-label="Message input"
        />
        <button onClick={sendMessage} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}