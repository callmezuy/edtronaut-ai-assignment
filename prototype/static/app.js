/**
 * Gucci CEO NPC Simulation — Frontend Logic
 * Handles SSE streaming, message rendering, state updates.
 */

// ============================================================
// STATE
// ============================================================
let currentSessionId = null;
let isStreaming = false;

// ============================================================
// SESSION MANAGEMENT
// ============================================================
async function createNewSession() {
    try {
        const resp = await fetch('/api/session/new', { method: 'POST' });
        const data = await resp.json();
        currentSessionId = data.session_id;

        // Update UI
        document.getElementById('sessionBadge').textContent = `Session: ${currentSessionId}`;
        document.getElementById('chatInput').disabled = false;
        document.getElementById('btnSend').disabled = false;

        // Reset chat
        clearChat();
        updateMetrics(data.state);

        console.log(`[Session] Created: ${currentSessionId}`);
    } catch (err) {
        console.error('[Session] Error:', err);
    }
}

// ============================================================
// MESSAGE SENDING
// ============================================================
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message || !currentSessionId || isStreaming) return;

    // Clear input
    input.value = '';
    autoResize(input);

    // Hide welcome message
    const welcome = document.getElementById('welcomeMessage');
    if (welcome) welcome.style.display = 'none';

    // Add user message to chat
    addMessage('user', message);

    // Show typing indicator
    showTyping(true);
    setStatus('thinking', 'Generating response...');
    isStreaming = true;
    updateSendButton();

    try {
        const response = await fetch(`/api/chat/${currentSessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_message: message }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';
        let messageEl = null;
        let safetyFlag = 'SAFE';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            const lines = text.split('\n');

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;

                try {
                    const data = JSON.parse(line.slice(6));

                    if (data.type === 'meta') {
                        // Update metrics
                        updateMetrics(data.state);
                        safetyFlag = data.safety_flag;

                        // Show supervisor indicator
                        if (data.state.supervisor_active) {
                            showSupervisor(true);
                            setTimeout(() => showSupervisor(false), 5000);
                        }

                        // Show safety flag
                        if (safetyFlag !== 'SAFE') {
                            showSafetyFlag(safetyFlag);
                        } else {
                            hideSafetyFlag();
                        }

                        // Hide typing, prepare message element
                        showTyping(false);
                        messageEl = addMessage('assistant', '', safetyFlag !== 'SAFE');

                    } else if (data.type === 'token') {
                        assistantMessage += data.content;
                        if (messageEl) {
                            const contentEl = messageEl.querySelector('.message-text');
                            if (contentEl) {
                                contentEl.innerHTML = formatMessage(assistantMessage);
                            }
                        }
                        scrollToBottom();

                    } else if (data.type === 'done') {
                        // Add safety flag badge if needed
                        if (safetyFlag !== 'SAFE' && messageEl) {
                            const flagEl = document.createElement('div');
                            flagEl.className = 'message-flag';
                            flagEl.textContent = `🛡️ ${safetyFlag}`;
                            messageEl.querySelector('.message-content').appendChild(flagEl);
                        }
                        setStatus('ready', 'Ready');
                    }
                } catch (e) {
                    // Skip malformed JSON
                }
            }
        }
    } catch (err) {
        console.error('[Chat] Error:', err);
        showTyping(false);
        addMessage('assistant', 'Connection error. Please try again.');
        setStatus('ready', 'Ready');
    }

    isStreaming = false;
    updateSendButton();
}

// ============================================================
// UI HELPERS
// ============================================================
function addMessage(role, content, isFlagged = false) {
    const container = document.getElementById('chatMessages');
    const typingEl = document.getElementById('typingIndicator');

    const msgEl = document.createElement('div');
    msgEl.className = `message ${role}${isFlagged ? ' flagged' : ''}`;

    const avatar = role === 'user' ? '👤' : '👔';

    msgEl.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-text">${formatMessage(content)}</div>
        </div>
    `;

    // Insert before typing indicator
    container.insertBefore(msgEl, typingEl);
    scrollToBottom();

    return msgEl;
}

function formatMessage(text) {
    // Bold: **text**
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic: *text*
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    return text;
}

function clearChat() {
    const container = document.getElementById('chatMessages');
    const messages = container.querySelectorAll('.message');
    messages.forEach(m => m.remove());

    const welcome = document.getElementById('welcomeMessage');
    if (welcome) welcome.style.display = '';

    hideSafetyFlag();
    showSupervisor(false);
}

function scrollToBottom() {
    const container = document.getElementById('chatMessages');
    container.scrollTop = container.scrollHeight;
}

function showTyping(show) {
    const el = document.getElementById('typingIndicator');
    el.classList.toggle('active', show);
    if (show) scrollToBottom();
}

function setStatus(type, text) {
    const dot = document.getElementById('statusDot');
    const label = document.getElementById('statusText');

    dot.className = 'status-dot';
    if (type === 'thinking') dot.classList.add('warning');
    else if (type === 'error') dot.classList.add('danger');

    label.textContent = text;
}

function updateMetrics(state) {
    if (!state) return;

    const trust = state.trust_level || 0;
    const frustration = state.frustration_level || 0;
    const turn = state.turn_count || 0;

    document.getElementById('trustValue').textContent = trust;
    document.getElementById('frustrationValue').textContent = frustration;
    document.getElementById('turnValue').textContent = turn;

    // Update bars (max scale = 5)
    const trustPct = Math.min((trust / 5) * 100, 100);
    const frustPct = Math.min((frustration / 5) * 100, 100);

    document.getElementById('trustBar').style.width = `${trustPct}%`;
    document.getElementById('frustrationBar').style.width = `${frustPct}%`;
}

function showSafetyFlag(flag) {
    const el = document.getElementById('safetyFlag');
    const text = document.getElementById('safetyFlagText');
    text.textContent = flag.replace('FLAGGED_', '').replace(/_/g, ' ');
    el.classList.add('active');
}

function hideSafetyFlag() {
    document.getElementById('safetyFlag').classList.remove('active');
}

function showSupervisor(show) {
    document.getElementById('supervisorIndicator').classList.toggle('active', show);
}

function updateSendButton() {
    const btn = document.getElementById('btnSend');
    const input = document.getElementById('chatInput');
    btn.disabled = isStreaming || !input.value.trim() || !currentSessionId;
}

// ============================================================
// INPUT HANDLERS
// ============================================================
function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    updateSendButton();
}

function insertMessage(text) {
    const input = document.getElementById('chatInput');
    input.value = text;
    autoResize(input);
    input.focus();
}

function insertAndSend(text) {
    if (!currentSessionId) {
        // Auto-create session first
        createNewSession().then(() => {
            setTimeout(() => {
                const input = document.getElementById('chatInput');
                input.value = text;
                autoResize(input);
                sendMessage();
            }, 300);
        });
    } else {
        const input = document.getElementById('chatInput');
        input.value = text;
        autoResize(input);
        sendMessage();
    }
}

// ============================================================
// INPUT MONITORING
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('chatInput');
    input.addEventListener('input', () => updateSendButton());

    // Auto-create session on load
    createNewSession();
});
