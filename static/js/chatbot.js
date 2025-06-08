document.addEventListener('DOMContentLoaded', function() {
    const chatbotIcon = document.getElementById('chatbot-icon');
    const chatbotOverlay = document.getElementById('chatbot-overlay');
    const closeChatbotBtn = document.getElementById('close-chatbot');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const voiceBtn = document.getElementById('voice-btn');
    const chatMessages = document.getElementById('chat-messages');

    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let audioPlayer = new Audio();

    // Event Listeners for Chatbot Overlay
    chatbotIcon.addEventListener('click', () => {
        chatbotOverlay.classList.add('open');
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to bottom on open
    });

    closeChatbotBtn.addEventListener('click', () => {
        chatbotOverlay.classList.remove('open');
    });

    // Handle text input
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Handle voice input
    voiceBtn.addEventListener('click', toggleRecording);

    function addMessage(role, content, isStreaming = false) {
        let messageDiv;
        let messageContent;

        if (isStreaming) {
            const existingMessage = chatMessages.querySelector('.assistant-message:last-child');
            if (existingMessage) {
                // If streaming, update the text content of the existing assistant message
                existingMessage.querySelector('.message-content').textContent = content;
                chatMessages.scrollTop = chatMessages.scrollHeight;
                return; // Exit after updating
            }
        }

        // If not streaming, or if it's the first chunk of a streaming message (no existing message yet)
        messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message mb-2`;
        
        messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            addMessage('user', message);
            messageInput.value = '';
            
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => {
                const reader = response.body.getReader();
                let responseText = '';
                
                function readStream() {
                    return reader.read().then(({done, value}) => {
                        if (done) {
                            addMessage('assistant', responseText);
                            // Convert response to speech and play
                            fetch('/text-to-speech', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({ text: responseText })
                            })
                            .then(response => response.blob())
                            .then(blob => {
                                const audioUrl = URL.createObjectURL(blob);
                                audioPlayer.src = audioUrl;
                                audioPlayer.play();
                            })
                            .catch(error => console.error('Error playing audio:', error));
                            return;
                        }
                        responseText += new TextDecoder().decode(value);
                        addMessage('assistant', responseText, true); // Update streaming message
                        return readStream();
                    });
                }
                
                return readStream();
            })
            .catch(error => {
                console.error('Error:', error);
                addMessage('system', 'Error: Could not send message');
            });
        }
    }

    async function toggleRecording() {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' }); // Changed to wav for Sarvam
                    const formData = new FormData();
                    formData.append('audio', audioBlob);

                    try {
                        const response = await fetch('/speech-to-text', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await response.json();
                        if (data.text) {
                            messageInput.value = data.text;
                            sendMessage();
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        addMessage('system', 'Error: Could not process voice input');
                    }
                };

                mediaRecorder.start();
                isRecording = true;
                voiceBtn.classList.add('btn-danger');
                voiceBtn.textContent = 'Stop Recording'; // Update button text
            } catch (error) {
                console.error('Error accessing microphone:', error);
                addMessage('system', 'Error: Could not access microphone');
            }
        } else {
            mediaRecorder.stop();
            isRecording = false;
            voiceBtn.classList.remove('btn-danger');
            voiceBtn.textContent = ''; // Clear button text
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>'; // Restore icon
        }
    }

    // Initial welcome message
    if (chatMessages.children.length === 0) {
        addMessage('assistant', 'Hello! I am your agricultural assistant. How can I help you today?');
    }
}); 