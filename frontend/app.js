/**
 * StudyMate AI — Core App JS
 * Handles all backend API requests, authentication, upload, chat,
 * summaries, quizzes, flashcards, and study plans.
 */

// Dynamic API Base URL detection
const API_BASE = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
    ? "http://localhost:8001/api/v1"
    : `${window.location.origin}/api/v1`;

// Application State
let state = {
    token: localStorage.getItem("token") || null,
    username: localStorage.getItem("username") || null,
    selectedDocId: null,
    activeTab: "chat",
    conversationId: null,
    // Summarizer state
    summaryData: null,
    summaryDocId: null,
    // Quiz state
    quizData: null,
    quizDocId: null,
    quizAnswers: {},
    quizChecked: {},
    // Flashcard state
    flashcardData: null,
    flashcardDocId: null,
    flashcardIndex: 0,
    flashcardFlipped: false,
    // Plan state
    planData: null,
    planDocId: null
};

// ──────────────────────────────────────
// Page Lifecycles & Navigation
// ──────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
    initApp();
});

function initApp() {
    if (state.token) {
        showView("workspace");
        loadUserProfile();
        loadDocumentsList();
        loadConversationHistory();
        renderChatWelcome();
    } else {
        showView("landing");
    }
}

function showView(view) {
    const landing = document.getElementById("landing-view");
    const workspace = document.getElementById("workspace-view");
    if (view === "workspace") {
        landing.classList.add("hidden");
        workspace.classList.remove("hidden");
        document.body.classList.remove("overflow-y-auto");
    } else {
        landing.classList.remove("hidden");
        workspace.classList.add("hidden");
        document.body.classList.add("overflow-y-auto");
    }
}

// ──────────────────────────────────────
// Authentication Flow
// ──────────────────────────────────────
function openAuthModal(tab = "login") {
    const modal = document.getElementById("auth-modal");
    modal.classList.remove("hidden");
    switchAuthTab(tab);
}

function closeAuthModal() {
    const modal = document.getElementById("auth-modal");
    modal.classList.add("hidden");
    document.getElementById("auth-error").classList.add("hidden");
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const loginBtn = document.getElementById("tab-login-btn");
    const registerBtn = document.getElementById("tab-register-btn");
    document.getElementById("auth-error").classList.add("hidden");

    if (tab === "login") {
        loginForm.classList.remove("hidden");
        registerForm.classList.add("hidden");
        loginBtn.className = "text-lg font-bold border-b-2 border-accent-glow pb-2 focus:outline-none text-text-primary";
        registerBtn.className = "text-lg font-bold text-text-muted pb-2 focus:outline-none hover:text-text-primary";
    } else {
        loginForm.classList.add("hidden");
        registerForm.classList.remove("hidden");
        loginBtn.className = "text-lg font-bold text-text-muted pb-2 focus:outline-none hover:text-text-primary";
        registerBtn.className = "text-lg font-bold border-b-2 border-accent-blue pb-2 focus:outline-none text-text-primary";
    }
}

async function handleLoginSubmit(event) {
    event.preventDefault();
    const errorBanner = document.getElementById("auth-error");
    errorBanner.classList.add("hidden");

    const usernameInput = document.getElementById("login-username").value.trim();
    const passwordInput = document.getElementById("login-password").value;

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: usernameInput, password: passwordInput })
        });

        const data = await response.json();

        if (response.ok) {
            state.token = data.access_token;
            state.username = usernameInput;
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("username", usernameInput);
            closeAuthModal();
            initApp();
        } else {
            errorBanner.innerText = data.detail || "Authentication failed.";
            errorBanner.classList.remove("hidden");
        }
    } catch (e) {
        errorBanner.innerText = "Error connecting to server.";
        errorBanner.classList.remove("hidden");
    }
}

async function handleRegisterSubmit(event) {
    event.preventDefault();
    const errorBanner = document.getElementById("auth-error");
    errorBanner.classList.add("hidden");

    const email = document.getElementById("reg-email").value.trim();
    const username = document.getElementById("reg-username").value.trim();
    const password = document.getElementById("reg-password").value;

    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, username, password })
        });

        const data = await response.json();

        if (response.ok) {
            switchAuthTab("login");
            document.getElementById("login-username").value = username;
            alert("Account created successfully! You can now log in.");
        } else {
            errorBanner.innerText = data.detail || "Registration failed.";
            errorBanner.classList.remove("hidden");
        }
    } catch (e) {
        errorBanner.innerText = "Error connecting to server.";
        errorBanner.classList.remove("hidden");
    }
}

