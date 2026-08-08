/* ============================================================
   THE INTERVIEW AGENT
   Frontend Application Logic
============================================================ */

"use strict";

/* ============================================================
   CONFIGURATION
============================================================ */

const API_BASE_URL = "http://127.0.0.1:8000";
const API_URL = `${API_BASE_URL}/api/interview`;

const MAX_QUESTIONS = 8;
const MAX_CHARACTERS = 5000;


/* ============================================================
   APPLICATION STATE
============================================================ */

const state = {
    sessionId: null,
    questionCount: 0,
    interviewStarted: false,
    interviewCompleted: false,
    isLoading: false,

    candidate: {
        member: {
            id: "CAND-001",
            name: "Sarah Johnson",
            jobRole: "Senior Data Engineer",
            yearsExperience: 9,
            education: "MS Computer Science",
            status: "COMPLETED"
        },

        missions: [
            {
                day: 7,
                title: "Embeddings Explained",
                passed: true,
                attempts: 1
            },
            {
                day: 8,
                title: "Vector Databases Overview",
                passed: true,
                attempts: 1
            },
            {
                day: 10,
                title: "Retrieval & Matching Engine",
                passed: true,
                attempts: 2
            },
            {
                day: 12,
                title: "Prompt Engineering Fundamentals",
                passed: true,
                attempts: 4
            },
            {
                day: 16,
                title: "Chatbot Backend & API Integration",
                passed: true,
                attempts: 1
            },
            {
                day: 22,
                title: "Multi-Agent Orchestration",
                passed: true,
                attempts: 2
            },
            {
                day: 23,
                title: "Model Context Protocol (MCP)",
                passed: true,
                attempts: 2
            },
            {
                day: 28,
                title: "Docker & Kubernetes Deployment",
                passed: true,
                attempts: 3
            },
            {
                day: 29,
                title: "Monitoring, Logging & Observability",
                skipped: true
            },
            {
                day: 31,
                title: "Capstone Project & Final Demo",
                passed: true,
                attempts: 1
            }
        ],

        signals: {
            commitDays: 28,
            missionsCompleted: 30,
            missionsFirstTry: 20
        }
    }
};


/* ============================================================
   DOM ELEMENTS
============================================================ */

const elements = {

    startScreen:
        document.getElementById("startScreen"),

    interviewScreen:
        document.getElementById("interviewScreen"),

    completionScreen:
        document.getElementById("completionScreen"),

    startInterviewBtn:
        document.getElementById("startInterviewBtn"),

    restartBtn:
        document.getElementById("restartBtn"),

    newInterviewBtn:
        document.getElementById("newInterviewBtn"),

    answerInput:
        document.getElementById("answerInput"),

    sendButton:
        document.getElementById("sendButton"),

    conversation:
        document.getElementById("conversation"),

    thinkingIndicator:
        document.getElementById("thinkingIndicator"),

    questionLabel:
        document.getElementById("questionLabel"),

    progressLabel:
        document.getElementById("progressLabel"),

    progressBar:
        document.getElementById("progressBar"),

    topicBadge:
        document.getElementById("topicBadge"),

    characterCount:
        document.getElementById("characterCount"),

    connectionStatus:
        document.getElementById("connectionStatus"),

    statusText:
        document.getElementById("statusText"),

    themeToggle:
        document.getElementById("themeToggle"),

    candidateName:
        document.getElementById("candidateName"),

    candidateRole:
        document.getElementById("candidateRole"),

    feedbackSummary:
        document.getElementById("feedbackSummary"),

    strengthsList:
        document.getElementById("strengthsList"),

    gapsList:
        document.getElementById("gapsList"),

    nextList:
        document.getElementById("nextList"),

    toast:
        document.getElementById("toast"),

    toastIcon:
        document.getElementById("toastIcon"),

    toastMessage:
        document.getElementById("toastMessage")
};


/* ============================================================
   INITIALIZATION
============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    initializeApplication();
});


function initializeApplication() {

    loadTheme();

    updateCandidatePreview();

    updateCharacterCount();

    setupEventListeners();

    setConnectionStatus("ready");
}


/* ============================================================
   EVENT LISTENERS
============================================================ */

function setupEventListeners() {

    elements.startInterviewBtn?.addEventListener(
        "click",
        startInterview
    );

    elements.sendButton?.addEventListener(
        "click",
        submitAnswer
    );

    elements.restartBtn?.addEventListener(
        "click",
        restartInterview
    );

    elements.newInterviewBtn?.addEventListener(
        "click",
        restartInterview
    );

    elements.answerInput?.addEventListener(
        "input",
        updateCharacterCount
    );

    elements.answerInput?.addEventListener(
        "keydown",
        handleAnswerKeydown
    );

    elements.themeToggle?.addEventListener(
        "click",
        toggleTheme
    );
}


