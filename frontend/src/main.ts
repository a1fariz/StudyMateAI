/**
 * StudyMate AI — Core App TypeScript
 * Overhauled with strict typings, clean structure, and modern practices.
 */

// API Interfaces
interface DocumentInfo {
    id: string;
    original_filename: string;
    status: 'uploaded' | 'processing' | 'processed' | 'failed';
    total_pages?: number;
    total_chunks?: number;
}

interface ConversationInfo {
    id: string;
    title: string;
}

interface MessageInfo {
    role: 'user' | 'assistant';
    content: string;
    sources?: Array<{
        page_number: number;
        cited_in_answer: boolean;
    }>;
}

interface QuizQuestion {
    question: string;
    options: string[];
    correct_option: number;
    explanation: string;
}

interface Flashcard {
    question: string;
    answer: string;
}

interface StudyPlanDay {
    day: number;
    topic: string;
    tasks: string[];
}

interface AppState {
    token: string | null;
    username: string | null;
    selectedDocId: string | null;
    activeTab: 'chat' | 'summarizer' | 'quiz' | 'flashcards' | 'plan';
    conversationId: string | null;
    // Summarizer state
    summaryData: { title: string; summary_points: string[] } | null;
    summaryDocId: string | null;
    // Quiz state
    quizData: QuizQuestion[] | null;
    quizDocId: string | null;
    quizAnswers: Record<number, number>;
    quizChecked: Record<number, boolean>;
    // Flashcard state
    flashcardData: Flashcard[] | null;
    flashcardDocId: string | null;
    flashcardIndex: number;
    flashcardFlipped: boolean;
    // Plan state
    planData: StudyPlanDay[] | null;
    planDocId: string | null;
}

// Dynamic API Base URL detection
const API_BASE = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
    ? "http://localhost:8001/api/v1"
    : `${window.location.origin}/api/v1`;

// Application State Initializer
const state: AppState = {
    token: localStorage.getItem("token") || null,
    username: localStorage.getItem("username") || null,
    selectedDocId: null,
    activeTab: "chat",
    conversationId: null,
    summaryData: null,
    summaryDocId: null,
    quizData: null,
    quizDocId: null,
    quizAnswers: {},
    quizChecked: {},
    flashcardData: null,
    flashcardDocId: null,
    flashcardIndex: 0,
    flashcardFlipped: false,
    planData: null,
    planDocId: null
};

// ──────────────────────────────────────
// Helper Functions for Safe Element Updates
// ──────────────────────────────────────
function getElement<T extends HTMLElement>(id: string): T {
    const el = document.getElementById(id);
    if (!el) {
        throw new Error(`Required element with id "${id}" was not found in the DOM.`);
    }
    return el as T;
}

function showElement(id: string): void {
    const el = document.getElementById(id);
    if (el) {
        el.classList.remove("hidden");
        el.classList.add("block");
    }
}

function hideElement(id: string): void {
    const el = document.getElementById(id);
    if (el) {
        el.classList.add("hidden");
        el.classList.remove("block");
    }
}

// Helper for HTTP Auth Headers
function authHeaders(): Record<string, string> {
    return state.token ? { "Authorization": `Bearer ${state.token}` } : {};
}

// ──────────────────────────────────────
// Lifecycle & Navigation
// ──────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
    initApp();
    setupEventListeners();
});