function handleLogout() {
    state.token = null;
    state.username = null;
    state.selectedDocId = null;
    state.conversationId = null;
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    showView("landing");
}

function loadUserProfile() {
    document.getElementById("user-display-name").innerText = state.username;
    document.getElementById("user-avatar-initial").innerText = state.username ? state.username[0].toUpperCase() : "U";
}

// Helper to construct auth headers
function authHeaders() {
    return {
        "Authorization": `Bearer ${state.token}`
    };
}

// ──────────────────────────────────────
// Document Management
// ──────────────────────────────────────
async function loadDocumentsList() {
    try {
        const response = await fetch(`${API_BASE}/documents/`, {
            headers: authHeaders()
        });
        if (response.ok) {
            const data = await response.json();
            const select = document.getElementById("doc-context-select");
            
            // Keep default value
            select.innerHTML = '<option value="all">🌐 All Documents</option>';
            
            data.documents.forEach(doc => {
                const opt = document.createElement("option");
                opt.value = doc.id;
                const statusEmoji = doc.status === "processed" ? "✅" : "⏳";
                opt.innerText = `${statusEmoji} ${doc.original_filename.substring(0, 28)}`;
                select.appendChild(opt);
            });

            if (state.selectedDocId) {
                select.value = state.selectedDocId;
            }
        }
    } catch (e) {
        console.error("Failed to load documents list", e);
    }
}

function handleDocSelectionChange() {
    const val = document.getElementById("doc-context-select").value;
    state.selectedDocId = val === "all" ? null : val;
    
    // Clear smart feature states on change
    resetSmartFeatureStates();
    syncWarnings();
    
    // Load summary automatically if doc selected and tab is active
    if (state.selectedDocId && state.activeTab === "summarizer") {
        fetchSummaryData();
    }
}

function resetSmartFeatureStates() {
    state.summaryData = null;
    state.quizData = null;
    state.flashcardData = null;
    state.planData = null;
}

function syncWarnings() {
    const isDocSelected = !!state.selectedDocId;
    
    // Summarizer warning
    const sumWarning = document.getElementById("summary-warning");
    const sumBox = document.getElementById("summary-box");
    if (isDocSelected) {
        sumWarning.classList.add("hidden");
        sumBox.classList.remove("hidden");
    } else {
        sumWarning.classList.remove("hidden");
        sumBox.classList.add("hidden");
    }

    // Quiz warning
    const quizWarning = document.getElementById("quiz-warning");
    const quizConfig = document.getElementById("quiz-config-box");
    const quizActive = document.getElementById("quiz-active-box");
    if (isDocSelected) {
        quizWarning.classList.add("hidden");
        if (state.quizData) {
            quizConfig.classList.add("hidden");
            quizActive.classList.remove("hidden");
        } else {
            quizConfig.classList.remove("hidden");
            quizActive.classList.add("hidden");
        }
    } else {
        quizWarning.classList.remove("hidden");
        quizConfig.classList.add("hidden");
        quizActive.classList.add("hidden");
    }

    // Flashcards warning
    const cardsWarning = document.getElementById("flashcards-warning");
    const cardsConfig = document.getElementById("flashcards-config-box");
    const cardsActive = document.getElementById("flashcards-active-box");
    if (isDocSelected) {
        cardsWarning.classList.add("hidden");
        if (state.flashcardData) {
            cardsConfig.classList.add("hidden");
            cardsActive.classList.remove("hidden");
        } else {
            cardsConfig.classList.remove("hidden");
            cardsActive.classList.add("hidden");
        }
    } else {
        cardsWarning.classList.remove("hidden");
        cardsConfig.classList.add("hidden");
        cardsActive.classList.add("hidden");
    }

    // Study Plan warning
    const planWarning = document.getElementById("plan-warning");
    const planConfig = document.getElementById("plan-config-box");
    const planActive = document.getElementById("plan-active-box");
    if (isDocSelected) {
        planWarning.classList.add("hidden");
        if (state.planData) {
            planConfig.classList.add("hidden");
            planActive.classList.remove("hidden");
        } else {
            planConfig.classList.remove("hidden");
            planActive.classList.add("hidden");
        }
    } else {
        planWarning.classList.remove("hidden");
        planConfig.classList.add("hidden");
        planActive.classList.add("hidden");
    }
}