/* ============================================================
   START INTERVIEW
============================================================ */

async function startInterview() {

    if (state.isLoading) {
        return;
    }

    state.sessionId =
        `session-${Date.now()}-${Math.random()
            .toString(36)
            .substring(2, 8)}`;

    state.questionCount = 0;
    state.interviewStarted = false;
    state.interviewCompleted = false;

    clearConversation();

    showScreen("interview");

    setLoading(true);

    setConnectionStatus("connecting");

    try {

        const response =
            await sendInterviewRequest({
                sessionId: state.sessionId,
                candidate: state.candidate
            });

        state.interviewStarted = true;

        state.questionCount = 1;

        addMessage(
            "ai",
            extractReply(response)
        );

        updateProgress();

        setConnectionStatus("connected");

        showToast(
            "Interview started!",
            "✓"
        );

        elements.answerInput?.focus();

    } catch (error) {

        console.error(
            "Start interview error:",
            error
        );

        setConnectionStatus("error");

        showToast(
            getErrorMessage(error),
            "!"
        );

        showScreen("start");

    } finally {

        setLoading(false);
    }
}


/* ============================================================
   SUBMIT ANSWER
============================================================ */

async function submitAnswer() {

    if (state.isLoading) {
        return;
    }

    if (!state.interviewStarted) {
        return;
    }

    const answer =
        elements.answerInput.value.trim();

    if (!answer) {

        showToast(
            "Please enter your answer first.",
            "!"
        );

        elements.answerInput.focus();

        return;
    }

    if (answer.length > MAX_CHARACTERS) {

        showToast(
            `Answer cannot exceed ${MAX_CHARACTERS} characters.`,
            "!"
        );

        return;
    }

    addMessage(
        "user",
        answer
    );

    elements.answerInput.value = "";

    updateCharacterCount();

    setLoading(true);

    try {

        const response =
            await sendInterviewRequest({
                sessionId: state.sessionId,
                message: answer
            });

        if (response.done) {

            state.interviewCompleted = true;

            showCompletionScreen(
                response.feedback
            );

            return;
        }

        state.questionCount++;

        addMessage(
            "ai",
            extractReply(response)
        );

        updateProgress();

    } catch (error) {

        console.error(
            "Answer submission error:",
            error
        );

        showToast(
            getErrorMessage(error),
            "!"
        );

    } finally {

        setLoading(false);
    }
}


/* ============================================================
   API REQUEST
============================================================ */

async function sendInterviewRequest(payload) {

    console.log(
        "Sending interview request to:",
        API_URL
    );

    console.log(
        "Payload:",
        payload
    );

    let response;

    try {

        response = await fetch(
            API_URL,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(payload)
            }
        );

    } catch (error) {

        console.error(
            "Network error:",
            error
        );

        throw new Error(
            "Unable to connect to the FastAPI backend. " +
            "Make sure the backend is running on port 8000."
        );
    }

    let data = null;

    try {

        data = await response.json();

    } catch {

        throw new Error(
            `Server returned HTTP ${response.status}.`
        );
    }

    if (!response.ok) {

        const detail =
            data?.detail ||
            `Request failed with status ${response.status}.`;

        throw new Error(detail);
    }

    return data;
}


/* ============================================================
   MESSAGE EXTRACTION
============================================================ */

function extractReply(response) {

    if (!response) {

        return (
            "The interviewer did not return a response."
        );
    }

    return (
        response.reply ||
        response.message ||
        "The interviewer did not return a response."
    );
}


/* ============================================================
   CONVERSATION UI
============================================================ */

function addMessage(type, text) {

    const message =
        document.createElement("div");

    message.className =
        `message message-${type}`;

    const avatar =
        document.createElement("div");

    avatar.className =
        "message-avatar";

    avatar.textContent =
        type === "ai"
            ? "🤖"
            : getCandidateInitials();

    const content =
        document.createElement("div");

    content.className =
        "message-content";

    const label =
        document.createElement("div");

    label.className =
        "message-label";

    label.textContent =
        type === "ai"
            ? "AI Interviewer"
            : state.candidate.member.name;

    const bubble =
        document.createElement("div");

    bubble.className =
        "message-bubble";

    bubble.textContent = text;

    content.appendChild(label);

    content.appendChild(bubble);

    message.appendChild(avatar);

    message.appendChild(content);

    elements.conversation.appendChild(message);

    requestAnimationFrame(() => {

        message.classList.add(
            "message-visible"
        );

        scrollConversationToBottom();
    });
}


/* ============================================================
   SCROLL
============================================================ */

function scrollConversationToBottom() {

    if (!elements.conversation) {
        return;
    }

    elements.conversation.scrollTo({
        top:
            elements.conversation.scrollHeight,
        behavior: "smooth"
    });
}