function initApp(): void {
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

function showView(view: "workspace" | "landing"): void {
    const landing = getElement("landing-view");
    const workspace = getElement("workspace-view");
    
    if (view === "workspace") {
        landing.classList.add("hidden");
        workspace.classList.remove("hidden");
        document.body.classList.remove("overflow-y-auto");
        document.body.classList.add("overflow-hidden");
    } else {
        landing.classList.remove("hidden");
        workspace.classList.add("hidden");
        document.body.classList.add("overflow-y-auto");
        document.body.classList.remove("overflow-hidden");
    }
}

function setupEventListeners(): void {
    // Dropzone setup
    const dropzone = document.getElementById("upload-zone");
    if (dropzone) {
        dropzone.addEventListener("dragover", (e: DragEvent) => {
            e.preventDefault();
            dropzone.classList.add("border-indigo-500", "bg-indigo-500/5");
        });
        dropzone.addEventListener("dragleave", () => {
            dropzone.classList.remove("border-indigo-500", "bg-indigo-500/5");
        });
        dropzone.addEventListener("drop", (e: DragEvent) => {
            e.preventDefault();
            dropzone.classList.remove("border-indigo-500", "bg-indigo-500/5");
            const files = e.dataTransfer?.files;
            if (files && files.length > 0) {
                const file = files[0];
                if (file.type === "application/pdf") {
                    uploadDocument(file);
                } else {
                    alert("Please drop a valid PDF file.");
                }
            }
        });
        dropzone.addEventListener("click", () => {
            const fileInput = getElement<HTMLInputElement>("file-input");
            fileInput.click();
        });
    }

    // Bind forms
    const loginForm = document.getElementById("login-form");
    if (loginForm) loginForm.addEventListener("submit", handleLoginSubmit);

    const registerForm = document.getElementById("register-form");
    if (registerForm) registerForm.addEventListener("submit", handleRegisterSubmit);

    const chatForm = document.getElementById("chat-form-el");
    if (chatForm) chatForm.addEventListener("submit", handleChatSubmit);
}

// ──────────────────────────────────────
// Authentication Flow
// ──────────────────────────────────────
(window as any).openAuthModal = function(tab: "login" | "register" = "login"): void {
    showElement("auth-modal");
    (window as any).switchAuthTab(tab);
};

(window as any).closeAuthModal = function(): void {
    hideElement("auth-modal");
    hideElement("auth-error");
};

(window as any).switchAuthTab = function(tab: "login" | "register"): void {
    const loginForm = getElement("login-form");
    const registerForm = getElement("register-form");
    const loginBtn = getElement("tab-login-btn");
    const registerBtn = getElement("tab-register-btn");
    hideElement("auth-error");

    if (tab === "login") {
        loginForm.classList.remove("hidden");
        registerForm.classList.add("hidden");
        loginBtn.className = "text-lg font-bold border-b-2 border-indigo-500 pb-2 focus:outline-none text-white";
        registerBtn.className = "text-lg font-bold text-brand-textMuted pb-2 focus:outline-none hover:text-white transition-colors";
    } else {
        loginForm.classList.add("hidden");
        registerForm.classList.remove("hidden");
        loginBtn.className = "text-lg font-bold text-brand-textMuted pb-2 focus:outline-none hover:text-white transition-colors";
        registerBtn.className = "text-lg font-bold border-b-2 border-indigo-500 pb-2 focus:outline-none text-white";
    }
};

async function handleLoginSubmit(event: Event): Promise<void> {
    event.preventDefault();
    const errorBanner = getElement("auth-error");
    errorBanner.classList.add("hidden");

    const usernameInput = getElement<HTMLInputElement>("login-username").value.trim();
    const passwordInput = getElement<HTMLInputElement>("login-password").value;

    try {
        const formData = new URLSearchParams();
        formData.append("username", usernameInput);
        formData.append("password", passwordInput);

        const response = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData.toString()
        });

        const data = await response.json();

        if (response.ok) {
            state.token = data.access_token;
            state.username = usernameInput;
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("username", usernameInput);
            (window as any).closeAuthModal();
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

async function handleRegisterSubmit(event: Event): Promise<void> {
    event.preventDefault();
    const errorBanner = getElement("auth-error");
    errorBanner.classList.add("hidden");

    const email = getElement<HTMLInputElement>("reg-email").value.trim();
    const username = getElement<HTMLInputElement>("reg-username").value.trim();
    const password = getElement<HTMLInputElement>("reg-password").value;

    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, username, password })
        });

        const data = await response.json();

        if (response.ok) {
            (window as any).switchAuthTab("login");
            getElement<HTMLInputElement>("login-username").value = username;
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

(window as any).handleLogout = function(): void {
    state.token = null;
    state.username = null;
    state.selectedDocId = null;
    state.conversationId = null;
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    showView("landing");
};

function loadUserProfile(): void {
    const userDisplay = getElement("user-display-name");
    const userAvatar = getElement("user-avatar-initial");
    
    if (state.username) {
        userDisplay.innerText = state.username;
        userAvatar.innerText = state.username[0].toUpperCase();
    }
}

// ──────────────────────────────────────
// Document Management
// ──────────────────────────────────────
async function loadDocumentsList(): Promise<void> {
    try {
        const response = await fetch(`${API_BASE}/documents/`, {
            headers: authHeaders()
        });
        if (response.ok) {
            const data = await response.json();
            const select = getElement<HTMLSelectElement>("doc-context-select");
            
            select.innerHTML = '<option value="all">🌐 All Documents</option>';
            
            data.documents.forEach((doc: DocumentInfo) => {
                const opt = document.createElement("option");
                opt.value = doc.id;
                const statusEmoji = doc.status === "processed" ? "✅" : (doc.status === "failed" ? "❌" : "⏳");
                opt.innerText = `${statusEmoji} ${doc.original_filename.substring(0, 24)}`;
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

(window as any).handleDocSelectionChange = function(): void {
    const val = getElement<HTMLSelectElement>("doc-context-select").value;
    state.selectedDocId = val === "all" ? null : val;
    
    resetSmartFeatureStates();
    syncWarnings();
    
    if (state.selectedDocId && state.activeTab === "summarizer") {
        fetchSummaryData();
    }
};

function resetSmartFeatureStates(): void {
    state.summaryData = null;
    state.quizData = null;
    state.flashcardData = null;
    state.planData = null;
}

function syncWarnings(): void {
    const isDocSelected = !!state.selectedDocId;
    
    // Summarizer warning
    if (isDocSelected) {
        hideElement("summary-warning");
        showElement("summary-box");
    } else {
        showElement("summary-warning");
        hideElement("summary-box");
    }

    // Quiz warning
    if (isDocSelected) {
        hideElement("quiz-warning");
        if (state.quizData) {
            hideElement("quiz-config-box");
            showElement("quiz-active-box");
        } else {
            showElement("quiz-config-box");
            hideElement("quiz-active-box");
        }
    } else {
        showElement("quiz-warning");
        hideElement("quiz-config-box");
        hideElement("quiz-active-box");
    }

    // Flashcards warning
    if (isDocSelected) {
        hideElement("flashcards-warning");
        if (state.flashcardData) {
            hideElement("flashcards-config-box");
            showElement("flashcards-active-box");
        } else {
            showElement("flashcards-config-box");
            hideElement("flashcards-active-box");
        }
    } else {
        showElement("flashcards-warning");
        hideElement("flashcards-config-box");
        hideElement("flashcards-active-box");
    }

    // Study Plan warning
    if (isDocSelected) {
        hideElement("plan-warning");
        if (state.planData) {
            hideElement("plan-config-box");
            showElement("plan-active-box");
        } else {
            showElement("plan-config-box");
            hideElement("plan-active-box");
        }
    } else {
        showElement("plan-warning");
        hideElement("plan-config-box");
        hideElement("plan-active-box");
    }
}

// ──────────────────────────────────────
// File Upload & Processing
// ──────────────────────────────────────
(window as any).handleFileSelect = function(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) uploadDocument(file);
};

async function uploadDocument(file: File): Promise<void> {
    const banner = getElement("status-banner");
    banner.classList.remove("hidden");
    banner.className = "mt-3 p-3 rounded-2xl text-[11px] border border-indigo-500/20 bg-indigo-950/20 text-indigo-200";
    banner.innerHTML = `<div class="flex items-center space-x-2">
        <svg class="animate-spin h-4 w-4 text-indigo-400" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
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
                <svg class="animate-spin h-4 w-4 text-brand-accentGlow" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <span>Extracting content & generating vector index...</span>
            </div>`;

            // Auto-trigger processing
            const procResponse = await fetch(`${API_BASE}/documents/${data.id}/process`, {
                method: "POST",
                headers: authHeaders()
            });

            if (procResponse.ok) {
                const procData = await procResponse.json();
                banner.className = "mt-3 p-3 rounded-2xl text-[11px] border border-emerald-500/20 bg-emerald-950/20 text-emerald-300";
                banner.innerHTML = `✅ Indexed ${procData.total_chunks} chunks successfully!`;
                loadDocumentsList();
            } else {
                const procErr = await procResponse.json();
                banner.className = "mt-3 p-3 rounded-2xl text-[11px] border border-rose-500/20 bg-rose-950/20 text-rose-300";
                banner.innerHTML = `⚠️ Processing failed: ${procErr.detail || "Error"}`;
            }
        } else {
            banner.className = "mt-3 p-3 rounded-2xl text-[11px] border border-rose-500/20 bg-rose-950/20 text-rose-300";
            banner.innerHTML = `❌ Upload failed: ${data.detail || "Error"}`;
        }
    } catch (e) {
        banner.className = "mt-3 p-3 rounded-2xl text-[11px] border border-rose-500/20 bg-rose-950/20 text-rose-300";
        banner.innerHTML = "Connection error.";
    }
}

// ──────────────────────────────────────
// Tab Navigation
// ──────────────────────────────────────
(window as any).switchWorkspaceTab = function(tab: AppState['activeTab']): void {
    state.activeTab = tab;

    const tabsList: AppState['activeTab'][] = ["chat", "summarizer", "quiz", "flashcards", "plan"];
    tabsList.forEach(t => {
        const btn = getElement(`tab-${t}`);
        const cnt = getElement(`content-${t}`);
        if (t === tab) {
            btn.className = "px-5 py-2.5 rounded-full text-sm font-semibold transition-all flex items-center space-x-2 bg-indigo-600 text-white shadow-lg shadow-indigo-600/20";
            cnt.classList.remove("hidden");
            cnt.classList.add("block");
        } else {
            btn.className = "px-5 py-2.5 rounded-full text-sm font-semibold transition-all flex items-center space-x-2 text-brand-textMuted hover:text-white hover:bg-white/5";
            cnt.classList.add("hidden");
            cnt.classList.remove("block");
        }
    });

    syncWarnings();
    if (state.selectedDocId) {
        if (tab === "summarizer" && !state.summaryData) {
            fetchSummaryData();
        }
    }
};

// ──────────────────────────────────────
// Chat Assistant
// ──────────────────────────────────────
async function loadConversationHistory(): Promise<void> {
    try {
        const response = await fetch(`${API_BASE}/conversations`, {
            headers: authHeaders()
        });
        if (response.ok) {
            const data = await response.json();
            const container = getElement("history-container");
            container.innerHTML = "";

            data.conversations.forEach((c: ConversationInfo) => {
                const item = document.createElement("div");
                const isActive = state.conversationId === c.id;
                item.className = `flex justify-between items-center rounded-xl p-2.5 cursor-pointer text-xs transition-all border group ${
                    isActive 
                        ? "bg-indigo-950/35 border-indigo-500/30 text-indigo-300 shadow-sm" 
                        : "border-transparent hover:bg-white/5 text-brand-textMuted hover:text-white"
                }`;
                
                item.innerHTML = `
                    <div class="truncate pr-2 flex-grow flex items-center space-x-2" onclick="selectConversation('${c.id}')">
                        <span class="material-symbols-outlined text-sm ${isActive ? 'text-indigo-400' : 'text-brand-textMuted'}">chat_bubble</span>
                        <span class="truncate">${c.title}</span>
                    </div>
                    <button onclick="deleteConversation('${c.id}', event)" class="opacity-0 group-hover:opacity-100 hover:text-rose-400 text-base shrink-0 p-1 flex items-center transition-opacity" title="Delete conversation">
                        <span class="material-symbols-outlined text-sm">delete</span>
                    </button>
                `;
                container.appendChild(item);
            });
        }
    } catch (e) {
        console.error(e);
    }
}

function renderChatWelcome(): void {
    const container = getElement("chat-messages-container");
    container.innerHTML = `
        <div class="h-full flex flex-col items-center justify-center text-center p-8 text-brand-textMuted space-y-4 max-w-[500px] mx-auto mt-16">
            <div class="w-16 h-16 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                <span class="material-symbols-outlined text-indigo-400 text-3xl">chat_bubble</span>
            </div>
            <h3 class="text-xl font-bold text-white">Ask your Documents</h3>
            <p class="text-xs leading-relaxed">Select a document in the sidebar to narrow the RAG scope, or ask across all materials. The AI will reply with citations grounded in your book pages.</p>
        </div>
    `;
}

(window as any).selectConversation = async function(convId: string): Promise<void> {
    state.conversationId = convId;
    loadConversationHistory();

    const container = getElement("chat-messages-container");
    container.innerHTML = `<div class="p-8 text-center text-xs text-brand-textMuted animate-pulse">Loading messages...</div>`;

    try {
        const response = await fetch(`${API_BASE}/conversations/${convId}`, {
            headers: authHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            container.innerHTML = "";
            data.messages.forEach((msg: MessageInfo) => {
                appendChatMessage(msg.role, msg.content, msg.sources);
            });
        }
    } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-xs text-rose-400">Failed to load conversation.</div>`;
    }
};

(window as any).deleteConversation = async function(convId: string, event: Event): Promise<void> {
    event.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat history?")) return;

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
};

(window as any).startNewChat = function(): void {
    state.conversationId = null;
    loadConversationHistory();
    renderChatWelcome();
};

function appendChatMessage(role: 'user' | 'assistant', content: string, sources: MessageInfo['sources'] = []): void {
    const container = getElement("chat-messages-container");
    
    // Remove welcome view if present
    if (container.querySelector(".text-brand-textMuted")) {
        container.innerHTML = "";
    }

    const bubble = document.createElement("div");
    
    if (role === "user") {
        bubble.className = "flex justify-end mb-4 animate-fade-in";
        bubble.innerHTML = `
            <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm max-w-[80%] break-words shadow-md shadow-indigo-600/10">
                ${content}
            </div>
        `;
    } else {
        bubble.className = "flex justify-start mb-4 animate-fade-in";
        
        let sourcesHtml = "";
        if (sources && sources.length > 0) {
            const cited = sources.filter(s => s.cited_in_answer);
            const supporting = sources.filter(s => !s.cited_in_answer);

            let citedHtml = "";
            if (cited.length > 0) {
                const list = cited.map(s => `<span class="bg-brand-accentGlow/10 border border-brand-accentGlow/25 text-brand-accentGlow px-2 py-0.5 rounded text-[10px]">Page ${s.page_number}</span>`).join(" ");
                citedHtml = `
                    <div class="text-[10px] text-brand-accentGlow font-semibold flex items-center space-x-1.5">
                        <span class="material-symbols-outlined text-xs">bookmark</span>
                        <span>Cited sources:</span>
                        <div class="flex flex-wrap gap-1">${list}</div>
                    </div>
                `;
            }

            let supportingHtml = "";
            if (supporting.length > 0) {
                const list = supporting.map(s => `<span class="bg-white/5 border border-white/10 text-brand-textMuted px-2 py-0.5 rounded text-[10px]">Page ${s.page_number}</span>`).join(" ");
                supportingHtml = `
                    <div class="text-[10px] text-brand-textMuted flex items-center space-x-1.5">
                        <span class="material-symbols-outlined text-xs">attachment</span>
                        <span>Supporting context:</span>
                        <div class="flex flex-wrap gap-1">${list}</div>
                    </div>
                `;
            }

            if (citedHtml || supportingHtml) {
                sourcesHtml = `
                    <div class="mt-3 pt-3 border-t border-brand-border/40 space-y-2">
                        ${citedHtml}
                        ${supportingHtml}
                    </div>
                `;
            }
        }

        bubble.innerHTML = `
            <div class="bg-brand-card border border-brand-border/60 shadow-lg text-slate-100 rounded-2xl rounded-tl-sm px-4 py-3 text-sm max-w-[80%] break-words">
                <div class="whitespace-pre-wrap leading-relaxed">${content}</div>
                ${sourcesHtml}
            </div>
        `;
    }

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

async function handleChatSubmit(event: Event): Promise<void> {
    event.preventDefault();
    const input = getElement<HTMLInputElement>("chat-input");
    const query = input.value.trim();
    if (!query) return;

    input.value = "";
    appendChatMessage("user", query);

    const container = getElement("chat-messages-container");
    const loader = document.createElement("div");
    loader.className = "flex justify-start mb-4";
    loader.innerHTML = `
        <div class="bg-brand-card border border-brand-border/60 shadow-lg rounded-2xl rounded-tl-sm px-4 py-3 text-xs text-brand-textMuted flex items-center space-x-2 animate-pulse">
            <svg class="animate-spin h-4.5 w-4.5 text-indigo-400" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <span>Searching database and draft response...</span>
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
        appendChatMessage("assistant", "❌ Network error. Check connection.");
    }
}

// ──────────────────────────────────────
// Summarizer
// ──────────────────────────────────────
async function fetchSummaryData(): Promise<void> {
    const container = getElement("summary-points-container");
    container.innerHTML = `<div class="text-center text-xs text-brand-textMuted py-16 animate-pulse">Compiling key points from document...</div>`;
    
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
            container.innerHTML = `<div class="text-center text-xs text-rose-400 py-16">⚠️ ${data.detail || "Failed to generate summary."}</div>`;
        }
    } catch (e) {
        container.innerHTML = `<div class="text-center text-xs text-rose-400 py-16">Network connection error.</div>`;
    }
}

function renderSummary(): void {
    if (!state.summaryData) return;
    getElement("summary-title").innerText = state.summaryData.title;
    
    const container = getElement("summary-points-container");
    container.innerHTML = "";

    state.summaryData.summary_points.forEach(point => {
        const item = document.createElement("div");
        item.className = "flex items-start space-x-3 p-4 bg-brand-card/60 border border-brand-border/50 shadow-md rounded-2xl hover:border-indigo-500/30 transition-all duration-300";
        item.innerHTML = `
            <span class="material-symbols-outlined text-indigo-400 text-xl shrink-0 mt-0.5">tips_and_updates</span>
            <p class="text-sm leading-relaxed text-slate-200">${point}</p>
        `;
        container.appendChild(item);
    });
}

(window as any).downloadSummaryPDF = function(): void {
    if (!state.selectedDocId) return;
    const url = `${API_BASE}/documents/${state.selectedDocId}/export-summary`;

    const link = document.createElement("a");
    fetch(url, { headers: authHeaders() })
        .then(res => res.blob())
        .then(blob => {
            const blobUrl = window.URL.createObjectURL(blob);
            link.href = blobUrl;
            link.download = `summary-${state.selectedDocId?.substring(0, 6)}.pdf`;
            link.click();
            window.URL.revokeObjectURL(blobUrl);
        })
        .catch(() => alert("Failed to download PDF summary."));
};

// ──────────────────────────────────────
// Practice Quizzes
// ──────────────────────────────────────
(window as any).triggerQuizGeneration = async function(): Promise<void> {
    const inputEl = getElement<HTMLInputElement>("quiz-count-input");
    const numQ = parseInt(inputEl.value) || 10;
    const configBox = getElement("quiz-config-box");
    const activeBox = getElement("quiz-active-box");
    
    configBox.innerHTML = `<div class="py-16 space-y-4">
        <svg class="animate-spin h-8 w-8 text-indigo-400 mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <p class="text-xs text-brand-textMuted">Compiling practice questions...</p>
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
            
            configBox.classList.add("hidden");
            activeBox.classList.remove("hidden");
            renderActiveQuiz();
        } else {
            alert(data.detail || "Failed to generate quiz.");
            (window as any).resetQuiz();
        }
    } catch (e) {
        alert("Network error.");
        (window as any).resetQuiz();
    }
};

function renderActiveQuiz(): void {
    const quizData = state.quizData;
    if (!quizData) return;
    const list = getElement("quiz-questions-list");
    list.innerHTML = "";
    
    quizData.forEach((q, idx) => {
        const card = document.createElement("div");
        card.className = "p-6 bg-brand-card/60 border border-brand-border/60 shadow-md rounded-3xl space-y-4";
        
        let optionsHtml = "";
        q.options.forEach((opt, optIdx) => {
            const isSelected = state.quizAnswers[idx] === optIdx;
            const isChecked = state.quizChecked[idx];
            let optClass = "flex items-center space-x-3 p-3.5 rounded-2xl border text-xs w-full text-left transition-all ";
            
            if (isChecked) {
                if (optIdx === q.correct_option) {
                    optClass += "bg-emerald-950/25 border-emerald-500/30 text-emerald-300";
                } else if (isSelected) {
                    optClass += "bg-rose-950/25 border-rose-500/30 text-rose-300";
                } else {
                    optClass += "bg-white/[0.02] border-brand-border/40 text-brand-textMuted";
                }
            } else {
                optClass += isSelected 
                    ? "bg-indigo-600/20 border-indigo-500 text-indigo-300" 
                    : "bg-brand-card border-brand-border/70 hover:border-brand-border text-slate-200";
            }

            optionsHtml += `
                <button onclick="selectQuizOption(${idx}, ${optIdx})" ${isChecked ? "disabled" : ""} class="${optClass}">
                    <span class="w-5 h-5 rounded-full border border-white/10 flex items-center justify-center text-[10px] font-bold shrink-0 bg-white/5">
                        ${String.fromCharCode(65 + optIdx)}
                    </span>
                    <span class="flex-grow">${opt}</span>
                </button>
            `;
        });

        let expHtml = "";
        if (state.quizChecked[idx]) {
            const userChoice = state.quizAnswers[idx];
            const isCorrect = userChoice === q.correct_option;
            
            expHtml = `
                <div class="mt-4 p-4 rounded-2xl text-xs space-y-2 ${isCorrect ? "bg-emerald-950/30 text-emerald-300 border border-emerald-500/20" : "bg-rose-950/30 text-rose-300 border border-rose-500/20"}">
                    <p class="font-bold flex items-center space-x-1">
                        <span>${isCorrect ? "✅ Correct!" : "❌ Incorrect"}</span>
                    </p>
                    <p class="leading-relaxed"><strong>Explanation:</strong> ${q.explanation}</p>
                </div>
            `;
        }

        const showCheckBtn = state.quizAnswers[idx] !== undefined && !state.quizChecked[idx];

        card.innerHTML = `
            <div class="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Question ${idx + 1} of ${quizData.length}</div>
            <h4 class="text-sm font-semibold leading-relaxed text-slate-100">${q.question}</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">${optionsHtml}</div>
            ${showCheckBtn ? `<button onclick="checkQuizQuestion(${idx})" class="mt-3 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-5 py-2.5 rounded-full transition-colors active:scale-95 shadow-md shadow-indigo-600/10">Check Answer</button>` : ""}
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
            if (state.quizAnswers[idx] === quizData[idx].correct_option) correctCount++;
        });

        const scoreDiv = getElement("quiz-score-display");
        scoreDiv.classList.remove("hidden");
        getElement("quiz-score-metric").innerText = `${correctCount} / ${quizData.length}`;
    } else {
        getElement("quiz-score-display").classList.add("hidden");
    }
}

(window as any).selectQuizOption = function(qIdx: number, optIdx: number): void {
    state.quizAnswers[qIdx] = optIdx;
    renderActiveQuiz();
};

(window as any).checkQuizQuestion = function(qIdx: number): void {
    state.quizChecked[qIdx] = true;
    renderActiveQuiz();
};

(window as any).resetQuiz = function(): void {
    state.quizData = null;
    state.quizDocId = null;
    
    const configBox = getElement("quiz-config-box");
    configBox.innerHTML = `
        <span class="material-symbols-outlined text-5xl text-indigo-400">quiz</span>
        <h3 class="text-xl font-bold text-white">Generate Practice Quiz</h3>
        <p class="text-brand-textMuted text-xs max-w-[400px] mx-auto">Choose the length of your practice test. Questions are dynamically compiled based on your PDF contents.</p>
        <div class="flex items-center justify-center space-x-4 py-2">
            <label class="text-xs font-semibold text-brand-textMuted">Questions count:</label>
            <input type="number" id="quiz-count-input" value="10" min="5" max="20" class="w-20 bg-white/5 border border-brand-border rounded-2xl px-3 py-2 text-center text-sm focus:border-indigo-500 focus:ring-0 focus:outline-none text-white"/>
        </div>
        <button onclick="triggerQuizGeneration()" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-3.5 rounded-full hover:opacity-90 active:scale-95 transition-all">
            Create Practice Quiz
        </button>
    `;
    
    syncWarnings();
};

// ──────────────────────────────────────
// Flashcards
// ──────────────────────────────────────
(window as any).triggerFlashcardGeneration = async function(): Promise<void> {
    const configBox = getElement("flashcards-config-box");
    const activeBox = getElement("flashcards-active-box");
    
    configBox.innerHTML = `<div class="py-16 space-y-4">
        <svg class="animate-spin h-8 w-8 text-indigo-400 mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <p class="text-xs text-brand-textMuted">Compiling card deck...</p>
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
            (window as any).resetFlashcards();
        }
    } catch (e) {
        alert("Network error.");
        (window as any).resetFlashcards();
    }
};

function renderActiveFlashcard(): void {
    if (!state.flashcardData) return;
    const card = state.flashcardData[state.flashcardIndex];
    getElement("flashcard-question-text").innerText = card.question;
    getElement("flashcard-answer-text").innerText = card.answer;
    
    getElement("flashcard-counter").innerText = `Card ${state.flashcardIndex + 1} of ${state.flashcardData.length}`;
    
    const inner = getElement("flashcard-inner");
    if (state.flashcardFlipped) {
        inner.classList.add("card-flipped");
    } else {
        inner.classList.remove("card-flipped");
    }

    const prevBtn = getElement<HTMLButtonElement>("flashcard-prev-btn");
    const nextBtn = getElement<HTMLButtonElement>("flashcard-next-btn");
    
    prevBtn.disabled = state.flashcardIndex === 0;
    nextBtn.disabled = state.flashcardIndex === state.flashcardData.length - 1;
    prevBtn.style.opacity = state.flashcardIndex === 0 ? "0.4" : "1";
    nextBtn.style.opacity = state.flashcardIndex === state.flashcardData.length - 1 ? "0.4" : "1";
}

(window as any).flipFlashcard = function(): void {
    state.flashcardFlipped = !state.flashcardFlipped;
    const inner = getElement("flashcard-inner");
    inner.classList.toggle("card-flipped", state.flashcardFlipped);
};

(window as any).prevFlashcard = function(): void {
    if (state.flashcardIndex > 0) {
        state.flashcardIndex--;
        state.flashcardFlipped = false;
        renderActiveFlashcard();
    }
};

(window as any).nextFlashcard = function(): void {
    if (state.flashcardData && state.flashcardIndex < state.flashcardData.length - 1) {
        state.flashcardIndex++;
        state.flashcardFlipped = false;
        renderActiveFlashcard();
    }
};

(window as any).resetFlashcards = function(): void {
    state.flashcardData = null;
    state.flashcardDocId = null;

    const configBox = getElement("flashcards-config-box");
    configBox.innerHTML = `
        <span class="material-symbols-outlined text-5xl text-indigo-400">style</span>
        <h3 class="text-xl font-bold text-white">Generate Study Flashcards</h3>
        <p class="text-brand-textMuted text-xs max-w-[400px] mx-auto">Create an interactive deck of flashcards from the text concepts.</p>
        <button onclick="triggerFlashcardGeneration()" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-3.5 rounded-full hover:opacity-90 active:scale-95 transition-all">
            Create Card Deck
        </button>
    `;
    
    syncWarnings();
};

// ──────────────────────────────────────
// Study Plan
// ──────────────────────────────────────
(window as any).triggerPlanGeneration = async function(): Promise<void> {
    const daysInput = getElement<HTMLInputElement>("plan-days-input");
    const days = parseInt(daysInput.value) || 7;
    const configBox = getElement("plan-config-box");
    const activeBox = getElement("plan-active-box");
    
    configBox.innerHTML = `<div class="py-16 space-y-4">
        <svg class="animate-spin h-8 w-8 text-indigo-400 mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <p class="text-xs text-brand-textMuted">Structuring study schedule...</p>
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
            (window as any).resetPlan();
        }
    } catch (e) {
        alert("Network error.");
        (window as any).resetPlan();
    }
};

function renderActivePlan(): void {
    if (!state.planData) return;
    const container = getElement("plan-days-container");
    container.innerHTML = "";

    state.planData.forEach(day => {
        const card = document.createElement("div");
        card.className = "p-5 bg-brand-card/60 border border-brand-border/60 shadow-md rounded-2xl space-y-3";
        
        let tasksHtml = "";
        day.tasks.forEach((task) => {
            tasksHtml += `
                <label class="flex items-start space-x-3 text-xs leading-relaxed text-brand-textMuted hover:text-slate-200 cursor-pointer select-none">
                    <input type="checkbox" class="mt-0.5 rounded border-brand-border bg-white/5 text-indigo-600 focus:ring-0 focus:outline-none"/>
                    <span>${task}</span>
                </label>
            `;
        });

        card.innerHTML = `
            <div class="flex items-center space-x-2 text-indigo-400">
                <span class="material-symbols-outlined text-lg">event</span>
                <h4 class="text-sm font-bold">Day ${day.day}: ${day.topic}</h4>
            </div>
            <div class="space-y-2.5 pl-7 flex flex-col">${tasksHtml}</div>
        `;
        container.appendChild(card);
    });
}

(window as any).resetPlan = function(): void {
    state.planData = null;
    state.planDocId = null;

    const configBox = getElement("plan-config-box");
    configBox.innerHTML = `
        <span class="material-symbols-outlined text-5xl text-indigo-400">calendar_today</span>
        <h3 class="text-xl font-bold text-white">Generate Custom Study Plan</h3>
        <p class="text-brand-textMuted text-xs max-w-[400px] mx-auto">Create a day-by-day plan mapping the document's sections over a defined duration.</p>
        <div class="flex items-center justify-center space-x-4 py-2">
            <label class="text-xs font-semibold text-brand-textMuted">Duration (days):</label>
            <input type="number" id="plan-days-input" value="7" min="3" max="14" class="w-20 bg-white/5 border border-brand-border rounded-2xl px-3 py-2 text-center text-sm focus:border-indigo-500 focus:ring-0 focus:outline-none text-white"/>
        </div>
        <button onclick="triggerPlanGeneration()" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-3.5 rounded-full hover:opacity-90 active:scale-95 transition-all">
            Create Plan
        </button>
    `;

    syncWarnings();
};
