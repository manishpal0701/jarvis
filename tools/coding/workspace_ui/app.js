(function() {
    const filePathEl = document.getElementById('filePath');
    const langBadgeEl = document.getElementById('langBadge');
    const statusPillEl = document.getElementById('statusPill');
    const statusTextEl = document.getElementById('statusText');
    const lineNumbersEl = document.getElementById('lineNumbers');
    const codeDisplayEl = document.getElementById('codeDisplay');
    const fileTabsContainer = document.getElementById('fileTabsContainer');
    const editorViewport = document.querySelector('.editor-viewport');

    let currentCode = "";
    let currentFilePath = "main.py";
    let projectFilesList = [];
    let filesMap = {};
    let sseInstance = null;

    function updateLineNumbers(code) {
        if (!lineNumbersEl) return;
        const lines = code ? code.split('\n') : [""];
        const count = Math.max(1, lines.length);
        let nums = [];
        for (let i = 1; i <= count; i++) {
            nums.push(i);
        }
        lineNumbersEl.innerHTML = nums.join('<br>');
    }

    function highlightCode(code) {
        if (!code) return "";
        let escaped = code
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
        return escaped;
    }

    function renderCode(code) {
        currentCode = code || "";
        const len = currentCode.length;
        const first100 = currentCode.substring(0, 100);

        console.log(`[renderCode Log] renderCode() called? YES | Content length: ${len} | First 100 characters: ${JSON.stringify(first100)}`);

        if (codeDisplayEl) {
            console.log(`[DOM Editor Update] Updating codeDisplayEl.innerHTML | Length being written: ${len}`);
            codeDisplayEl.innerHTML = highlightCode(currentCode);
        } else {
            console.error(`[DOM Editor Update ERROR] codeDisplayEl element is null/undefined!`);
        }

        updateLineNumbers(currentCode);
        if (editorViewport) {
            editorViewport.scrollTop = editorViewport.scrollHeight;
        }
    }

    function setStatus(text, stateClass) {
        if (statusTextEl) statusTextEl.textContent = text || "";
        if (statusPillEl) statusPillEl.className = "status-pill " + (stateClass || "writing");
    }

    function setFileInfo(filePath, lang) {
        if (filePath) {
            currentFilePath = filePath;
            if (filePathEl) filePathEl.textContent = filePath;
        }
        if (lang && langBadgeEl) {
            langBadgeEl.textContent = lang.toUpperCase();
        }
        renderProjectTabs();
    }

    function renderProjectTabs() {
        if (!fileTabsContainer) return;

        if (!projectFilesList || projectFilesList.length === 0) {
            fileTabsContainer.innerHTML = `
                <div class="file-path-badge active" data-path="${currentFilePath}">
                    <span class="folder-icon">📁</span>
                    <span>${currentFilePath}</span>
                </div>
            `;
            return;
        }

        let html = "";
        projectFilesList.forEach(f => {
            const isActive = f.path === currentFilePath ? "active" : "";
            html += `
                <div class="file-path-badge ${isActive}" data-path="${f.path}">
                    <span class="folder-icon">📁</span>
                    <span>${f.path}</span>
                </div>
            `;
        });
        fileTabsContainer.innerHTML = html;

        // Add tab click listeners
        const tabBadges = fileTabsContainer.querySelectorAll('.file-path-badge');
        tabBadges.forEach(badge => {
            badge.addEventListener('click', function() {
                const targetPath = this.getAttribute('data-path');
                if (targetPath && targetPath !== currentFilePath) {
                    currentFilePath = targetPath;
                    const code = filesMap[currentFilePath] || "";
                    let item = projectFilesList.find(x => x.path === currentFilePath);
                    setFileInfo(currentFilePath, item ? item.lang : undefined);
                    renderCode(code);
                }
            });
        });
    }

    // Connect to Server-Sent Events (SSE) stream
    function connectSSE() {
        if (sseInstance) {
            try { sseInstance.close(); } catch(e) {}
            sseInstance = null;
        }

        console.log("[Workspace UI] Connecting to SSE stream at /api/stream...");
        const evtSource = new EventSource('/api/stream');
        sseInstance = evtSource;

        evtSource.onopen = function() {
            console.log("[Workspace UI] SSE connected successfully (Status 200).");
        };

        evtSource.onmessage = function(event) {
            try {
                const rawData = event.data || "";
                const payloadLen = rawData.length;
                const first100 = rawData.substring(0, 100);
                const data = JSON.parse(rawData);
                const eventName = data.type || "unknown";

                console.log(`[SSE Event] Event name: ${eventName} | Payload length: ${payloadLen} | First 100 chars: ${JSON.stringify(first100)}`);

                if (data.type === 'init') {
                    console.log(`[SSE Details - init] code length: ${(data.code || "").length}, file_path: ${data.file_path}`);
                    if (data.project_files) {
                        projectFilesList = data.project_files;
                    }
                    if (data.all_files) {
                        filesMap = Object.assign({}, data.all_files);
                    }
                    if (data.file_path) {
                        currentFilePath = data.file_path;
                        setFileInfo(data.file_path, data.language);
                    }
                    if (data.status) {
                        setStatus(data.status, data.state);
                    }
                    if (data.code !== undefined) {
                        filesMap[currentFilePath] = data.code;
                        renderCode(data.code);
                    }
                }
                else if (data.type === 'status_update') {
                    console.log(`[SSE Details - status_update] status: "${data.status}", state: "${data.state}"`);
                    setStatus(data.status, data.state);
                }
                else if (data.type === 'file_update') {
                    console.log(`[SSE Details - file_update] file_path: "${data.file_path}", language: "${data.language}"`);
                    if (data.file_path) {
                        currentFilePath = data.file_path;
                        setFileInfo(data.file_path, data.language);
                    }
                    if (data.code !== undefined) {
                        filesMap[currentFilePath] = data.code;
                        renderCode(data.code);
                    }
                }
                else if (data.type === 'project_files_update') {
                    console.log(`[SSE Details - project_files_update] count: ${(data.files || []).length}`);
                    if (data.files) projectFilesList = data.files;
                    if (data.all_files) Object.assign(filesMap, data.all_files);
                    renderProjectTabs();
                }
                else if (data.type === 'file_start') {
                    console.log(`[SSE Details - file_start] file_path: "${data.file_path}"`);
                    if (data.file_path) {
                        currentFilePath = data.file_path;
                        filesMap[currentFilePath] = filesMap[currentFilePath] || "";
                        setFileInfo(currentFilePath);
                        renderCode(filesMap[currentFilePath]);
                    }
                }
                else if (data.type === 'file_end') {
                    console.log(`[SSE Details - file_end] file_path: "${data.file_path}"`);
                    if (data.file_path && filesMap[data.file_path] !== undefined) {
                        if (currentFilePath === data.file_path) {
                            renderCode(filesMap[data.file_path]);
                        }
                    }
                }
                else if (data.type === 'code_stream') {
                    const targetPath = data.file_path || currentFilePath;
                    const chunkLen = (data.chunk || "").length;
                    console.log(`[SSE Details - code_stream] chunk length: ${chunkLen}, targetPath: "${targetPath}", line: ${data.line}, col: ${data.column}`);
                    filesMap[targetPath] = (filesMap[targetPath] || "") + data.chunk;
                    if (targetPath === currentFilePath) {
                        if (data.line && data.column) {
                            setStatus(`Jarvis typing ${targetPath}... Ln ${data.line}, Col ${data.column}`, "writing");
                        }
                        renderCode(filesMap[targetPath]);
                    }
                }
                else if (data.type === 'code_set') {
                    const targetPath = data.file_path || currentFilePath;
                    const codeLen = (data.code || "").length;
                    console.log(`[SSE Details - code_set] code length: ${codeLen}, targetPath: "${targetPath}", is_final: ${data.is_final}`);
                    filesMap[targetPath] = data.code;
                    if (targetPath === currentFilePath) {
                        renderCode(data.code);
                    }
                }
            } catch (err) {
                console.error("[Workspace UI] SSE message parse error:", err);
            }
        };

        evtSource.onerror = function(err) {
            console.warn("[Workspace UI] SSE Error / Disconnect. Reconnecting in 3s...", err);
            setStatus("Reconnecting...", "thinking");
            try { evtSource.close(); } catch(e) {}
            sseInstance = null;
            setTimeout(connectSSE, 3000);
        };
    }

    // Initialize single SSE connection on load
    connectSSE();
})();