// ──────────────────────────────────────
// File Upload & Processing
// ──────────────────────────────────────
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) uploadDocument(file);
}

// Drag & drop listeners
const dropzone = document.getElementById("upload-zone");
dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("border-accent-glow");
});
dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("border-accent-glow");
});
dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-accent-glow");
    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
        uploadDocument(file);
    } else {
        alert("Please drop a valid PDF file.");
    }
});
dropzone.addEventListener("click", () => {
    document.getElementById("file-input").click();
});

async function uploadDocument(file) {
    const banner = document.getElementById("status-banner");
    banner.classList.remove("hidden");
    banner.className = "mt-3 p-3 rounded-lg text-[11px] border border-accent-glow/20 bg-accent-glow/5 text-text-primary";
    banner.innerHTML = `<div class="flex items-center space-x-2">
        <svg class="animate-spin h-4.5 w-4.5 text-accent-glow" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <span>Uploading PDF...</span>
    </div>`;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${API_BASE}/documents/upload`, {
            method: "POST",
            headers: authHeaders(),
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            banner.innerHTML = `<div class="flex items-center space-x-2">
                <svg class="animate-spin h-4.5 w-4.5 text-accent-blue" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <span>Extracting content & generating vector index...</span>
            </div>`;

            // Auto-trigger parsing/embedding
            const procResponse = await fetch(`${API_BASE}/documents/${data.id}/process`, {
                method: "POST",
                headers: authHeaders()
            });

            if (procResponse.ok) {
                const procData = await procResponse.json();
                banner.className = "mt-3 p-3 rounded-lg text-[11px] border border-green-200 bg-green-50 text-green-800";
                banner.innerHTML = `✅ Processed: ${procData.total_chunks} chunks indexing successfully!`;
                loadDocumentsList();
            } else {
                const procErr = await procResponse.json();
                banner.className = "mt-3 p-3 rounded-lg text-[11px] border border-red-200 bg-red-50 text-red-800";
                banner.innerHTML = `⚠️ Processing: ${procErr.detail || "failed"}`;
            }
        } else {
            banner.className = "mt-3 p-3 rounded-lg text-[11px] border border-red-200 bg-red-50 text-red-800";
            banner.innerHTML = `❌ Upload: ${data.detail || "failed"}`;
        }
    } catch (e) {
        banner.className = "mt-3 p-3 rounded-lg text-[11px] border border-red-200 bg-red-50 text-red-800";
        banner.innerHTML = "Connection error.";
    }
}

// ──────────────────────────────────────
// Tab View Switcher
// ──────────────────────────────────────
function switchWorkspaceTab(tab) {
    state.activeTab = tab;

    // Toggle button UI
    const tabsList = ["chat", "summarizer", "quiz", "flashcards", "plan"];
    tabsList.forEach(t => {
        const btn = document.getElementById(`tab-${t}`);
        const cnt = document.getElementById(`content-${t}`);
        if (t === tab) {
            btn.className = "px-5 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center space-x-2 bg-accent-glow text-white shadow-lg";
            cnt.classList.remove("hidden");
        } else {
            btn.className = "px-5 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center space-x-2 text-text-muted hover:text-text-primary";
            cnt.classList.add("hidden");
        }
    });

    // Populate active tab content
    syncWarnings();
    if (state.selectedDocId) {
        if (tab === "summarizer" && !state.summaryData) {
            fetchSummaryData();
        }
    }
}

// ──────────────────────────────────────
// Chat Assistant
// ──────────────────────────────────────
async function loadConversationHistory() {
    try {
        const response = await fetch(`${API_BASE}/conversations`, {
            headers: authHeaders()
        });
        if (response.ok) {
            const data = await response.json();
            const container = document.getElementById("history-container");
            container.innerHTML = "";

            data.conversations.forEach(c => {
                const item = document.createElement("div");
                const isActive = state.conversationId === c.id;
                item.className = `flex justify-between items-center rounded-lg p-2.5 cursor-pointer text-xs transition-colors group ${
                    isActive ? "bg-accent-glow/15 border border-accent-glow/30 text-accent-glow" : "hover:bg-black/[0.03] text-text-muted hover:text-text-primary"
                }`;
                
                item.innerHTML = `
                    <div onclick="selectConversation('${c.id}')" class="truncate pr-2 flex-grow">${c.title}</div>
                    <button onclick="deleteConversation('${c.id}', event)" class="opacity-0 group-hover:opacity-100 hover:text-red-400 text-[16px] shrink-0">🗑️</button>
                `;
                container.appendChild(item);
            });
        }
    } catch (e) {
        console.error(e);
    }
}

function renderChatWelcome() {
    const container = document.getElementById("chat-messages-container");
    container.innerHTML = `
        <div class="h-full flex flex-col items-center justify-center text-center p-8 text-text-muted space-y-4">
            <span class="material-symbols-outlined text-accent-glow text-6xl">chat_bubble</span>
            <h3 class="text-xl font-bold text-text-primary">Chat Assistant</h3>
            <p class="text-xs max-w-[400px]">Select a document to scope search, or chat with all documents. Ask any questions and we'll reply with page source citations.</p>
        </div>
    `;
}

async function selectConversation(convId) {
    state.conversationId = convId;
    loadConversationHistory();

    const container = document.getElementById("chat-messages-container");
    container.innerHTML = `<div class="p-8 text-center text-xs text-text-muted animate-pulse">Loading messages...</div>`;

    try {
        const response = await fetch(`${API_BASE}/conversations/${convId}`, {
            headers: authHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            container.innerHTML = "";
            data.messages.forEach(msg => {
                appendChatMessage(msg.role, msg.content, msg.sources);
            });
        }
    } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-xs text-red-400">Failed to load conversation.</div>`;
    }
}

