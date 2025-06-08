// DOM Elements
const weatherInfo = document.getElementById('weather-info');
const alertsList = document.getElementById('alerts-list');
const tasksList = document.getElementById('tasks-list');
const chatButton = document.getElementById('chat-button');
const chatContainer = document.getElementById('chat-container');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const chatClose = document.getElementById('chat-close');
const locationModal = new bootstrap.Modal(document.getElementById('locationModal'));
const locationForm = document.getElementById('location-form');
const useMyLocationBtn = document.getElementById('use-my-location');

// Application state
let isChatOpen = false;

// Global variables
let socket;
let streamElements = {};
let userLocation = {
    lat: null,
    lon: null,
    name: 'Unknown Location'
};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Initialize WebSocket connection first
    initializeSocket();
    
    // Check if location is already set
    const savedLocation = localStorage.getItem('userLocation');
    if (savedLocation) {
        userLocation = JSON.parse(savedLocation);
        initializeApp();
    } else {
        // Show location modal if location is not set
        locationModal.show();
    }
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize video containers
    initializeVideoContainers();
});

function initializeApp() {
    // Update UI with location
    updateLocationUI();
    
    // Load weather data
    loadWeatherData();
    
    // Start video streams
    if (socket && socket.connected) {
        socket.emit('start_streams');
    }
}

function initializeSocket() {
    console.log('Initializing WebSocket connection for chat...');
    
    // Connect to the Socket.IO server with reconnection settings
    socket = io({
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 20000,
        transports: ['websocket'],
        upgrade: false,
        forceNew: true,
        autoConnect: true
    });
    
    // Connection established
    socket.on('connect', () => {
        console.log('✅ Connected to chat server with ID:', socket.id);
        updateConnectionStatus(true);
        
        // Request initial data (alerts, tasks, etc.)
        console.log('Requesting initial data...');
        socket.emit('get_alerts');
        loadTasks();
    });
    
    // Handle connection errors
    socket.on('connect_error', (error) => {
        console.error('❌ Chat connection error:', error);
        updateConnectionStatus(false);
        
        // Try to reconnect after 5 seconds
        console.log('Attempting to reconnect in 5 seconds...');
        setTimeout(initializeSocket, 5000);
    });
    
    // Handle reconnection events
    socket.on('reconnect_attempt', () => {
        console.log('Attempting to reconnect to chat server...');
    });
    
    socket.on('reconnect_failed', () => {
        console.error('Failed to reconnect to chat server');
        updateConnectionStatus(false);
    });
    
    // Handle new alerts
    socket.on('new_alert', handleNewAlert);
    
    // Handle initial data
    socket.on('initial_data', handleInitialData);
}

