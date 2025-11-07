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
    setHistory(newHistory.slice(-10)); // Keep last 10
    localStorage.setItem('askrgipt_history', JSON.stringify(newHistory.slice(-10)));

    try {
      const response = await fetch('https://akhawattushar-askrgipt.hf.space/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data: [userMessage] })
      });

      if (!response.ok) {
        throw new Error('Backend response error');
      }

      const data = await response.json();
      setMessages(prev => [...prev, {
        type: 'bot',
        text: data.data[0] || 'Sorry, I didn\'t get that. Could you rephrase?'
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'bot',
        text: '❌ Error: Could not connect to backend. Please try again later!'
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

  return (
    <div className="chatbot">
      <div className="header">
        <div>
          <h1>RGIPT Chatbot</h1>
          <p>Your AI Assistant for RGIPT</p>
        </div>
        <button className="history-btn" onClick={() => setShowHistory(!showHistory)}>
          📜 History
        </button>
      </div>

      {showHistory && (
        <div className="history-panel">
          <div className="history-header">
            <h3>Recent Questions</h3>
            <button onClick={clearHistory}>Clear All</button>
          </div>
          {history.length === 0 ? (
            <p className="empty-history">No history yet</p>
          ) : (
            <div className="history-list">
              {history.map((item, idx) => (
                <div key={idx} className="history-item" onClick={() => loadHistoryItem(item.question)}>
                  <span>💬</span>
                  <span>{item.question}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            <div className="text">
              <ReactMarkdown>{msg.text}</ReactMarkdown>
            </div>
            {msg.sources && (
              <div className="sources">
                Sources: {msg.sources.join(', ')}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="message bot">
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
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
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message here..."
        />
        <button onClick={sendMessage} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}