async function deleteConversation(convId, event) {
    event.stopPropagation();
    if (!confirm("Delete this conversation?")) return;

    try {
        const response = await fetch(`${API_BASE}/conversations/${convId}`, {
            method: "DELETE",
            headers: authHeaders()
        });

        if (response.ok) {
            if (state.conversationId === convId) {
                state.conversationId = null;
                renderChatWelcome();
            }
            loadConversationHistory();
        }
    } catch (e) {
        alert("Failed to delete conversation.");
    }
}

function startNewChat() {
    state.conversationId = null;
    loadConversationHistory();
    renderChatWelcome();
}

function appendChatMessage(role, content, sources = []) {
    const container = document.getElementById("chat-messages-container");
    
    // Remove welcome state if present
    if (container.querySelector(".text-text-muted")) {
        container.innerHTML = "";
    }

    const bubble = document.createElement("div");
    
    if (role === "user") {
        bubble.className = "flex justify-end";
        bubble.innerHTML = `
            <div class="bg-[#f1ece4] text-[#191919] rounded-2xl rounded-tr-sm px-4 py-3 text-sm max-w-[80%] border border-[#e5e0d8] break-words shadow-sm">
                ${content}
            </div>
        `;
    } else {
        bubble.className = "flex justify-start";
        
        let sourcesHtml = "";
        if (sources && sources.length > 0) {
            const cited = sources.filter(s => s.cited_in_answer);
            const supporting = sources.filter(s => !s.cited_in_answer);

            if (cited.length > 0) {
                const list = cited.map(s => `Page ${s.page_number}`).join(", ");
                sourcesHtml += `<div class="text-[10px] text-accent-glow font-bold mt-2 flex items-center space-x-1">
                    <span class="material-symbols-outlined text-xs">bookmark</span>
                    <span>Cited: ${list}</span>
                </div>`;
            }
            if (supporting.length > 0) {
                const list = supporting.map(s => `Page ${s.page_number}`).join(", ");
                sourcesHtml += `<div class="text-[10px] text-text-muted mt-1 flex items-center space-x-1">
                    <span class="material-symbols-outlined text-xs">attachment</span>
                    <span>Supporting context: ${list}</span>
                </div>`;
            }
        }

        bubble.innerHTML = `
            <div class="bg-panel-bg border border-[#e5e0d8] shadow-sm text-text-primary rounded-2xl rounded-tl-sm px-4 py-3 text-sm max-w-[80%] break-words">
                <div class="whitespace-pre-wrap leading-relaxed">${content}</div>
                ${sourcesHtml}
            </div>
        `;
    }

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

async function handleChatSubmit(event) {
    event.preventDefault();
    const input = document.getElementById("chat-input");
    const query = input.value.trim();
    if (!query) return;

    input.value = "";
    appendChatMessage("user", query);

    // Append loading spinner
    const container = document.getElementById("chat-messages-container");
    const loader = document.createElement("div");
    loader.className = "flex justify-start";
    loader.innerHTML = `
        <div class="bg-panel-bg border border-[#e5e0d8] shadow-sm rounded-2xl rounded-tl-sm px-4 py-3 text-xs text-text-muted flex items-center space-x-2 animate-pulse">
            <svg class="animate-spin h-4 w-4 text-accent-glow" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <span>Searching and drafting response...</span>
        </div>
    `;
    container.appendChild(loader);
    container.scrollTop = container.scrollHeight;

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...authHeaders()
            },
            body: JSON.stringify({
                question: query,
                document_id: state.selectedDocId,
                conversation_id: state.conversationId
            })
        });

        loader.remove();
        const data = await response.json();

        if (response.ok) {
            const isNew = !state.conversationId;
            state.conversationId = data.conversation_id;
            appendChatMessage("assistant", data.answer, data.sources);
            if (isNew) loadConversationHistory();
        } else {
            appendChatMessage("assistant", `❌ Error: ${data.detail || "Failed to process chat query."}`);
        }
    } catch (e) {
        loader.remove();
        appendChatMessage("assistant", "❌ Network error. Check console.");
    }
}