// Handle video frames from server
function handleVideoFrame(data) {
    try {
        if (!data || !data.camera_id || !data.frame) {
            console.error('Invalid frame data received:', data);
            return;
        }

        const { camera_id, frame, timestamp, detections } = data;
        const frameId = performance.now().toFixed(2);
        
        // Log frame received (throttled to avoid console spam)
        if (Math.random() < 0.05) { // Log approximately 5% of frames for better debugging
            console.log(`[${frameId}] Received frame from ${camera_id} at ${timestamp || new Date().toISOString()}`);
        }
        
        // Get or create the video container
        let container = document.getElementById(`video-${camera_id}`);
        if (!container) {
            console.log(`[${frameId}] Creating new container for camera: ${camera_id}`);
            container = createVideoElement(camera_id);
            if (!container) {
                console.error(`[${frameId}] Failed to create container for camera: ${camera_id}`);
                return;
            }
        }
        
        // Find or create the image element
        let img = container.querySelector('img.video-feed');
        if (!img) {
            img = document.createElement('img');
            img.className = 'video-feed w-100';
            img.alt = `Live feed from ${camera_id}`;
            img.style.display = 'block';
            img.style.width = '100%';
            img.style.height = 'auto';
            img.style.objectFit = 'contain';
            img.style.backgroundColor = '#000';
            container.appendChild(img);
        }
        
        // Create a new Image object to preload the frame
        const tempImg = new Image();
        
        // Set up error handling first
        tempImg.onerror = (error) => {
            console.error(`[${frameId}] Failed to load frame for ${camera_id}:`, error);
            img.style.display = 'none';
        };
        
        tempImg.onload = () => {
            try {
                // Use requestAnimationFrame for smoother updates
                requestAnimationFrame(() => {
                    img.src = tempImg.src;
                    img.style.display = 'block';
                    
                    // Update timestamp if element exists
                    const timestampEl = container.querySelector('.camera-timestamp');
                    if (timestampEl) {
                        timestampEl.textContent = timestamp || new Date().toLocaleTimeString();
                    }
                    
                    // Log successful frame update
                    if (Math.random() < 0.05) {
                        console.log(`[${frameId}] Updated frame for ${camera_id}`);
                    }
                });
                
                // Update active cameras list if needed
                if (!activeCameras.has(camera_id)) {
                    activeCameras.add(camera_id);
                    updateActiveCameras();
                }
                
            } catch (error) {
                console.error(`[${frameId}] Error in frame update for ${camera_id}:`, error);
            }
        };
        
        // Start loading the image
        try {
            tempImg.src = `data:image/jpeg;base64,${frame}`;
        } catch (error) {
            console.error(`[${frameId}] Error setting image source for ${camera_id}:`, error);
        }
        
    } catch (error) {
        console.error('Error in handleVideoFrame:', error);
    }
}

// Initialize video containers for all cameras
function initializeVideoContainers() {
    const videoGrid = document.getElementById('video-grid');
    if (!videoGrid) return;
    
    // Clear existing containers
    videoGrid.innerHTML = '';
    
    // Create a container for each camera
    Object.keys(VIDEO_SOURCES).forEach(cameraId => {
        const container = document.createElement('div');
        container.className = 'col-md-6 col-lg-4 mb-4';
        container.innerHTML = `
            <div class="card h-100">
                <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
                    <span>${cameraId}</span>
                    <span class="badge bg-success">Live</span>
                </div>
                <div class="camera-container" id="video-${cameraId}">
                    <div class="camera-overlay">
                        <div class="camera-timestamp">Connecting...</div>
                    </div>
                </div>
            </div>
        `;
        videoGrid.appendChild(container);
    });
}

// Create a new video element
function createVideoElement(cameraId) {
    const container = document.getElementById(`video-${cameraId}`);
    if (!container) return null;
    
    // Store reference to the container
    streamElements[cameraId] = container;
    return container;
}

// Handle new alerts
function handleNewAlert(alert) {
    // Play alert sound for high severity alerts
    if (alert.severity === 'high') {
        playAlertSound();
    }
    
    // Add to alerts list
    addAlertToUI(alert);
    
    // Update notifications badge
    updateNotificationBadge(1);
}

