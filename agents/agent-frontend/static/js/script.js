document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const fileInput = document.getElementById('file-input');
    const fileName = document.getElementById('file-name');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const clearChatButton = document.getElementById('clear-chat');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // Auto-resize the message input as the user types
    messageInput.addEventListener('input', function() {
        // Reset height to auto to properly calculate the new height
        this.style.height = 'auto';
        
        // Set new height based on scrollHeight, with a max height
        const newHeight = Math.min(this.scrollHeight, 150);
        this.style.height = `${newHeight}px`;
        
        // Enable/disable send button based on content
        validateSendButton();
    });
    
    // Handle file input change
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const file = this.files[0];
            
            // Check file size (max 16MB)
            if (file.size > 16 * 1024 * 1024) {
                alert('File is too large. Maximum file size is 16MB.');
                this.value = '';
                fileName.textContent = '';
                return;
            }
            
            // Display file name
            fileName.textContent = file.name;
        } else {
            fileName.textContent = '';
        }
        
        // Enable/disable send button based on content
        validateSendButton();
    });
    
    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const messageText = messageInput.value.trim();
        const file = fileInput.files[0];
        
        // Don't submit if no message and no file
        if (!messageText && !file) return;
        
        // Create FormData object
        const formData = new FormData();
        if (messageText) formData.append('message', messageText);
        if (file) formData.append('file', file);
        
        // Add user message to UI immediately
        if (messageText) {
            addMessageToUI('user', messageText);
        } else if (file) {
            addMessageToUI('user', `Uploading file: ${file.name}...`);
        }
        
        // Clear inputs
        messageInput.value = '';
        messageInput.style.height = '40px'; // Reset height
        fileInput.value = '';
        fileName.textContent = '';
        
        // Disable send button
        sendButton.disabled = true;
        
        // Show typing indicator
        showTypingIndicator();
        
        // Scroll to bottom of chat
        scrollToBottom();
        
        // Send message to server
        fetch('/send_message', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add agent response to UI
            addMessageToUI('agent', data.agent_response.text);
            
            // Scroll to bottom of chat
            scrollToBottom();
        })
        .catch(error => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add error message
            addErrorMessage('Sorry, there was a problem sending your message. Please try again.');
            console.error('Error:', error);
            
            // Scroll to bottom of chat
            scrollToBottom();
        });
    });
    
    // Clear chat history
    clearChatButton.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            fetch('/clear_chat', {
                method: 'POST',
            })
            .then(response => {
                if (response.ok) {
                    // Clear chat messages in UI
                    chatMessages.innerHTML = `
                        <div class="empty-chat">
                            <div class="welcome-message">
                                <i class="fas fa-robot welcome-icon"></i>
                                <h2>Welcome to AI Agent Chat</h2>
                                <p>Start a conversation or upload a file to get assistance from an agent.</p>
                            </div>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error clearing chat:', error);
            });
        }
    });
    
    // Validate the send button state
    function validateSendButton() {
        sendButton.disabled = messageInput.value.trim() === '' && fileInput.files.length === 0;
    }
    
    // Add message to UI
    function addMessageToUI(sender, text, fileUrl = null) {
        // Remove empty chat message if present
        const emptyChat = chatMessages.querySelector('.empty-chat');
        if (emptyChat) {
            chatMessages.removeChild(emptyChat);
        }
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // Get current time
        const now = new Date();
        const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Set message content - For agent messages, use the HTML directly to preserve markdown formatting
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-header">
                    <span class="sender-name">${sender === 'user' ? 'You' : 'AI Assistant'}</span>
                    <span class="timestamp">${time}</span>
                </div>
                <div class="message-text ${sender === 'agent' ? 'markdown-body' : ''}">${sender === 'user' ? formatMessageText(text) : text}</div>
                ${fileUrl ? `
                <div class="file-attachment">
                    <i class="fas fa-file-alt"></i>
                    <a href="${fileUrl}" target="_blank">View uploaded file</a>
                </div>
                ` : ''}
            </div>
        `;
        
        // Add to chat container with animation
        messageDiv.style.opacity = '0';
        chatMessages.appendChild(messageDiv);
        
        // Trigger reflow for animation
        void messageDiv.offsetWidth;
        messageDiv.style.opacity = '1';
    }
    
    // Format message text with line breaks and links
    function formatMessageText(text) {
        // Convert line breaks to <br>
        let formatted = text.replace(/\n/g, '<br>');
        
        // Convert URLs to clickable links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        formatted = formatted.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
        
        return formatted;
    }
    
    // Add error message
    function addErrorMessage(text) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = text;
        chatMessages.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode === chatMessages) {
                chatMessages.removeChild(errorDiv);
            }
        }, 5000);
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        typingIndicator.classList.remove('hidden');
    }
    
    // Hide typing indicator
    function hideTypingIndicator() {
        typingIndicator.classList.add('hidden');
    }
    
    // Scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Auto-grow the message input initially
    messageInput.dispatchEvent(new Event('input'));
    
    // Initialize scroll position
    scrollToBottom();
});