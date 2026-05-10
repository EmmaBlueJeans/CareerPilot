(function () {
    const shell = document.getElementById('chat-shell');
    if (!shell) return;

    const sessionId = shell.dataset.sessionId;
    const alreadyStarted = shell.dataset.alreadyStarted === '1';
    const stream = document.getElementById('chat-stream');
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');

    function scrollToEnd() {
        stream.scrollTop = stream.scrollHeight;
    }

    function bubble(role, content) {
        const div = document.createElement('div');
        div.className = 'chat-bubble ' + role;
        div.textContent = content;
        return div;
    }

    function typingBubble() {
        const div = document.createElement('div');
        div.className = 'chat-bubble assistant typing';
        div.innerHTML = '<span></span><span></span><span></span>';
        return div;
    }

    function setSending(sending) {
        sendBtn.disabled = sending;
        input.disabled = sending;
        sendBtn.querySelector('.btn-label').textContent = sending ? 'Sending…' : 'Send';
        sendBtn.querySelector('.btn-spinner').hidden = !sending;
    }

    function renderAll(messages) {
        stream.innerHTML = '';
        messages.forEach(m => stream.appendChild(bubble(m.role, m.content)));
        scrollToEnd();
    }

    async function start() {
        const typing = typingBubble();
        stream.appendChild(typing);
        scrollToEnd();
        try {
            const res = await fetch(`/interview/${sessionId}/start`, { method: 'POST' });
            const data = await res.json();
            typing.remove();
            if (data.error) {
                alert(data.error);
                return;
            }
            renderAll(data.messages);
        } catch (e) {
            typing.remove();
            alert('Failed to start interview: ' + e.message);
        }
    }

    async function send(text) {
        stream.appendChild(bubble('user', text));
        scrollToEnd();
        const typing = typingBubble();
        stream.appendChild(typing);
        scrollToEnd();

        setSending(true);
        try {
            const res = await fetch(`/interview/${sessionId}/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text }),
            });
            const data = await res.json();
            typing.remove();
            if (data.error) {
                alert(data.error);
                return;
            }
            renderAll(data.messages);
            if (data.concluded) {
                form.hidden = true;
                setTimeout(() => window.location.reload(), 600);
            }
        } catch (e) {
            typing.remove();
            alert('Failed to send: ' + e.message);
        } finally {
            setSending(false);
        }
    }

    form.addEventListener('submit', e => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        autoresize();
        send(text);
    });

    input.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });

    function autoresize() {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 160) + 'px';
    }
    input.addEventListener('input', autoresize);

    if (alreadyStarted) {
        scrollToEnd();
    } else {
        start();
    }
})();