// ──────────────────────────────────────
// Summarizer
// ──────────────────────────────────────
async function fetchSummaryData() {
    const container = document.getElementById("summary-points-container");
    container.innerHTML = `<div class="text-center text-xs text-text-muted py-10 animate-pulse">Compiling keypoints from document...</div>`;
    
    try {
        const response = await fetch(`${API_BASE}/documents/${state.selectedDocId}/summary`, {
            method: "POST",
            headers: authHeaders()
        });

        const data = await response.json();

        if (response.ok) {
            state.summaryData = data;
            state.summaryDocId = state.selectedDocId;
            renderSummary();
        } else {
            container.innerHTML = `<div class="text-center text-xs text-red-400 py-10">⚠️ ${data.detail || "Failed to generate summary."}</div>`;
        }
    } catch (e) {
        container.innerHTML = `<div class="text-center text-xs text-red-400 py-10">Network connection error.</div>`;
    }
}

function renderSummary() {
    document.getElementById("summary-title").innerText = state.summaryData.title;
    
    const container = document.getElementById("summary-points-container");
    container.innerHTML = "";

    state.summaryData.summary_points.forEach(point => {
        const item = document.createElement("div");
        item.className = "flex items-start space-x-3 p-4 bg-panel-bg border border-[#e5e0d8] shadow-sm rounded-2xl hover:border-accent-glow/20 transition-all";
        item.innerHTML = `
            <span class="material-symbols-outlined text-accent-glow text-xl shrink-0 mt-0.5">tips_and_updates</span>
            <p class="text-sm leading-relaxed">${point}</p>
        `;
        container.appendChild(item);
    });
}

function downloadSummaryPDF() {
    if (!state.selectedDocId) return;
    const url = `${API_BASE}/documents/${state.selectedDocId}/export-summary`;

    const link = document.createElement("a");
    link.href = url;
    // Set headers dynamically using browser download redirect isn't trivial, so we fetch it
    fetch(url, { headers: authHeaders() })
        .then(res => res.blob())
        .then(blob => {
            const blobUrl = window.URL.createObjectURL(blob);
            link.href = blobUrl;
            link.download = `summary-${state.selectedDocId.substring(0,6)}.pdf`;
            link.click();
            window.URL.revokeObjectURL(blobUrl);
        })
        .catch(err => alert("Failed to download PDF summary."));
}