/* ============================================================
   THINKING STATE
============================================================ */

function setLoading(isLoading) {

    state.isLoading = isLoading;

    if (elements.sendButton) {

        elements.sendButton.disabled =
            isLoading;
    }

    if (elements.answerInput) {

        elements.answerInput.disabled =
            isLoading;
    }

    if (isLoading) {

        elements.thinkingIndicator
            ?.classList
            .remove("hidden");

        elements.sendButton
            ?.classList
            .add("loading");

        if (elements.sendButton) {

            elements.sendButton.innerHTML =
                `
                    <span class="button-spinner"></span>
                    Thinking...
                `;
        }

        scrollConversationToBottom();

    } else {

        elements.thinkingIndicator
            ?.classList
            .add("hidden");

        elements.sendButton
            ?.classList
            .remove("loading");

        if (elements.sendButton) {

            elements.sendButton.innerHTML =
                `
                    Send
                    <span>➤</span>
                `;
        }

        if (
            state.interviewStarted &&
            !state.interviewCompleted
        ) {

            elements.answerInput?.focus();
        }
    }
}


/* ============================================================
   PROGRESS
============================================================ */

function updateProgress() {

    const current =
        Math.min(
            state.questionCount,
            MAX_QUESTIONS
        );

    const percentage =
        Math.min(
            (current / MAX_QUESTIONS) * 100,
            100
        );

    if (elements.questionLabel) {

        elements.questionLabel.textContent =
            `Question ${current}`;
    }

    if (elements.progressBar) {

        elements.progressBar.style.width =
            `${percentage}%`;
    }

    if (current >= MAX_QUESTIONS) {

        elements.progressLabel.textContent =
            "Final questions";

    } else if (current >= 5) {

        elements.progressLabel.textContent =
            "Making great progress";

    } else if (current >= 2) {

        elements.progressLabel.textContent =
            "Interview in progress";

    } else {

        elements.progressLabel.textContent =
            "Getting started";
    }
}


/* ============================================================
   CHARACTER COUNTER
============================================================ */

function updateCharacterCount() {

    if (!elements.answerInput) {
        return;
    }

    const length =
        elements.answerInput.value.length;

    elements.characterCount.textContent =
        `${length} / ${MAX_CHARACTERS}`;

    elements.characterCount.classList.remove(
        "warning",
        "danger"
    );

    if (length >= MAX_CHARACTERS * 0.9) {

        elements.characterCount.classList.add(
            "danger"
        );

    } else if (
        length >= MAX_CHARACTERS * 0.75
    ) {

        elements.characterCount.classList.add(
            "warning"
        );
    }
}


/* ============================================================
   KEYBOARD HANDLING
============================================================ */

function handleAnswerKeydown(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        submitAnswer();
    }
}


/* ============================================================
   COMPLETION
============================================================ */

function showCompletionScreen(feedback) {

    setLoading(false);

    setConnectionStatus("completed");

    renderFeedback(
        feedback || {}
    );

    showScreen("completion");

    showToast(
        "Interview completed!",
        "🎉"
    );
}


function renderFeedback(feedback) {

    const summary =
        feedback.summary ||
        "Your interview has been completed successfully.";

    elements.feedbackSummary.textContent =
        summary;

    renderList(
        elements.strengthsList,
        feedback.strengths,
        "No strengths were provided."
    );

    renderList(
        elements.gapsList,
        feedback.gaps,
        "No knowledge gaps were identified."
    );

    renderList(
        elements.nextList,
        feedback.next,
        "Keep practicing and continue building."
    );
}


function renderList(
    element,
    items,
    fallback
) {

    element.innerHTML = "";

    if (
        !Array.isArray(items) ||
        items.length === 0
    ) {

        const li =
            document.createElement("li");

        li.textContent = fallback;

        element.appendChild(li);

        return;
    }

    items.forEach(item => {

        const li =
            document.createElement("li");

        li.textContent = item;

        element.appendChild(li);
    });
}


/* ============================================================
   SCREEN MANAGEMENT
============================================================ */

function showScreen(screen) {

    elements.startScreen?.classList.add(
        "hidden"
    );

    elements.interviewScreen?.classList.add(
        "hidden"
    );

    elements.completionScreen?.classList.add(
        "hidden"
    );

    if (screen === "start") {

        elements.startScreen?.classList.remove(
            "hidden"
        );
    }

    if (screen === "interview") {

        elements.interviewScreen?.classList.remove(
            "hidden"
        );
    }

    if (screen === "completion") {

        elements.completionScreen?.classList.remove(
            "hidden"
        );
    }
}


/* ============================================================
   RESTART
============================================================ */