// Add alert to the UI
function addAlertToUI(alert) {
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${getAlertClass(alert.severity)} alert-dismissible fade show`;
    alertElement.role = 'alert';
    
    const timeAgo = timeSince(new Date(alert.timestamp));
    
    alertElement.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <strong>${alert.message}</strong>
                <div class="text-muted small">${timeAgo} ago</div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const alertsContainer = document.getElementById('alerts-container');
    if (alertsContainer.firstChild) {
        alertsContainer.insertBefore(alertElement, alertsContainer.firstChild);
    } else {
        alertsContainer.appendChild(alertElement);
    }
    
    // Auto-remove alert after 1 hour
    setTimeout(() => {
        alertElement.remove();
    }, 3600000);
}

// Handle initial data from server
function handleInitialData(data) {
    // Update active cameras
    data.cameras.forEach(camId => activeCameras.add(camId));
    updateActiveCameras();
    
    // Load recent alerts
    if (data.alerts && data.alerts.length > 0) {
        data.alerts.reverse().forEach(alert => {
            addAlertToUI(alert);
        });
    }
}

// Helper function to get alert class based on severity
function getAlertClass(severity) {
    const classes = {
        'high': 'danger',
        'medium': 'warning',
        'low': 'info'
    };
    return classes[severity] || 'secondary';
}

// Play alert sound
function playAlertSound() {
    if (alertSound) {
        alertSound.play().catch(e => console.warn('Could not play alert sound:', e));
    }
}

// Update notification badge
function updateNotificationBadge(count = 0) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        const currentCount = parseInt(badge.textContent) || 0;
        badge.textContent = currentCount + count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    }
}

// Update connection status UI
function updateConnectionStatus(isConnected) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.textContent = isConnected ? 'Connected' : 'Disconnected';
        statusElement.className = isConnected ? 'text-success' : 'text-danger';
    }
}

// Update active cameras list
function updateActiveCameras() {
    const activeList = document.getElementById('active-cameras');
    if (activeList) {
        activeList.innerHTML = Array.from(activeCameras).map(cam => 
            `<li class="list-group-item d-flex justify-content-between align-items-center">
                ${cam}
                <span class="badge bg-success rounded-pill">Live</span>
            </li>`
        ).join('');
    }
}

// Helper function to format time since
function timeSince(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    let interval = Math.floor(seconds / 31536000);
    if (interval >= 1) return interval + ' year' + (interval === 1 ? '' : 's');
    
    interval = Math.floor(seconds / 2592000);
    if (interval >= 1) return interval + ' month' + (interval === 1 ? '' : 's');
    
    interval = Math.floor(seconds / 86400);
    if (interval >= 1) return interval + ' day' + (interval === 1 ? '' : 's');
    
    interval = Math.floor(seconds / 3600);
    if (interval >= 1) return interval + ' hour' + (interval === 1 ? '' : 's');
    
    interval = Math.floor(seconds / 60);
    if (interval >= 1) return interval + ' minute' + (interval === 1 ? '' : 's');
    
    return Math.floor(seconds) + ' second' + (seconds === 1 ? '' : 's');
}

// Setup event listeners
function setupEventListeners() {
    // Chat button click
    chatButton.addEventListener('click', toggleChat);
    
    // Close chat button
    chatClose.addEventListener('click', toggleChat);
    
    // Send message button click
    sendButton.addEventListener('click', sendMessage);
    
    // Send message on Enter key (but allow Shift+Enter for new line)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-resize textarea as user types
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });
    
    // Close chat when clicking outside
    document.addEventListener('click', (e) => {
        if (isChatOpen && 
            !chatContainer.contains(e.target) && 
            !chatButton.contains(e.target)) {
            toggleChat();
        }
    });
    
    // Prevent chat close when clicking inside chat
    chatContainer.addEventListener('click', (e) => {
        e.stopPropagation();
    });
    
    // Location form submission
    locationForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const locationInput = document.getElementById('location-input');
        if (locationInput.value.trim()) {
            geocodeLocation(locationInput.value);
        }
    });
    
    // Use my location button
    useMyLocationBtn.addEventListener('click', getCurrentLocation);
}

// Location functions
function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation.lat = position.coords.latitude;
                userLocation.lon = position.coords.longitude;
                
                // Get location name using reverse geocoding
                fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${userLocation.lat}&lon=${userLocation.lon}`)
                    .then(response => response.json())
                    .then(data => {
                        userLocation.name = data.display_name || 'Current Location';
                        saveLocationAndInitialize();
                    })
                    .catch(() => {
                        userLocation.name = 'Current Location';
                        saveLocationAndInitialize();
                    });
            },
            (error) => {
                console.error('Error getting location:', error);
                alert('Unable to retrieve your location. Please enter it manually.');
            }
        );
    } else {
        alert('Geolocation is not supported by your browser. Please enter your location manually.');
    }
}