// ──────────────────────────────────────
// Practice Quizzes
// ──────────────────────────────────────
async function triggerQuizGeneration() {
    const numQ = parseInt(document.getElementById("quiz-count-input").value) || 10;
    const configBox = document.getElementById("quiz-config-box");
    const activeBox = document.getElementById("quiz-active-box");
    
    configBox.innerHTML = `<div class="py-10 space-y-4">
        <svg class="animate-spin h-8 w-8 text-accent-glow mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <p class="text-xs text-text-muted">Drafting quiz questions...</p>
    </div>`;

    try {
        const response = await fetch(`${API_BASE}/documents/${state.selectedDocId}/quiz?num_questions=${numQ}`, {
            method: "POST",
            headers: authHeaders()
        });

        const data = await response.json();

        if (response.ok) {
            state.quizData = data.questions;
            state.quizDocId = state.selectedDocId;
            state.quizAnswers = {};
            state.quizChecked = {};
            
            // Render
            configBox.classList.add("hidden");
            activeBox.classList.remove("hidden");
            renderActiveQuiz();
        } else {
            alert(data.detail || "Failed to generate quiz.");
            resetQuiz();
        }
    } catch (e) {
        alert("Network error.");
        resetQuiz();
    }
}

function renderActiveQuiz() {
    const list = document.getElementById("quiz-questions-list");
    list.innerHTML = "";
    
    state.quizData.forEach((q, idx) => {
        const card = document.createElement("div");
        card.className = "p-6 glass-panel rounded-3xl border border-[#e5e0d8] shadow-sm space-y-4";
        
        // Build options HTML
        let optionsHtml = "";
        q.options.forEach((opt, optIdx) => {
            const isSelected = state.quizAnswers[idx] === optIdx;
            const isChecked = state.quizChecked[idx];
            let optClass = "flex items-center space-x-3 p-3.5 rounded-2xl border text-sm w-full text-left transition-all ";
            
            if (isChecked) {
                if (optIdx === q.correct_option) {
                    optClass += "bg-[#f0f7f0] border-[#d5ecd5] text-[#2c5a27]";
                } else if (isSelected) {
                    optClass += "bg-[#fcf0f0] border-[#ecd5d5] text-[#9c3a3a]";
                } else {
                    optClass += "bg-black/[0.02] border-[#e5e0d8] text-text-muted";
                }
            } else {
                optClass += isSelected 
                    ? "bg-accent-glow/10 border-accent-glow text-accent-glow" 
                    : "bg-panel-bg border-black/10 hover:border-accent-glow/30 text-text-primary";
            }

            optionsHtml += `
                <button onclick="selectQuizOption(${idx}, ${optIdx})" ${isChecked ? "disabled" : ""} class="${optClass}">
                    <span class="w-5 h-5 rounded-full border border-black/10 flex items-center justify-center text-[10px] uppercase font-bold shrink-0">
                        ${String.fromCharCode(65 + optIdx)}
                    </span>
                    <span>${opt}</span>
                </button>
            `;
        });

        // Explanation text box
        let expHtml = "";
        if (state.quizChecked[idx]) {
            const userChoice = state.quizAnswers[idx];
            const isCorrect = userChoice === q.correct_option;
            
            expHtml = `
                <div class="mt-4 p-4 rounded-2xl text-xs space-y-2 ${isCorrect ? "bg-[#f0f7f0] text-[#2c5a27] border border-[#d5ecd5]" : "bg-[#fcf0f0] text-[#9c3a3a] border border-[#ecd5d5]"}">
                    <p class="font-bold">${isCorrect ? "✅ Correct!" : "❌ Incorrect"}</p>
                    <p class="leading-relaxed"><strong>Explanation:</strong> ${q.explanation}</p>
                </div>
            `;
        }

        const showCheckBtn = state.quizAnswers[idx] !== undefined && !state.quizChecked[idx];

        card.innerHTML = `
            <div class="text-xs font-bold text-accent-glow">QUESTION ${idx + 1} OF ${state.quizData.length}</div>
            <h4 class="text-sm font-semibold leading-relaxed">${q.question}</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">${optionsHtml}</div>
            ${showCheckBtn ? `<button onclick="checkQuizQuestion(${idx})" class="mt-3 bg-accent-blue hover:bg-accent-glow text-white text-xs font-semibold px-5 py-2.5 rounded-full transition-colors">Check Answer</button>` : ""}
            ${expHtml}
        `;
        list.appendChild(card);
    });

    // Score display handling
    const checkedCount = Object.keys(state.quizChecked).length;
    if (checkedCount > 0) {
        let correctCount = 0;
        Object.keys(state.quizChecked).forEach(key => {
            const idx = parseInt(key);
            if (state.quizAnswers[idx] === state.quizData[idx].correct_option) correctCount++;
        });

        const scoreDiv = document.getElementById("quiz-score-display");
        scoreDiv.classList.remove("hidden");
        document.getElementById("quiz-score-metric").innerText = `${correctCount} / ${state.quizData.length}`;
    } else {
        document.getElementById("quiz-score-display").classList.add("hidden");
    }
}

