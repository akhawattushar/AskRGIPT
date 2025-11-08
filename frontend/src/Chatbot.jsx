import React, { useState, useEffect, useRef } from "react";
import { Client } from "@gradio/client";
import ReactMarkdown from "react-markdown";
import "./Chatbot.css";

const GRADIO_CONNECT_MODE = "auto";
const GRADIO_SPACE_NAME = "akhawattushar/askrgipt";
const GRADIO_URL = "";

const examples = [
  "How many students per hostel room at RGIPT?",
  "What's the fee structure for BTech at RGIPT?",
  "What are the library hours at RGIPT?",
  "Tell me about RGIPT placement statistics",
  "Which branches are available at RGIPT?",
  "How to get admission in RGIPT?",
  "What is the campus location of RGIPT?"
];

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

  const handleExampleClick = (example) => {
    setInput(example);
  };

  const clearChat = () => {
    setMessages([
      {
        id: Date.now(),
        type: "bot",
        text: "Hi! 👋 I'm **AskRGIPT**. Ask me anything about RGIPT!",
        ts: new Date().toISOString(),
      },
    ]);
    setInput("");
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
        <div className="title-area">
          <span className="app-logo">🎓</span> 
          <h1>AskRGIPT</h1> 
          <p>Your AI Assistant for RGIPT</p>
        </div>
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

      {/* INPUT AREA + BUTTONS */}
      <div className="input-area" style={{position:"relative"}}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") sendMessage();
          }}
          placeholder="Ask about admissions, exams, library rules..."
          aria-label="Message input"
          style={{
            borderRadius: "25px",
            padding: "14px 20px",
            border: "none",
            width: "100%",
            fontSize: "1.1rem",
            boxShadow: "0 0 8px rgb(124 58 237 / 0.09)",
            outline: "none",
            background: "#312e81",
            color: "#fff",
            marginTop: 8,
          }}
        />
        <div style={{
          margin: "16px 0 0 0",
          display: "flex",
          flexWrap: "nowrap",
          gap: "12px",
          overflowX: "auto",
          paddingBottom: 8,
        }}>
          {examples.map((ex, i) => (
            <button
              key={i}
              onClick={() => handleExampleClick(ex)}
              style={{
                background: "linear-gradient(90deg,#7c3aed 40%,#6366f1 90%)",
                color: "white",
                border: "none",
                padding: "8px 18px",
                borderRadius: "25px",
                cursor: "pointer",
                fontSize: "1rem",
                fontWeight: 500,
                boxShadow: "0 2px 8px #7c3aed55",
                whiteSpace: "nowrap"
              }}
            >
              {ex}
            </button>
          ))}
        </div>
        <div style={{marginTop: "12px", display: "flex", gap: "12px"}}>
          <button onClick={sendMessage} disabled={loading}
            style={{
              flex: 1,
              background: "linear-gradient(90deg,#2563eb 40%,#10b981 90%)",
              color: "white",
              border: "none",
              borderRadius: "25px",
              padding: "12px 0",
              fontSize: "1.1rem",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer"
            }}>
            Send
          </button>
          <button onClick={clearChat}
            style={{
              background: "linear-gradient(90deg,#ef4444 40%,#f9fafb 90%)",
              color: "white",
              border: "none",
              borderRadius: "25px",
              padding: "12px 20px",
              fontSize: "1.1rem",
              fontWeight: 600,
              cursor: "pointer"
            }}>
            Clear Chat
          </button>
        </div>
      </div>
    </div>
  );
}