function geocodeLocation(locationName) {
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationName)}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                userLocation.lat = parseFloat(data[0].lat);
                userLocation.lon = parseFloat(data[0].lon);
                userLocation.name = data[0].display_name;
                saveLocationAndInitialize();
            } else {
                alert('Location not found. Please try a different location.');
            }
        })
        .catch(error => {
            console.error('Error geocoding location:', error);
            alert('Error finding location. Please try again.');
        });
}

function saveLocationAndInitialize() {
    localStorage.setItem('userLocation', JSON.stringify(userLocation));
    locationModal.hide();
    initializeApp();
}

function updateLocationUI() {
    const locationElement = document.getElementById('current-location');
    if (locationElement) {
        locationElement.textContent = userLocation.name;
    }
}

// Weather functions
async function loadWeatherData() {
    if (!userLocation.lat || !userLocation.lon) return;
    try {
        // Fetch weather data
        const response = await fetch('/api/weather', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: userLocation.lat, lon: userLocation.lon })
        });
        const weatherData = await response.json();
        if (response.ok) {
            updateWeatherUI(weatherData);
            // Fetch farm advice from Groq
            loadFarmAdvice(weatherData);
        } else {
            console.error('Failed to load weather data:', weatherData);
        }
    } catch (error) {
        console.error('Error fetching weather data:', error);
    }
}

async function loadFarmAdvice(weatherData) {
    try {
        const locationName = userLocation.name || `${userLocation.lat},${userLocation.lon}`;
        const response = await fetch('/api/suggestions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weather: weatherData, location: locationName })
        });
        const data = await response.json();
        if (response.ok && data.advice) {
            updateFarmAdviceUI(data.advice);
        } else {
            updateFarmAdviceUI('No advice available.');
        }
    } catch (error) {
        console.error('Error fetching farm advice:', error);
        updateFarmAdviceUI('Error fetching advice.');
    }
}

function updateWeatherUI(weather) {
    if (!weather) return;
    const weatherHtml = `
        <div class="weather-card">
            <div class="weather-main">
                <div class="weather-temp">${Math.round(weather.temp)}°C</div>
                <div class="weather-desc">${weather.description}</div>
            </div>
            <div class="weather-details">
                <div><i class="bi bi-droplet"></i> ${weather.humidity}%</div>
                <div><i class="bi bi-wind"></i> ${weather.wind_speed} m/s</div>
            </div>
            <div id="farm-advice" class="mt-3 text-success small">
                <em>Loading farm advice...</em>
            </div>
        </div>
    `;
    if (weatherInfo) {
        weatherInfo.innerHTML = weatherHtml;
    }
}

function updateFarmAdviceUI(advice) {
    const adviceDiv = document.getElementById('farm-advice');
    if (adviceDiv) {
        adviceDiv.innerHTML = `<strong>Farm Advice:</strong> <br>${advice}`;
    }
}

