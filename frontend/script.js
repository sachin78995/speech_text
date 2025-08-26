(function () {
    const apiBase = 'http://localhost:5000/api';
    const authUser = JSON.parse(localStorage.getItem('auth_user') || 'null');
    if (!authUser) {
        // Require login for the main app
        window.location.href = 'login.html';
        return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    const transcriptEl = document.getElementById('transcript');
    const itemsEl = document.getElementById('items');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const saveBtn = document.getElementById('saveBtn');
    const languageEl = document.getElementById('language');

    let recognition = null;
    let recognizing = false;

    function appendItem(item) {
        const li = document.createElement('li');
        li.className = 'item';
        li.textContent = `[${item.language || 'unknown'}] ${item.text}`;
        itemsEl.prepend(li);
    }

    async function refreshList() {
        try {
            const res = await fetch(`${apiBase}/transcripts`);
            const data = await res.json();
            itemsEl.innerHTML = '';
            data.forEach(appendItem);
        } catch (e) {
            console.error(e);
        }
    }

    async function saveCurrent() {
        const text = transcriptEl.value.trim();
        if (!text) return;
        const language = languageEl.value;
        const res = await fetch(`${apiBase}/transcripts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, language })
        });
        if (res.ok) {
            const item = await res.json();
            appendItem(item);
            transcriptEl.value = '';
            saveBtn.disabled = true;
        } else {
            const err = await res.json().catch(() => ({ error: 'Unknown error' }));
            alert('Failed to save: ' + (err.error || res.status));
        }
    }

    function setupRecognition() {
        if (!SpeechRecognition) {
            alert('Speech Recognition API is not supported in this browser. Try Chrome.');
            return null;
        }
        const rec = new SpeechRecognition();
        rec.continuous = true;
        rec.interimResults = true;
        rec.lang = languageEl.value;

        let finalTranscript = '';

        rec.onresult = function (event) {
            let interim = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                const t = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += t;
                } else {
                    interim += t;
                }
            }
            transcriptEl.value = (finalTranscript + ' ' + interim).trim();
            saveBtn.disabled = transcriptEl.value.trim().length === 0;
        };

        rec.onerror = function (e) {
            console.error('Recognition error', e);
        };

        rec.onend = function () {
            recognizing = false;
            startBtn.disabled = false;
            stopBtn.disabled = true;
        };

        return rec;
    }

    startBtn.addEventListener('click', function () {
        if (recognizing) return;
        recognition = setupRecognition();
        if (!recognition) return;
        recognition.lang = languageEl.value;
        recognition.start();
        recognizing = true;
        startBtn.disabled = true;
        stopBtn.disabled = false;
    });

    stopBtn.addEventListener('click', function () {
        if (recognition && recognizing) {
            recognition.stop();
        }
    });

    saveBtn.addEventListener('click', saveCurrent);
    languageEl.addEventListener('change', function () {
        if (recognition && recognizing) {
            recognition.lang = languageEl.value;
        }
    });

    refreshList();
    // Simple logout link injection
    const header = document.querySelector('h1');
    if (header) {
        const span = document.createElement('span');
        span.style.fontSize = '0.9rem';
        span.style.marginLeft = '12px';
        span.innerHTML = `(Signed in as ${authUser.first_name || ''} ${authUser.last_name || ''} <a href="#" id="logoutLink">logout</a>)`;
        header.after(span);
        span.querySelector('#logoutLink').addEventListener('click', function(e){
            e.preventDefault();
            localStorage.removeItem('auth_user');
            window.location.href = 'login.html';
        });
    }
})();


