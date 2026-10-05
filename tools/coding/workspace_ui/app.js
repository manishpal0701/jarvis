function initWorkspaceApp() {
    const fileTree = document.getElementById('fileTree');
    const fileTabsContainer = document.getElementById('fileTabsContainer');
    const lineNumbers = document.getElementById('lineNumbers');
    const codeDisplay = document.getElementById('codeDisplay');
    const statusText = document.getElementById('statusText');
    const statusPill = document.getElementById('statusPill');
    const editorFileName = document.getElementById('editorFileName');
    const editorLangBadge = document.getElementById('editorLangBadge');
    const editorFileStatus = document.getElementById('editorFileStatus');
    const editorLineCount = document.getElementById('editorLineCount');
    const previewUrlInput = document.getElementById('previewUrlInput');
    const previewIframe = document.getElementById('previewIframe');
    const refreshPreviewBtn = document.getElementById('refreshPreviewBtn');
    const openBrowserBtn = document.getElementById('openBrowserBtn');
    const temporaryPublicUrl = document.getElementById('temporaryPublicUrl');
    const permanentPublicUrl = document.getElementById('permanentPublicUrl');

    let currentFilePath = "src/App.tsx";
    let activeGeneratingFile = null;
    let projectFiles = [];
    const allFilesContent = {}; // { "src/components/Navbar.tsx": "...actual code..." }
    const fileStates = {}; // { "src/components/Navbar.tsx": "waiting" | "generating" | "complete" }
    let previewUrl = "http://127.0.0.1:5177";

    // Helper: Line Count & Numbers
    function updateLineNumbers(code) {
        if (!code) {
            lineNumbers.textContent = "1";
            editorLineCount.textContent = "0 lines";
            return 0;
        }
        const lines = code.split('\n');
        const count = lines.length;
        let numsHtml = "";
        for (let i = 1; i <= count; i++) {
            numsHtml += i + "\n";
        }
        lineNumbers.textContent = numsHtml;
        editorLineCount.textContent = `${count} lines`;
        return count;
    }

    function getLanguageFromPath(filePath) {
        if (!filePath) return "CODE";
        const ext = filePath.split('.').pop().toLowerCase();
        if (ext === 'tsx' || ext === 'jsx') return 'TSX';
        if (ext === 'ts') return 'TS';
        if (ext === 'js') return 'JS';
        if (ext === 'css') return 'CSS';
        if (ext === 'json') return 'JSON';
        if (ext === 'html') return 'HTML';
        if (ext === 'md') return 'MD';
        return ext.toUpperCase();
    }

    function updateEditorSubbar() {
        const basename = currentFilePath ? currentFilePath.split('/').pop() : "App.tsx";
        editorFileName.textContent = basename;
        editorLangBadge.textContent = getLanguageFromPath(currentFilePath);

        const st = fileStates[currentFilePath] || "waiting";
        if (st === "generating") {
            editorFileStatus.className = "editor-file-status status-generating";
            editorFileStatus.textContent = "● Generating...";
        } else if (st === "complete") {
            editorFileStatus.className = "editor-file-status status-complete";
            editorFileStatus.textContent = "✓ Complete";
        } else {
            editorFileStatus.className = "editor-file-status status-waiting";
            editorFileStatus.textContent = "○ Waiting";
        }
    }

    function renderProjectStructure() {
        fileTree.innerHTML = "";
        fileTabsContainer.innerHTML = "";

        if (!projectFiles || projectFiles.length === 0) {
            return;
        }

        projectFiles.forEach(f => {
            const fState = fileStates[f.path] || (allFilesContent[f.path] ? "complete" : "waiting");
            let iconSymbol = "○";
            let iconColor = "#64748b";
            if (fState === "generating") {
                iconSymbol = "●";
                iconColor = "#f59e0b";
            } else if (fState === "complete") {
                iconSymbol = "✓";
                iconColor = "#4ade80";
            }

            // Sidebar Item
            const item = document.createElement('div');
            item.className = `file-item ${f.path === currentFilePath ? 'active' : ''}`;
            item.innerHTML = `<span>📄 ${f.path}</span> <span style="font-size:11px; font-weight:bold; color:${iconColor};">${iconSymbol}</span>`;
            item.addEventListener('click', () => selectFile(f.path));
            fileTree.appendChild(item);

            // Tab Item
            const tab = document.createElement('div');
            tab.className = `file-tab ${f.path === currentFilePath ? 'active' : ''}`;
            const basename = f.path.split('/').pop();
            tab.innerHTML = `<span>${basename}</span> <span style="font-size:10px; color:${iconColor};">${iconSymbol}</span>`;
            tab.addEventListener('click', () => selectFile(f.path));
            fileTabsContainer.appendChild(tab);
        });
    }

    function selectFile(filePath) {
        currentFilePath = filePath;
        updateEditorSubbar();

        const code = allFilesContent[filePath];
        const fState = fileStates[filePath] || "waiting";

        if (code !== undefined && code !== null && code.length > 0) {
            codeDisplay.textContent = code;
            if (fState === "generating") {
                const caret = document.createElement('span');
                caret.className = "streaming-caret";
                codeDisplay.appendChild(caret);
            }
            updateLineNumbers(code);
        } else if (fState === "waiting") {
            codeDisplay.textContent = `// Waiting for code generation: ${filePath}...`;
            updateLineNumbers("");
        } else {
            codeDisplay.textContent = "";
            updateLineNumbers("");
        }

        renderProjectStructure();
    }

    // SSE Stream Connection
    function connectSSE() {
        const evtSource = new EventSource('/api/stream');

        evtSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === 'init') {
                    if (data.project_files) {
                        projectFiles = data.project_files;
                        projectFiles.forEach(f => {
                            if (!fileStates[f.path]) fileStates[f.path] = "waiting";
                        });
                    }
                    if (data.all_files) {
                        Object.assign(allFilesContent, data.all_files);
                        Object.keys(data.all_files).forEach(fp => {
                            if (data.all_files[fp] && data.all_files[fp].trim()) {
                                fileStates[fp] = "complete";
                            }
                        });
                    }
                    if (data.file_path) currentFilePath = data.file_path;
                    if (data.status) statusText.textContent = data.status;
                    if (data.preview_url) {
                        previewUrl = data.preview_url;
                        previewUrlInput.value = previewUrl;
                        previewIframe.src = previewUrl;
                    }

                    renderProjectStructure();
                    selectFile(currentFilePath);
                }
                else if (data.type === 'project_files_update') {
                    projectFiles = data.files;
                    if (data.all_files) Object.assign(allFilesContent, data.all_files);
                    projectFiles.forEach(f => {
                        if (!fileStates[f.path]) {
                            fileStates[f.path] = (allFilesContent[f.path] && allFilesContent[f.path].trim()) ? "complete" : "waiting";
                        }
                    });
                    renderProjectStructure();
                }
                else if (data.type === 'file_start') {
                    activeGeneratingFile = data.file_path;
                    fileStates[data.file_path] = "generating";
                    if (allFilesContent[data.file_path] === undefined) {
                        allFilesContent[data.file_path] = "";
                    }
                    selectFile(data.file_path);
                }
                else if (data.type === 'code_stream') {
                    if (allFilesContent[data.file_path] === undefined) {
                        allFilesContent[data.file_path] = "";
                    }
                    allFilesContent[data.file_path] += data.chunk;
                    fileStates[data.file_path] = "generating";

                    if (data.file_path === currentFilePath) {
                        codeDisplay.textContent = allFilesContent[data.file_path];
                        const caret = document.createElement('span');
                        caret.className = "streaming-caret";
                        codeDisplay.appendChild(caret);
                        updateLineNumbers(allFilesContent[data.file_path]);
                        updateEditorSubbar();
                    }
                }
                else if (data.type === 'code_set') {
                    allFilesContent[data.file_path] = data.code;
                    fileStates[data.file_path] = "complete";

                    if (data.file_path === currentFilePath) {
                        codeDisplay.textContent = data.code;
                        updateLineNumbers(data.code);
                        updateEditorSubbar();
                    }
                    renderProjectStructure();
                }
                else if (data.type === 'file_end') {
                    fileStates[data.file_path] = "complete";
                    if (data.code) {
                        allFilesContent[data.file_path] = data.code;
                    }
                    if (activeGeneratingFile === data.file_path) {
                        activeGeneratingFile = null;
                    }
                    if (data.file_path === currentFilePath) {
                        const finalCode = allFilesContent[data.file_path] || "";
                        codeDisplay.textContent = finalCode;
                        updateLineNumbers(finalCode);
                        updateEditorSubbar();
                    }
                    renderProjectStructure();
                }
                else if (data.type === 'file_update') {
                    currentFilePath = data.file_path;
                    allFilesContent[data.file_path] = data.code;
                    fileStates[data.file_path] = "complete";
                    selectFile(data.file_path);
                }
                else if (data.type === 'status_update') {
                    statusText.textContent = data.status;
                    const cardHeader = document.getElementById('statusCardHeader');
                    const badgeBuild = document.getElementById('badgeBuild');
                    const badgeVQA = document.getElementById('badgeVQA');
                    const badgeResp = document.getElementById('badgeResponsive');
                    const pipelineSteps = document.getElementById('pipelineSteps');

                    if (pipelineSteps && data.status) {
                        const isError = data.status.includes("Failed") || data.status.includes("❌") || data.state === "error";
                        const isSuccess = data.status.includes("Ready") || data.status.includes("✓") || data.status.includes("Passed") || data.status.includes("SUCCESS");
                        const step = document.createElement('div');
                        step.className = `step-item ${isError ? 'step-failed' : (isSuccess ? 'step-done' : 'step-running')}`;
                        step.innerHTML = `<span>${isError ? '❌' : (isSuccess ? '✓' : '●')}</span> ${data.status}`;
                        pipelineSteps.appendChild(step);
                        pipelineSteps.scrollTop = pipelineSteps.scrollHeight;
                    }

                    if (data.status && (data.status.includes("Failed") || data.status.includes("❌") || data.state === "error")) {
                        if (cardHeader) {
                            cardHeader.textContent = "WEBSITE FAILED — REPAIR REQUIRED";
                            cardHeader.style.color = "#f87171";
                        }
                        if (badgeBuild) badgeBuild.className = "badge-red", badgeBuild.textContent = "❌ Failed";
                        if (badgeVQA) badgeVQA.className = "badge-red", badgeVQA.textContent = "❌ Failed";
                        if (badgeResp) badgeResp.className = "badge-red", badgeResp.textContent = "❌ Failed";
                    } else if (data.status && (data.status.includes("Website Ready") || data.status.includes("✓ Ready"))) {
                        if (cardHeader) {
                            cardHeader.textContent = "WEBSITE READY";
                            cardHeader.style.color = "#4ade80";
                        }
                        if (badgeBuild) badgeBuild.className = "badge-green", badgeBuild.textContent = "✓ Passed";
                        if (badgeVQA) badgeVQA.className = "badge-green", badgeVQA.textContent = "✓ 20/20";
                        if (badgeResp) badgeResp.className = "badge-green", badgeResp.textContent = "✓ Passed";
                    }

                    if (data.preview_url) {
                        previewUrl = data.preview_url;
                        previewUrlInput.value = previewUrl;
                        previewIframe.src = previewUrl;
                    }
                    if (data.temporary_url) {
                        temporaryPublicUrl.href = data.temporary_url;
                        temporaryPublicUrl.textContent = data.temporary_url;
                    }
                    if (data.permanent_url) {
                        permanentPublicUrl.textContent = data.permanent_url;
                    }
                }
            } catch (e) {
                console.error("SSE Error:", e);
            }
        };
    }

    if (refreshPreviewBtn) {
        refreshPreviewBtn.addEventListener('click', () => {
            if (previewIframe) previewIframe.src = previewIframe.src;
        });
    }

    if (openBrowserBtn) {
        openBrowserBtn.addEventListener('click', () => {
            if (previewUrl) window.open(previewUrl, '_blank');
        });
    }

    // ── CLIENT BRIEF MODAL OVERLAY DOM REFS (additional) ─────────────────────────
    const tabExplorerBtn = document.getElementById('tabExplorerBtn');
    const tabBriefBtn = document.getElementById('tabBriefBtn');
    const clientBriefPanel = document.getElementById('clientBriefPanel');
    const prevType = document.getElementById('prevType');
    const prevBrand = document.getElementById('prevBrand');
    const prevDesc = document.getElementById('prevDesc');
    const prevImageCount = document.getElementById('prevImageCount');
    const prevRefCount = document.getElementById('prevRefCount');

    // ── CLIENT BRIEF MODAL OVERLAY & FORM LOGIC ─────────────────────────────────
    const clientBriefModal = document.getElementById('clientBriefModal');
    const closeBriefModalBtn = document.getElementById('closeBriefModalBtn');
    const editBriefBtn = document.getElementById('editBriefBtn');

    const modalBizName = document.getElementById('modalBizName');
    const modalWebType = document.getElementById('modalWebType');
    const modalGoal = document.getElementById('modalGoal');
    const modalAudience = document.getElementById('modalAudience');
    const modalLocation = document.getElementById('modalLocation');
    const modalPhone = document.getElementById('modalPhone');
    const modalEmail = document.getElementById('modalEmail');
    const modalAddress = document.getElementById('modalAddress');
    const modalBizDesc = document.getElementById('modalBizDesc');

    const modalBrandStyle = document.getElementById('modalBrandStyle');
    const modalPrimaryColor = document.getElementById('modalPrimaryColor');
    const modalSecondaryColor = document.getElementById('modalSecondaryColor');
    const modalFont = document.getElementById('modalFont');

    const modalPages = document.getElementById('modalPages');
    const modalFeatures = document.getElementById('modalFeatures');
    const modalCta = document.getElementById('modalCta');
    const modalSeo = document.getElementById('modalSeo');
    const modalNotes = document.getElementById('modalNotes');

    const modalRefUrl = document.getElementById('modalRefUrl');
    const modalSaveRefUrlBtn = document.getElementById('modalSaveRefUrlBtn');

    const modalHeroHeading = document.getElementById('modalHeroHeading');
    const modalHeroDesc = document.getElementById('modalHeroDesc');
    const modalAboutContent = document.getElementById('modalAboutContent');

    const modalAssetRole = document.getElementById('modalAssetRole');
    const modalImageInput = document.getElementById('modalImageInput');
    const modalTriggerImagesBtn = document.getElementById('modalTriggerImagesBtn');
    const modalLogoInput = document.getElementById('modalLogoInput');
    const modalTriggerLogoBtn = document.getElementById('modalTriggerLogoBtn');

    const modalAssetCards = document.getElementById('modalAssetCards');
    const modalRefCards = document.getElementById('modalRefCards');
    const modalResetBtn = document.getElementById('modalResetBtn');
    const modalSaveBtn = document.getElementById('modalSaveBtn');
    const modalApproveBtn = document.getElementById('modalApproveBtn');

    function openClientBriefModal() {
        const modal = document.getElementById('clientBriefModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.style.display = 'flex';
            fetchBriefStatus();
        }
    }
    window.openClientBriefModal = openClientBriefModal;

    function closeClientBriefModal() {
        const modal = document.getElementById('clientBriefModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.style.display = 'none';
        }
    }
    window.closeClientBriefModal = closeClientBriefModal;

    if (closeBriefModalBtn) closeBriefModalBtn.addEventListener('click', closeClientBriefModal);

    document.addEventListener('click', (e) => {
        const btn = e.target.closest('#tabBriefBtn, #editBriefBtn');
        if (btn) {
            if (tabExplorerBtn) tabExplorerBtn.classList.remove('active');
            if (tabBriefBtn) tabBriefBtn.classList.add('active');
            openClientBriefModal();
        }
    });

    if (tabExplorerBtn) {
        tabExplorerBtn.addEventListener('click', () => {
            tabExplorerBtn.classList.add('active');
            if (tabBriefBtn) tabBriefBtn.classList.remove('active');
        });
    }

    if (tabBriefBtn) {
        tabBriefBtn.addEventListener('click', () => {
            if (tabExplorerBtn) tabExplorerBtn.classList.remove('active');
            tabBriefBtn.classList.add('active');
            openClientBriefModal();
        });
    }

    if (editBriefBtn) {
        editBriefBtn.addEventListener('click', () => {
            openClientBriefModal();
        });
    }

    // Modal Form Submission (Save Brief)
    async function saveModalBrief() {
        const payload = {
            company_name: modalBizName ? modalBizName.value.trim() : "",
            website_type: modalWebType ? modalWebType.value : "",
            website_goal: modalGoal ? modalGoal.value.trim() : "",
            target_audience: modalAudience ? modalAudience.value.trim() : "",
            location: modalLocation ? modalLocation.value.trim() : "",
            contact_number: modalPhone ? modalPhone.value.trim() : "",
            email: modalEmail ? modalEmail.value.trim() : "",
            address: modalAddress ? modalAddress.value.trim() : "",
            business_description: modalBizDesc ? modalBizDesc.value.trim() : "",
            brand_tone: modalBrandStyle ? modalBrandStyle.value.trim() : "",
            primary_color: modalPrimaryColor ? modalPrimaryColor.value.trim() : "",
            secondary_color: modalSecondaryColor ? modalSecondaryColor.value.trim() : "",
            preferred_font: modalFont ? modalFont.value.trim() : "",
            required_pages: modalPages ? modalPages.value.trim() : "",
            features_functionality: modalFeatures ? modalFeatures.value.trim() : "",
            cta_action: modalCta ? modalCta.value.trim() : "",
            seo_requirements: modalSeo ? modalSeo.value.trim() : "",
            special_requirements: modalNotes ? modalNotes.value.trim() : "",
            hero_heading: modalHeroHeading ? modalHeroHeading.value.trim() : "",
            hero_description: modalHeroDesc ? modalHeroDesc.value.trim() : "",
            about_content: modalAboutContent ? modalAboutContent.value.trim() : ""
        };

        try {
            await fetch('/api/brief/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            await fetchBriefStatus();
        } catch (err) {
            console.error("Failed to save brief form:", err);
        }
    }

    if (modalSaveBtn) {
        modalSaveBtn.addEventListener('click', async () => {
            await saveModalBrief();
            alert("Client Brief saved successfully!");
        });
    }

    if (modalResetBtn) {
        modalResetBtn.addEventListener('click', async () => {
            if (!confirm("Are you sure you want to clear the client brief?")) return;
            const fields = [
                modalBizName, modalGoal, modalAudience, modalLocation, modalPhone, modalEmail,
                modalAddress, modalBizDesc, modalBrandStyle, modalPrimaryColor, modalSecondaryColor,
                modalFont, modalPages, modalFeatures, modalCta, modalSeo, modalNotes,
                modalHeroHeading, modalHeroDesc, modalAboutContent, modalRefUrl
            ];
            fields.forEach(f => { if (f) f.value = ""; });

            await saveModalBrief();
            await fetchBriefStatus();
        });
    }

    if (modalApproveBtn) {
        modalApproveBtn.addEventListener('click', async () => {
            modalApproveBtn.disabled = true;
            modalApproveBtn.textContent = "⏳ Starting Build...";
            await saveModalBrief();
            try {
                await fetch('/api/brief/approve', { method: 'POST' });
                closeClientBriefModal();
                if (tabExplorerBtn) tabExplorerBtn.click();
            } catch (err) {
                console.error("Failed to approve brief:", err);
            } finally {
                modalApproveBtn.disabled = false;
                modalApproveBtn.textContent = "🚀 Save & Generate Website";
            }
        });
    }

    // Image file validation helper
    function isValidImageFile(file) {
        if (!file) return false;
        const validExtensions = ['.png', '.jpg', '.jpeg', '.webp', '.svg'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        const validMime = file.type.startsWith('image/');
        return validExtensions.includes(ext) || validMime;
    }

    // Modal Image Upload Handler
    if (modalTriggerImagesBtn && modalImageInput) {
        modalTriggerImagesBtn.addEventListener('click', () => modalImageInput.click());
        modalImageInput.addEventListener('change', async () => {
            if (!modalImageInput.files || modalImageInput.files.length === 0) return;

            const selectedRole = modalAssetRole ? modalAssetRole.value : "hero_image";
            const formData = new FormData();
            let validCount = 0;

            for (let i = 0; i < modalImageInput.files.length; i++) {
                const file = modalImageInput.files[i];
                if (!isValidImageFile(file)) {
                    alert(`Skipping invalid image file: ${file.name}. Only PNG, JPG, WEBP, and SVG formats are supported.`);
                    continue;
                }
                formData.append(`file_${validCount}`, file);
                validCount++;
            }

            if (validCount === 0) return;
            formData.append("role", selectedRole);

            try {
                const resp = await fetch('/api/brief/upload', {
                    method: 'POST',
                    body: formData
                });
                if (resp.ok) {
                    await fetchBriefStatus();
                } else {
                    alert("Image upload failed. Server returned error code.");
                }
            } catch (err) {
                console.error("Failed to upload client images:", err);
                alert("Upload failed: " + err.message);
            } finally {
                modalImageInput.value = "";
            }
        });
    }

    // Modal Logo Upload Handler
    if (modalTriggerLogoBtn && modalLogoInput) {
        modalTriggerLogoBtn.addEventListener('click', () => modalLogoInput.click());
        modalLogoInput.addEventListener('change', async () => {
            if (!modalLogoInput.files || modalLogoInput.files.length === 0) return;
            const file = modalLogoInput.files[0];
            if (!isValidImageFile(file)) {
                alert(`Invalid logo file: ${file.name}. Only PNG, JPG, WEBP, and SVG formats are supported.`);
                return;
            }

            const formData = new FormData();
            formData.append("file_logo", file);
            formData.append("role", "logo");

            try {
                const resp = await fetch('/api/brief/upload', {
                    method: 'POST',
                    body: formData
                });
                if (resp.ok) {
                    await fetchBriefStatus();
                } else {
                    alert("Logo upload failed.");
                }
            } catch (err) {
                console.error("Failed to upload logo:", err);
            } finally {
                modalLogoInput.value = "";
            }
        });
    }

    // Reference URL Save Button
    if (modalSaveRefUrlBtn && modalRefUrl) {
        modalSaveRefUrlBtn.addEventListener('click', async () => {
            const url = modalRefUrl.value.trim();
            if (!url) return;
            try {
                await fetch('/api/brief/reference', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ref_type: "URL", source: url, title: "Reference Website URL" })
                });
                modalRefUrl.value = "";
                await fetchBriefStatus();
            } catch (err) {
                console.error("Failed to save reference URL:", err);
            }
        });
    }

    // Asset Removal Function
    window.removeBriefAsset = async function(assetId) {
        try {
            await fetch('/api/brief/remove_asset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ asset_id: assetId })
            });
            await fetchBriefStatus();
        } catch (err) {
            console.error("Failed to remove asset:", err);
        }
    };

    // Update fetchBriefStatus to populate all Modal Form Fields and Asset Cards
    async function fetchBriefStatus() {
        try {
            const resp = await fetch('/api/brief/status');
            if (!resp.ok) return;
            const data = await resp.json();

            // Populate Form Inputs if not already typed by user
            if (modalBizName && data.company_name) modalBizName.value = data.company_name;
            if (modalWebType && data.website_type && data.website_type !== "UNKNOWN") modalWebType.value = data.website_type;
            if (modalGoal && data.website_goal) modalGoal.value = data.website_goal;
            if (modalAudience && data.target_audience) modalAudience.value = data.target_audience;
            if (modalLocation && data.location) modalLocation.value = data.location;
            if (modalPhone && data.contact_number) modalPhone.value = data.contact_number;
            if (modalEmail && data.email) modalEmail.value = data.email;
            if (modalAddress && data.address) modalAddress.value = data.address;
            if (modalBizDesc && data.business_description) modalBizDesc.value = data.business_description;
            if (modalBrandStyle && data.brand_tone) modalBrandStyle.value = data.brand_tone;
            if (modalPrimaryColor && data.primary_color) modalPrimaryColor.value = data.primary_color;
            if (modalSecondaryColor && data.secondary_color) modalSecondaryColor.value = data.secondary_color;
            if (modalFont && data.preferred_font) modalFont.value = data.preferred_font;
            if (modalPages && data.required_pages) modalPages.value = data.required_pages;
            if (modalFeatures && data.features_functionality) modalFeatures.value = data.features_functionality;
            if (modalCta && data.cta_action) modalCta.value = data.cta_action;
            if (modalSeo && data.seo_requirements) modalSeo.value = data.seo_requirements;
            if (modalNotes && data.special_requirements) modalNotes.value = data.special_requirements;
            if (modalHeroHeading && data.hero_heading) modalHeroHeading.value = data.hero_heading;
            if (modalHeroDesc && data.hero_description) modalHeroDesc.value = data.hero_description;
            if (modalAboutContent && data.about_content) modalAboutContent.value = data.about_content;

            // Render Asset Cards with Remove Button
            if (modalAssetCards) {
                if (!data.assets || data.assets.length === 0) {
                    modalAssetCards.innerHTML = '<div class="empty-hint">No client images uploaded yet</div>';
                } else {
                    modalAssetCards.innerHTML = "";
                    data.assets.forEach(a => {
                        const div = document.createElement('div');
                        div.className = 'asset-card-item';
                        div.innerHTML = `
                            <span>🖼️ <strong>${a.filename}</strong></span>
                            <span class="role-badge">${a.role.toUpperCase()}</span>
                            <button class="remove-btn" onclick="window.removeBriefAsset('${a.asset_id}')">🗑️ Remove</button>
                        `;
                        modalAssetCards.appendChild(div);
                    });
                }
            }

            // Render Reference Cards
            if (modalRefCards) {
                if (!data.references || data.references.length === 0) {
                    modalRefCards.innerHTML = '<div class="empty-hint">No reference URLs or files added yet</div>';
                } else {
                    modalRefCards.innerHTML = "";
                    data.references.forEach(r => {
                        const div = document.createElement('div');
                        div.className = 'asset-card-item';
                        div.innerHTML = `<span>🔗 [${r.ref_type}] ${r.title || r.source}</span>`;
                        modalRefCards.appendChild(div);
                    });
                }
            }

            // Render Preview Summary Panel in Sidebar
            if (prevType) prevType.textContent = data.website_type || "UNKNOWN";
            if (prevBrand) prevBrand.textContent = data.company_name || "Pending Details";
            if (prevDesc) prevDesc.textContent = data.business_description || "Provide business description";
            if (prevImageCount) prevImageCount.textContent = `${(data.assets || []).length} uploaded`;
            if (prevRefCount) prevRefCount.textContent = `${(data.references || []).length} added`;

        } catch (err) {
            console.error("Failed to fetch brief status:", err);
        }
    }
    window.fetchBriefStatus = fetchBriefStatus;

    fetchBriefStatus();
    connectSSE();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWorkspaceApp);
} else {
    initWorkspaceApp();
}


