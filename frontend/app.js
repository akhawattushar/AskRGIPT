// Campus Compass Frontend
const API_BASE_URL = 'http://localhost:2029';

const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const citationsPanel = document.getElementById('citationsPanel');
const citationsList = document.getElementById('citationsList');

// Initialize
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendButton.addEventListener('click', sendMessage);

// Check API health on load
checkHealth();

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        console.log('API Health:', data);
    } catch (error) {
        console.error('API Health check failed:', error);
        addMessage('bot', '⚠️ Unable to connect to the API. Please ensure the backend is running.', true);
    }
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';
    
    // Disable input while processing
    messageInput.disabled = true;
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="loading"></span>';

    try {
        // Send request to API
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Add bot response
        let botMessage = data.answer;
        
        // Add function indicator if function was used
        if (data.used_function) {
            botMessage += `<div class="function-indicator">🔧 Used: ${data.intent || 'function'}</div>`;
        }
        
        // Add citations if available
        if (data.citations && data.citations.length > 0) {
            botMessage += '<div class="citations">';
            botMessage += '<strong>📚 Sources:</strong><br>';
            data.citations.forEach((citation, index) => {
                botMessage += `<div class="citation-item" onclick="showCitation(${index})">`;
                botMessage += `  <strong>${citation.source}</strong>`;
                if (citation.page) {
                    botMessage += ` - Page ${citation.page}`;
                }
                botMessage += `</div>`;
            });
            botMessage += '</div>';
        }
        
        addMessage('bot', botMessage);
        
        // Update citations panel
        if (data.citations && data.citations.length > 0) {
            updateCitationsPanel(data.citations);
        } else {
            citationsPanel.style.display = 'none';
        }
        
        // Show warning if not grounded
        if (!data.is_grounded) {
            addMessage('bot', '⚠️ Note: This answer may not be fully grounded in the source documents.', true);
        }

    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('bot', '❌ Sorry, I encountered an error. Please try again.', true);
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        sendButton.innerHTML = 'Send';
        messageInput.focus();
    }
}

function addMessage(sender, content, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    if (isError) {
        contentDiv.classList.add('error-message');
    }
    contentDiv.innerHTML = content;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function updateCitationsPanel(citations) {
    citationsPanel.style.display = 'block';
    citationsList.innerHTML = '';
    
    citations.forEach((citation, index) => {
        const citationCard = document.createElement('div');
        citationCard.className = 'citation-card';
        
        let html = `<strong>${citation.source}</strong>`;
        if (citation.category) {
            html += ` <span style="color: #666; font-size: 0.9em;">(${citation.category})</span>`;
        }
        if (citation.page) {
            html += `<div class="page">Page ${citation.page}</div>`;
        }
        if (citation.text_preview) {
            html += `<div style="margin-top: 8px; font-size: 0.9em; color: #666;">${citation.text_preview}</div>`;
        }
        
        citationCard.innerHTML = html;
        citationsList.appendChild(citationCard);
    });
}

function showCitation(index) {
    // Scroll to citations panel
    citationsPanel.scrollIntoView({ behavior: 'smooth' });
}

// Example queries for quick testing
const exampleQueries = [
    "What are the library rules?",
    "What is the fee structure?",
    "When is the examination date?",
    "Summarize the academic policy"
];

// Add example queries as suggestions (optional)
function addExampleQueries() {
    // Could add clickable examples here
}

