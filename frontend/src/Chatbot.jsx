import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './Chatbot.css';

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { type: 'bot', text: 'Hi! 👋 I\'m **AskRGIPT**. Ask me anything about RGIPT!' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('askrgipt_history');
    if (saved) {
      setHistory(JSON.parse(saved));
    }
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setMessages([...messages, { type: 'user', text: userMessage }]);
    setInput('');
    setLoading(true);

    // Save to history
    const newHistory = [...history, { question: userMessage, timestamp: new Date().toISOString() }];
    setHistory(newHistory.slice(-10));
    localStorage.setItem('askrgipt_history', JSON.stringify(newHistory.slice(-10)));

    try {
      // ✅ FIXED: Connect to HF Spaces backend
      const response = await fetch('https://akhawattushar-askrgipt.hf.space/run/ask_rgipt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: [userMessage] })
      });

      if (!response.ok) throw new Error('API Error');
      const data = await response.json();

      setMessages(prev => [...prev, { type: 'bot', text: data[0] }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'bot',
        text: '❌ Error: Could not reach API. Make sure backend is running!'
      }]);
    }
    setLoading(false);
  };

  const loadHistoryItem = (question) => {
    setInput(question);
    setShowHistory(false);
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('askrgipt_history');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chatbot-container">
      {/* Header */}
      <div className="chatbot-header">
        <div className="header-content">
          <h1>🎓 AskRGIPT</h1>
          <p>Your AI Assistant for RGIPT</p>
        </div>
        <button
          className="history-btn"
          onClick={() => setShowHistory(!showHistory)}
        >
          📋 History
        </button>
      </div>

      {/* History Sidebar */}
      {showHistory && (
        <div className="history-sidebar">
          <h3>Recent Questions</h3>
          <div className="history-list">
            {history.length > 0 ? (
              history.map((item, idx) => (
                <div
                  key={idx}
                  className="history-item"
                  onClick={() => loadHistoryItem(item.question)}
                >
                  <p>{item.question.substring(0, 50)}...</p>
                  <span className="timestamp">
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))
            ) : (
              <p className="no-history">No history yet</p>
            )}
          </div>
          <button className="clear-btn" onClick={clearHistory}>
            Clear History
          </button>
        </div>
      )}

      {/* Messages Container */}
      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            <div className="message-content">
              <ReactMarkdown>{msg.text}</ReactMarkdown>
            </div>
          </div>
        ))}
        {loading && (
          <div className="message bot">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about admissions, exams, library rules..."
          className="input-field"
          rows="3"
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="send-btn"
        >
          ➤ Send
        </button>
      </div>
    </div>
  );
}