function selectQuizOption(qIdx, optIdx) {
    state.quizAnswers[qIdx] = optIdx;
    renderActiveQuiz();
}

function checkQuizQuestion(qIdx) {
    state.quizChecked[qIdx] = true;
    renderActiveQuiz();
}

function resetQuiz() {
    state.quizData = null;
    state.quizDocId = null;
    
    const configBox = document.getElementById("quiz-config-box");
    configBox.innerHTML = `
        <span class="material-symbols-outlined text-5xl text-accent-glow">quiz</span>
        <h3 class="text-xl font-bold">Generate Practice Quiz</h3>
        <p class="text-text-muted text-xs">Choose the length of your practice test. Questions are dynamically compiled based on your PDF contents.</p>
        <div class="flex items-center justify-center space-x-4">
            <label class="text-xs font-semibold text-text-muted">Questions count:</label>
            <input type="number" id="quiz-count-input" value="10" min="5" max="20" class="w-20 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-center text-sm focus:border-accent-glow focus:ring-0 focus:outline-none"/>
        </div>
        <button onclick="triggerQuizGeneration()" class="w-full bg-accent-glow text-white text-xs font-semibold py-3.5 rounded-xl hover:opacity-90 active:scale-95 transition-all">
            Create Practice Quiz
        </button>
    `;
    
    syncWarnings();
}

// ──────────────────────────────────────
// Flashcards
// ──────────────────────────────────────
async function triggerFlashcardGeneration() {
    const configBox = document.getElementById("flashcards-config-box");
    const activeBox = document.getElementById("flashcards-active-box");
    
    configBox.innerHTML = `<div class="py-10 space-y-4">
        <svg class="animate-spin h-8 w-8 text-accent-glow mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <p class="text-xs text-text-muted">Compiling deck cards...</p>
    </div>`;

    try {
        const response = await fetch(`${API_BASE}/documents/${state.selectedDocId}/flashcards`, {
            method: "POST",
            headers: authHeaders()
        });

        const data = await response.json();

        if (response.ok) {
            state.flashcardData = data.flashcards;
            state.flashcardDocId = state.selectedDocId;
            state.flashcardIndex = 0;
            state.flashcardFlipped = false;

            configBox.classList.add("hidden");
            activeBox.classList.remove("hidden");
            renderActiveFlashcard();
        } else {
            alert(data.detail || "Failed to generate flashcards.");
            resetFlashcards();
        }
    } catch (e) {
        alert("Network error.");
        resetFlashcards();
    }
}

function renderActiveFlashcard() {
    const card = state.flashcardData[state.flashcardIndex];
    document.getElementById("flashcard-question-text").innerText = card.question;
    document.getElementById("flashcard-answer-text").innerText = card.answer;
    
    // Update counter
    document.getElementById("flashcard-counter").innerText = `Card ${state.flashcardIndex + 1} of ${state.flashcardData.length}`;
    
    // Reset flip animations
    const inner = document.getElementById("flashcard-inner");
    if (state.flashcardFlipped) {
        inner.classList.add("card-flipped");
    } else {
        inner.classList.remove("card-flipped");
    }

    // Toggle button disabled classes
    document.getElementById("flashcard-prev-btn").disabled = state.flashcardIndex === 0;
    document.getElementById("flashcard-next-btn").disabled = state.flashcardIndex === state.flashcardData.length - 1;
    document.getElementById("flashcard-prev-btn").style.opacity = state.flashcardIndex === 0 ? "0.4" : "1";
    document.getElementById("flashcard-next-btn").style.opacity = state.flashcardIndex === state.flashcardData.length - 1 ? "0.4" : "1";
}

function flipFlashcard() {
    state.flashcardFlipped = !state.flashcardFlipped;
    const inner = document.getElementById("flashcard-inner");
    inner.classList.toggle("card-flipped", state.flashcardFlipped);
}

function prevFlashcard() {
    if (state.flashcardIndex > 0) {
        state.flashcardIndex--;
        state.flashcardFlipped = false;
        renderActiveFlashcard();
    }
}