// Alert functions
async function loadAlerts() {
    try {
        const response = await fetch('/api/alerts?limit=5');
        const alerts = await response.json();
        
        if (response.ok) {
            updateAlertsUI(alerts);
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

function updateAlertsUI(alerts) {
    if (!alertsList) return;
    
    alertsList.innerHTML = alerts.length > 0 
        ? alerts.map(alert => `
            <div class="alert alert-${alert.type} alert-dismissible fade show" role="alert">
                <strong>${alert.timestamp}</strong> - ${alert.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `).join('')
        : '<div class="text-muted">No recent alerts</div>';
}

function addAlertToUI(alert) {
    if (!alertsList) return;
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${alert.type} alert-dismissible fade show`;
    alertElement.role = 'alert';
    alertElement.innerHTML = `
        <strong>${alert.timestamp}</strong> - ${alert.message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsList.insertBefore(alertElement, alertsList.firstChild);
    
    // Remove oldest alert if more than 5
    if (alertsList.children.length > 5) {
        alertsList.removeChild(alertsList.lastChild);
    }
}

// Task functions
function loadTasks() {
    // In a real app, this would fetch tasks from the server
    const tasks = [
        { id: 1, title: 'Irrigate Field A', time: 'Tomorrow 6:00 AM', priority: 'high' },
        { id: 2, title: 'Check soil moisture', time: 'Today 4:00 PM', priority: 'medium' },
        { id: 3, title: 'Harvest tomatoes', time: 'Friday', priority: 'low' }
    ];
    
    updateTasksUI(tasks);
}

function updateTasksUI(tasks) {
    if (!tasksList) return;
    
    tasksList.innerHTML = tasks.length > 0
        ? tasks.map(task => `
            <div class="task-item ${task.priority}">
                <div class="task-title">${task.title}</div>
                <div class="task-time">${task.time}</div>
            </div>
        `).join('')
        : '<div class="text-muted">No upcoming tasks</div>';
}

// Chat functions
function toggleChat() {
    isChatOpen = !isChatOpen;
    
    if (isChatOpen) {
        document.body.classList.add('chat-open');
        chatContainer.classList.add('show');
        chatInput.focus();
        // Auto-scroll to bottom when opening
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 10);
    } else {
        document.body.classList.remove('chat-open');
        chatContainer.classList.remove('show');
    }
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Clear input and reset height
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Add user message to chat
    addMessage('user', message);
    
    // Show typing indicator
    const typingIndicator = addMessage('assistant', 'Typing...');
    
    try {
        // Send message to server
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        typingIndicator.remove();
        
        if (response.ok) {
            addMessage('assistant', data.response, data.timestamp);
        } else {
            throw new Error(data.error || 'Failed to get response');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        // Remove typing indicator on error
        if (typingIndicator && typingIndicator.remove) {
            typingIndicator.remove();
        }
        addMessage('system', 'Sorry, there was an error processing your message.');
    }
}

function addMessage(sender, text, timestamp = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    // Format timestamp
    const time = timestamp || new Date().toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true
    });
    
    // Sanitize text to prevent XSS
    const sanitizedText = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    // Convert URLs to clickable links
    const linkedText = sanitizedText.replace(
        /(https?:\/\/[^\s]+)/g, 
        url => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`
    );
    
    // Convert line breaks to <br> tags
    const formattedText = linkedText.replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = `
        <div class="message-content">${formattedText}</div>
        <div class="message-time">${time}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    
    // Smooth scroll to the new message
    messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
    
    return messageDiv;
}

// Helper functions
function createVideoElement(streamId) {
    const videoWrapper = document.createElement('div');
    videoWrapper.className = 'video-wrapper';
    videoWrapper.id = `video-${streamId}`;
    
    const videoTitle = document.createElement('div');
    videoTitle.className = 'video-title';
    videoTitle.textContent = `Camera ${streamId.split('_')[1]}`;
    
    const img = document.createElement('img');
    img.alt = `Camera Feed ${streamId}`;
    img.className = 'video-feed';
    
    videoWrapper.appendChild(videoTitle);
    videoWrapper.appendChild(img);
    videoContainer.appendChild(videoWrapper);
    
    streamElements[streamId] = img;
}

function showNotification(message, type = 'info') {
    // Check if browser supports notifications
    if (!('Notification' in window)) {
        console.log('This browser does not support desktop notification');
        return;
    }
    
    // Check if notification permissions are already granted
    if (Notification.permission === 'granted') {
        // If it's okay, create a notification
        new Notification('Farm Alert', {
            body: message,
            icon: `/static/images/alert-${type}.png`
        });
    }
    // Otherwise, ask for permission
    else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification('Farm Alert', {
                    body: message,
                    icon: `/static/images/alert-${type}.png`
                });
            }
        });
    }
}

// Request notification permission on page load
if ('Notification' in window) {
    Notification.requestPermission();
}
