document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const fileInput = document.getElementById('fileInput');

    fileInput.addEventListener('change', handleFileUpload);
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    async function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        addMessage(`📄 Uploading ${file.name}...`, 'user');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.error) {
                addMessage(`🔴 Error: ${data.error}`, 'bot');
            } else {
                addMessage(formatAnalysis(data.analysis), 'bot');
            }
        } catch (error) {
            addMessage(`🔴 Connection Error: ${error.message}`, 'bot');
        }
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        userInput.value = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            if (data.error) {
                addMessage(`🔴 Error: ${data.error}`, 'bot');
            } else {
                addMessage(data.response, 'bot');
            }
        } catch (error) {
            addMessage(`🔴 Connection Error: ${error.message}`, 'bot');
        }
    }

    function addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatAnalysis(text) {
        return text
            .replace(/(\d+\.)/g, '<br><strong>$1</strong>')
            .replace(/(⚠️)/g, '<span class="warning">$1</span>')
            .replace(/(Recommended)/g, '<div class="recommendation">$1</div>')
            .replace(/(Diet Suggestions:)/g, '<div class="diet-header">$1</div>');
    }
});

// Update the formatAnalysis function in script.js
function formatAnalysis(text) {
    // Convert markdown-like formatting to HTML
    let formatted = text
        .replace(/\*\*(.*?)\*\*/g, '<h3 class="section-title">$1</h3>')
        .replace(/(\d+\.)\s+(.*?):/g, '<div class="section-header">$1 $2</div>')
        .replace(/- \*\*(.*?)\*\*/g, '<div class="sub-header">$1</div>')
        .replace(/- (.*?):/g, '<div class="parameter">$1</div>')
        .replace(/⚠️/g, '<span class="warning">⚠️</span>')
        .replace(/(\d+%\))/g, '<span class="percentage">$1</span>')
        .replace(/(For .*?:)/g, '<div class="diet-header">$1</div>')
        .replace(/-/g, '<li>')
        .replace(/(\n)/g, '</li>$1');

    // Wrap sections in containers
    formatted = formatted
        .replace(/<h3 class="section-title">(.*?)<\/h3>/g, 
            '<div class="analysis-section condition-section">$1</div>')
        .replace(/<div class="section-header">(.*?)<\/div>/g, 
            '<div class="section-container"><div class="section-header">$1</div>')
        .replace(/<\/li>/g, '</li></div>');

    return `<div class="medical-report">${formatted}</div>`;
}