function nextFlashcard() {
    if (state.flashcardIndex < state.flashcardData.length - 1) {
        state.flashcardIndex++;
        state.flashcardFlipped = false;
        renderActiveFlashcard();
    }
}

function resetFlashcards() {
    state.flashcardData = null;
    state.flashcardDocId = null;

    const configBox = document.getElementById("flashcards-config-box");
    configBox.innerHTML = `
        <span class="material-symbols-outlined text-5xl text-accent-glow">style</span>
        <h3 class="text-xl font-bold">Generate Study Flashcards</h3>
        <p class="text-text-muted text-xs">Create an interactive deck of flashcards from the text concepts.</p>
        <button onclick="triggerFlashcardGeneration()" class="w-full bg-accent-glow text-white text-xs font-semibold py-3.5 rounded-xl hover:opacity-90 active:scale-95 transition-all">
            Create Card Deck
        </button>
    `;
    
    syncWarnings();
}

// ──────────────────────────────────────
// Study Schedule Plan
// ──────────────────────────────────────
async function triggerPlanGeneration() {
    const days = parseInt(document.getElementById("plan-days-input").value) || 7;
    const configBox = document.getElementById("plan-config-box");
    const activeBox = document.getElementById("plan-active-box");
    
    configBox.innerHTML = `<div class="py-10 space-y-4">
        <svg class="animate-spin h-8 w-8 text-accent-glow mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <p class="text-xs text-text-muted">Structuring schedule plans...</p>
    </div>`;

    try {
        const response = await fetch(`${API_BASE}/documents/${state.selectedDocId}/study-plan?days=${days}`, {
            method: "POST",
            headers: authHeaders()
        });

        const data = await response.json();

        if (response.ok) {
            state.planData = data.days;
            state.planDocId = state.selectedDocId;

            configBox.classList.add("hidden");
            activeBox.classList.remove("hidden");
            renderActivePlan();
        } else {
            alert(data.detail || "Failed to generate study plan.");
            resetPlan();
        }
    } catch (e) {
        alert("Network error.");
        resetPlan();
    }
}

function renderActivePlan() {
    const container = document.getElementById("plan-days-container");
    container.innerHTML = "";

    state.planData.forEach(day => {
        const card = document.createElement("div");
        card.className = "glass-panel rounded-2xl p-5 border border-[#e5e0d8] shadow-sm space-y-3";
        
        let tasksHtml = "";
        day.tasks.forEach((task, tIdx) => {
            tasksHtml += `
                <label class="flex items-start space-x-3 text-xs leading-relaxed text-text-muted hover:text-text-primary cursor-pointer select-none">
                    <input type="checkbox" class="mt-0.5 rounded border-black/20 bg-black/[0.03] text-accent-glow focus:ring-0 focus:outline-none"/>
                    <span>${task}</span>
                </label>
            `;
        });

        card.innerHTML = `
            <div class="flex items-center space-x-2 text-accent-glow">
                <span class="material-symbols-outlined text-lg">event</span>
                <h4 class="text-sm font-bold">Day ${day.day}: ${day.topic}</h4>
            </div>
            <div class="space-y-2.5 pl-7 flex flex-col">${tasksHtml}</div>
        `;
        container.appendChild(card);
    });
}

function resetPlan() {
    state.planData = null;
    state.planDocId = null;

    const configBox = document.getElementById("plan-config-box");
    configBox.innerHTML = `
        <span class="material-symbols-outlined text-5xl text-accent-glow">calendar_today</span>
        <h3 class="text-xl font-bold">Generate Custom Study Plan</h3>
        <p class="text-text-muted text-xs">Create a day-by-day plan mapping the document's sections over a defined duration.</p>
        <div class="flex items-center justify-center space-x-4">
            <label class="text-xs font-semibold text-text-muted">Duration (days):</label>
            <input type="number" id="plan-days-input" value="7" min="3" max="14" class="w-20 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-center text-sm focus:border-accent-glow focus:ring-0 focus:outline-none"/>
        </div>
        <button onclick="triggerPlanGeneration()" class="w-full bg-accent-glow text-white text-xs font-semibold py-3.5 rounded-xl hover:opacity-90 active:scale-95 transition-all">
            Create Plan
        </button>
    `;

    syncWarnings();
}