function restartInterview() {

    state.sessionId = null;

    state.questionCount = 0;

    state.interviewStarted = false;

    state.interviewCompleted = false;

    state.isLoading = false;

    clearConversation();

    if (elements.answerInput) {

        elements.answerInput.value = "";
    }

    updateCharacterCount();

    updateProgress();

    showScreen("start");

    setConnectionStatus("ready");

    showToast(
        "Ready for a new interview.",
        "✓"
    );
}


/* ============================================================
   CLEAR CONVERSATION
============================================================ */

function clearConversation() {

    if (elements.conversation) {

        elements.conversation.innerHTML = "";
    }
}


/* ============================================================
   CONNECTION STATUS
============================================================ */

function setConnectionStatus(status) {

    const statusMap = {

        ready: {
            text: "Ready"
        },

        connecting: {
            text: "Connecting..."
        },

        connected: {
            text: "Connected"
        },

        error: {
            text: "Connection error"
        },

        completed: {
            text: "Completed"
        }
    };

    const config =
        statusMap[status] ||
        statusMap.ready;

    if (elements.statusText) {

        elements.statusText.textContent =
            config.text;
    }

    if (elements.connectionStatus) {

        elements.connectionStatus.dataset.status =
            status;
    }
}


/* ============================================================
   CANDIDATE
============================================================ */

function updateCandidatePreview() {

    const member =
        state.candidate.member;

    if (elements.candidateName) {

        elements.candidateName.textContent =
            member.name;
    }

    if (elements.candidateRole) {

        elements.candidateRole.textContent =
            member.jobRole;
    }
}


function getCandidateInitials() {

    const name =
        state.candidate.member.name ||
        "User";

    return name
        .split(" ")
        .map(part => part[0])
        .join("")
        .substring(0, 2)
        .toUpperCase();
}


/* ============================================================
   TOPIC
============================================================ */

function updateTopic(topic) {

    if (!topic) {
        return;
    }

    if (elements.topicBadge) {

        elements.topicBadge.textContent =
            `🧠 ${topic}`;
    }
}


/* ============================================================
   TOAST
============================================================ */

let toastTimeout = null;


function showToast(
    message,
    icon = "✓"
) {

    if (!elements.toast) {
        return;
    }

    elements.toastMessage.textContent =
        message;

    elements.toastIcon.textContent =
        icon;

    elements.toast.classList.add(
        "show"
    );

    clearTimeout(toastTimeout);

    toastTimeout =
        setTimeout(() => {

            elements.toast.classList.remove(
                "show"
            );

        }, 3500);
}


/* ============================================================
   ERROR HANDLING
============================================================ */

function getErrorMessage(error) {

    const message =
        error?.message ||
        "Something went wrong.";

    if (
        message.includes("429") ||
        message.toLowerCase().includes("credit") ||
        message.toLowerCase().includes("quota")
    ) {

        return (
            "The AI service has reached its API quota. " +
            "Please check your AI API key or quota."
        );
    }

    if (
        message.includes("405") ||
        message.toLowerCase().includes(
            "method not allowed"
        )
    ) {

        return (
            "The request reached the wrong server. " +
            "Make sure the frontend is calling " +
            "FastAPI on port 8000."
        );
    }

    if (
        message.includes("Failed to fetch") ||
        message.toLowerCase().includes(
            "unable to connect"
        )
    ) {

        return (
            "Unable to connect to the backend. " +
            "Make sure FastAPI is running on port 8000."
        );
    }

    return message;
}


/* ============================================================
   THEME
============================================================ */

function loadTheme() {

    const savedTheme =
        localStorage.getItem(
            "interview-agent-theme"
        );

    if (savedTheme === "dark") {

        document.documentElement
            .setAttribute(
                "data-theme",
                "dark"
            );

        if (elements.themeToggle) {

            elements.themeToggle.textContent =
                "☀️";
        }

    } else {

        document.documentElement
            .removeAttribute(
                "data-theme"
            );

        if (elements.themeToggle) {

            elements.themeToggle.textContent =
                "🌙";
        }
    }
}


function toggleTheme() {

    const isDark =
        document.documentElement
            .getAttribute("data-theme") ===
        "dark";

    if (isDark) {

        document.documentElement
            .removeAttribute(
                "data-theme"
            );

        localStorage.setItem(
            "interview-agent-theme",
            "light"
        );

        elements.themeToggle.textContent =
            "🌙";

    } else {

        document.documentElement
            .setAttribute(
                "data-theme",
                "dark"
            );

        localStorage.setItem(
            "interview-agent-theme",
            "dark"
        );

        elements.themeToggle.textContent =
            "☀️";
    }
}


/* ============================================================
   GLOBAL NETWORK SAFETY
============================================================ */

window.addEventListener(
    "online",
    () => {

        setConnectionStatus("ready");
    }
);


window.addEventListener(
    "offline",
    () => {

        setConnectionStatus("error");

        showToast(
            "You appear to be offline.",
            "!"
        );
    }
);