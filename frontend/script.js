/* ============================================================
   THE INTERVIEW AGENT
   Frontend Application Logic
   Candidate Lookup + Adaptive Interview
============================================================ */

"use strict";


/* ============================================================
   CONFIGURATION
============================================================ */

const API_BASE_URL = "http://127.0.0.1:8000";

const CANDIDATE_API_URL =
    `${API_BASE_URL}/api/candidates`;

const INTERVIEW_API_URL =
    `${API_BASE_URL}/api/interview`;

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

    candidateLoading: false,

    candidateLoaded: false,

    candidate: null

};


/* ============================================================
   DOM ELEMENTS
============================================================ */

const elements = {

    /* Screens */

    startScreen:
        document.getElementById("startScreen"),

    interviewScreen:
        document.getElementById("interviewScreen"),

    completionScreen:
        document.getElementById("completionScreen"),


    /* Candidate Lookup */

    candidateIdInput:
        document.getElementById("candidateIdInput"),

    findCandidateBtn:
        document.getElementById("findCandidateBtn"),

    candidateLookupMessage:
        document.getElementById(
            "candidateLookupMessage"
        ),

    candidatePreview:
        document.getElementById(
            "candidatePreview"
        ),

    candidateInitials:
        document.getElementById(
            "candidateInitials"
        ),

    candidateName:
        document.getElementById(
            "candidateName"
        ),

    candidateRole:
        document.getElementById(
            "candidateRole"
        ),

    candidateDetails:
        document.getElementById(
            "candidateDetails"
        ),

    candidateCheck:
        document.getElementById(
            "candidateCheck"
        ),


    /* Interview */

    startInterviewBtn:
        document.getElementById(
            "startInterviewBtn"
        ),

    restartBtn:
        document.getElementById(
            "restartBtn"
        ),

    newInterviewBtn:
        document.getElementById(
            "newInterviewBtn"
        ),

    answerInput:
        document.getElementById(
            "answerInput"
        ),

    sendButton:
        document.getElementById(
            "sendButton"
        ),

    conversation:
        document.getElementById(
            "conversation"
        ),

    thinkingIndicator:
        document.getElementById(
            "thinkingIndicator"
        ),


    /* Progress */

    questionLabel:
        document.getElementById(
            "questionLabel"
        ),

    progressLabel:
        document.getElementById(
            "progressLabel"
        ),

    progressBar:
        document.getElementById(
            "progressBar"
        ),

    topicBadge:
        document.getElementById(
            "topicBadge"
        ),


    /* Composer */

    characterCount:
        document.getElementById(
            "characterCount"
        ),


    /* Header */

    connectionStatus:
        document.getElementById(
            "connectionStatus"
        ),

    statusText:
        document.getElementById(
            "statusText"
        ),

    themeToggle:
        document.getElementById(
            "themeToggle"
        ),


    /* Feedback */

    feedbackSummary:
        document.getElementById(
            "feedbackSummary"
        ),

    strengthsList:
        document.getElementById(
            "strengthsList"
        ),

    gapsList:
        document.getElementById(
            "gapsList"
        ),

    nextList:
        document.getElementById(
            "nextList"
        ),


    /* Toast */

    toast:
        document.getElementById(
            "toast"
        ),

    toastIcon:
        document.getElementById(
            "toastIcon"
        ),

    toastMessage:
        document.getElementById(
            "toastMessage"
        )

};


/* ============================================================
   INITIALIZATION
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeApplication();

    }
);


function initializeApplication() {

    loadTheme();

    setupEventListeners();

    updateCharacterCount();

    updateProgress();

    resetCandidateUI();

    setConnectionStatus("ready");

}


/* ============================================================
   EVENT LISTENERS
============================================================ */

function setupEventListeners() {

    elements.findCandidateBtn?.addEventListener(
        "click",
        findCandidate
    );


    elements.candidateIdInput?.addEventListener(
        "keydown",
        handleCandidateIdKeydown
    );


    elements.candidateIdInput?.addEventListener(
        "input",
        handleCandidateIdInput
    );


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
   CANDIDATE ID INPUT
============================================================ */

function handleCandidateIdInput() {

    const candidateId =
        elements.candidateIdInput.value.trim();


    /*
       If the user changes the ID after a
       successful lookup, invalidate the
       previously loaded candidate.
    */

    if (
        state.candidateLoaded &&
        candidateId !== state.candidate?.member?.id
    ) {

        resetCandidateUI();

    }


    elements.candidateIdInput.value =
        elements.candidateIdInput.value
            .toUpperCase();

}


function handleCandidateIdKeydown(event) {

    if (event.key === "Enter") {

        event.preventDefault();

        findCandidate();

    }

}


/* ============================================================
   FIND CANDIDATE
============================================================ */

async function findCandidate() {

    if (state.candidateLoading) {

        return;

    }


    const candidateId =
        elements.candidateIdInput.value
            .trim()
            .toUpperCase();


    /* -----------------------------------------------
       Validate input
    ------------------------------------------------ */

    if (!candidateId) {

        showCandidateLookupMessage(
            "Please enter a Candidate ID.",
            "error"
        );

        elements.candidateIdInput.focus();

        return;

    }


    /* -----------------------------------------------
       Basic Candidate ID validation
    ------------------------------------------------ */

    if (!/^CAND-\d+$/i.test(candidateId)) {

        showCandidateLookupMessage(
            "Invalid Candidate ID. Use a format like CAND-007.",
            "error"
        );

        elements.candidateIdInput.focus();

        return;

    }


    state.candidateLoading = true;

    setCandidateLookupLoading(true);

    setConnectionStatus("connecting");


    try {

        const response =
            await fetchCandidate(candidateId);


        const candidate =
            normalizeCandidate(response);


        if (!candidate) {

            throw new Error(
                "The server returned invalid candidate data."
            );

        }


        /* -------------------------------------------
           Store candidate
        -------------------------------------------- */

        state.candidate =
            candidate;

        state.candidateLoaded =
            true;


        /* -------------------------------------------
           Display candidate
        -------------------------------------------- */

        displayCandidate(candidate);


        showCandidateLookupMessage(
            "Candidate found successfully. You can start the interview.",
            "success"
        );


        setConnectionStatus("connected");

        showToast(
            "Candidate found successfully!",
            "✓"
        );


    } catch (error) {

        console.error(
            "Candidate lookup error:",
            error
        );


        state.candidate =
            null;

        state.candidateLoaded =
            false;


        resetCandidatePreview();


        setConnectionStatus("error");


        showCandidateLookupMessage(
            getCandidateErrorMessage(error),
            "error"
        );


        showToast(
            getCandidateErrorMessage(error),
            "!"
        );


    } finally {

        state.candidateLoading =
            false;

        setCandidateLookupLoading(false);

    }

}


/* ============================================================
   FETCH CANDIDATE
============================================================ */

async function fetchCandidate(candidateId) {

    const response =
        await fetch(
            `${CANDIDATE_API_URL}/${encodeURIComponent(candidateId)}`,
            {
                method: "GET",

                headers: {
                    "Accept": "application/json"
                }
            }
        );


    let data = null;


    try {

        data =
            await response.json();

    } catch {

        if (!response.ok) {

            throw new Error(
                `Server returned HTTP ${response.status}.`
            );

        }

    }


    if (!response.ok) {

        const detail =
            data?.detail ||
            `Candidate lookup failed with HTTP ${response.status}.`;

        throw new Error(detail);

    }


    return data;

}


/* ============================================================
   NORMALIZE CANDIDATE
============================================================ */

function normalizeCandidate(data) {

    /*
       Expected backend structure:

       {
           member: {
               id,
               name,
               jobRole,
               yearsExperience,
               education,
               status
           },
           missions: [...],
           signals: {...}
       }
    */


    if (
        data &&
        typeof data === "object" &&
        data.member
    ) {

        return data;

    }


    /*
       Also support a backend response where
       candidate information is wrapped.
    */

    if (
        data?.candidate &&
        data.candidate.member
    ) {

        return data.candidate;

    }


    return null;

}


/* ============================================================
   DISPLAY CANDIDATE
============================================================ */

function displayCandidate(candidate) {

    const member =
        candidate.member;


    const name =
        member.name ||
        "Unknown Candidate";


    const role =
        member.jobRole ||
        "Role not specified";


    const experience =
        formatExperience(
            member.yearsExperience
        );


    const education =
        member.education ||
        "Education not specified";


    const initials =
        getInitials(name);


    elements.candidateInitials.textContent =
        initials;


    elements.candidateName.textContent =
        name;


    elements.candidateRole.textContent =
        role;


    elements.candidateDetails.textContent =
        `${experience} • ${education}`;


    elements.candidateCheck.textContent =
        "✓";


    elements.candidatePreview.classList.remove(
        "hidden"
    );


    elements.startInterviewBtn.disabled =
        false;


    elements.startInterviewBtn.classList.add(
        "ready"
    );

}


/* ============================================================
   FORMAT EXPERIENCE
============================================================ */

function formatExperience(years) {

    if (
        years === null ||
        years === undefined ||
        years === ""
    ) {

        return "Experience not specified";

    }


    const numericYears =
        Number(years);


    if (
        Number.isNaN(numericYears)
    ) {

        return String(years);

    }


    if (numericYears === 0) {

        return "0 years experience";

    }


    if (numericYears === 1) {

        return "1 year experience";

    }


    return `${numericYears} years experience`;

}


/* ============================================================
   GET INITIALS
============================================================ */

function getInitials(name) {

    if (!name) {

        return "--";

    }


    return name
        .trim()
        .split(/\s+/)
        .map(
            part => part.charAt(0)
        )
        .join("")
        .substring(0, 2)
        .toUpperCase();

}


/* ============================================================
   CANDIDATE UI RESET
============================================================ */

function resetCandidateUI() {

    state.candidate =
        null;

    state.candidateLoaded =
        false;


    resetCandidatePreview();


    if (elements.startInterviewBtn) {

        elements.startInterviewBtn.disabled =
            true;

        elements.startInterviewBtn.classList.remove(
            "ready"
        );

    }


    showCandidateLookupMessage(
        "Enter your Candidate ID to continue.",
        "default"
    );

}


function resetCandidatePreview() {

    elements.candidatePreview?.classList.add(
        "hidden"
    );


    if (elements.candidateInitials) {

        elements.candidateInitials.textContent =
            "--";

    }


    if (elements.candidateName) {

        elements.candidateName.textContent =
            "Candidate Name";

    }


    if (elements.candidateRole) {

        elements.candidateRole.textContent =
            "Job Role";

    }


    if (elements.candidateDetails) {

        elements.candidateDetails.textContent =
            "Candidate details";

    }


    if (elements.candidateCheck) {

        elements.candidateCheck.textContent =
            "✓";

    }

}


/* ============================================================
   CANDIDATE LOOKUP MESSAGE
============================================================ */

function showCandidateLookupMessage(
    message,
    type = "default"
) {

    if (
        !elements.candidateLookupMessage
    ) {

        return;

    }


    elements.candidateLookupMessage.textContent =
        message;


    elements.candidateLookupMessage.dataset.state =
        type;

}


/* ============================================================
   CANDIDATE LOOKUP LOADING
============================================================ */

function setCandidateLookupLoading(
    isLoading
) {

    if (
        !elements.findCandidateBtn
    ) {

        return;

    }


    elements.findCandidateBtn.disabled =
        isLoading;


    if (isLoading) {

        elements.findCandidateBtn.innerHTML =
            `
                <span class="button-spinner"></span>
                Finding...
            `;

    } else {

        elements.findCandidateBtn.innerHTML =
            `
                <span>🔍</span>
                Find Candidate
            `;

    }

}


/* ============================================================
   START INTERVIEW
============================================================ */

async function startInterview() {

    if (state.isLoading) {

        return;

    }


    if (!state.candidateLoaded) {

        showToast(
            "Please find a valid candidate first.",
            "!"
        );

        return;

    }


    const candidate =
        state.candidate;


    const candidateId =
        candidate?.member?.id;


    if (!candidateId) {

        showToast(
            "Candidate information is incomplete.",
            "!"
        );

        return;

    }


    /*
       Generate a unique session ID for this
       interview attempt.
    */

    state.sessionId =
        `session-${candidateId}-${Date.now()}`;


    state.questionCount =
        0;


    state.interviewStarted =
        false;


    state.interviewCompleted =
        false;


    clearConversation();


    showScreen("interview");


    setLoading(true);

    setConnectionStatus("connecting");


    try {

        const response =
            await sendInterviewRequest({

                sessionId:
                    state.sessionId,

                candidate:
                    candidate

            });


        state.interviewStarted =
            true;


        state.questionCount =
            1;


        addMessage(
            "ai",
            extractReply(response)
        );


        updateProgress();


        setConnectionStatus(
            "connected"
        );


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


        setConnectionStatus(
            "error"
        );


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


    if (
        answer.length >
        MAX_CHARACTERS
    ) {

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


    elements.answerInput.value =
        "";


    updateCharacterCount();


    setLoading(true);


    try {

        const response =
            await sendInterviewRequest({

                sessionId:
                    state.sessionId,

                message:
                    answer

            });


        if (response.done) {

            state.interviewCompleted =
                true;


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
   INTERVIEW API REQUEST
============================================================ */

async function sendInterviewRequest(
    payload
) {

    const response =
        await fetch(
            INTERVIEW_API_URL,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",

                    "Accept":
                        "application/json"
                },

                body:
                    JSON.stringify(payload)
            }
        );


    let data;


    try {

        data =
            await response.json();

    } catch {

        throw new Error(
            `Server returned HTTP ${response.status}.`
        );

    }


    if (!response.ok) {

        const detail =
            data?.detail ||
            `Request failed with status ${response.status}.`;


        throw new Error(
            detail
        );

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

function addMessage(
    type,
    text
) {

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
            : getInitials(
                state.candidate?.member?.name
            );


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
            : (
                state.candidate?.member?.name ||
                "Candidate"
            );


    const bubble =
        document.createElement("div");


    bubble.className =
        "message-bubble";


    bubble.textContent =
        text;


    content.appendChild(
        label
    );


    content.appendChild(
        bubble
    );


    message.appendChild(
        avatar
    );


    message.appendChild(
        content
    );


    elements.conversation.appendChild(
        message
    );


    requestAnimationFrame(
        () => {

            message.classList.add(
                "message-visible"
            );


            scrollConversationToBottom();

        }
    );

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

        behavior:
            "smooth"

    });

}


/* ============================================================
   THINKING / LOADING STATE
============================================================ */

function setLoading(
    isLoading
) {

    state.isLoading =
        isLoading;


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
            `Question ${current || 1}`;

    }


    if (elements.progressBar) {

        elements.progressBar.style.width =
            `${percentage}%`;

    }


    if (!elements.progressLabel) {

        return;

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


    if (
        length >=
        MAX_CHARACTERS * 0.9
    ) {

        elements.characterCount.classList.add(
            "danger"
        );

    } else if (
        length >=
        MAX_CHARACTERS * 0.75
    ) {

        elements.characterCount.classList.add(
            "warning"
        );

    }

}


/* ============================================================
   KEYBOARD HANDLING
============================================================ */

function handleAnswerKeydown(
    event
) {

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

function showCompletionScreen(
    feedback
) {

    setLoading(false);


    setConnectionStatus(
        "completed"
    );


    renderFeedback(
        feedback || {}
    );


    showScreen(
        "completion"
    );


    showToast(
        "Interview completed!",
        "🎉"
    );

}


/* ============================================================
   FEEDBACK
============================================================ */

function renderFeedback(
    feedback
) {

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

    if (!element) {

        return;

    }


    element.innerHTML =
        "";


    if (
        !Array.isArray(items) ||
        items.length === 0
    ) {

        const li =
            document.createElement("li");


        li.textContent =
            fallback;


        element.appendChild(
            li
        );


        return;

    }


    items.forEach(
        item => {

            const li =
                document.createElement("li");


            li.textContent =
                item;


            element.appendChild(
                li
            );

        }
    );

}


/* ============================================================
   SCREEN MANAGEMENT
============================================================ */

function showScreen(
    screen
) {

    elements.startScreen
        ?.classList
        .add("hidden");


    elements.interviewScreen
        ?.classList
        .add("hidden");


    elements.completionScreen
        ?.classList
        .add("hidden");


    if (screen === "start") {

        elements.startScreen
            ?.classList
            .remove("hidden");

    }


    if (screen === "interview") {

        elements.interviewScreen
            ?.classList
            .remove("hidden");

    }


    if (screen === "completion") {

        elements.completionScreen
            ?.classList
            .remove("hidden");

    }

}


/* ============================================================
   RESTART
============================================================ */

function restartInterview() {

    state.sessionId =
        null;


    state.questionCount =
        0;


    state.interviewStarted =
        false;


    state.interviewCompleted =
        false;


    state.isLoading =
        false;


    clearConversation();


    if (elements.answerInput) {

        elements.answerInput.value =
            "";

    }


    updateCharacterCount();

    updateProgress();


    /*
       Keep the currently selected candidate.

       This means Restart takes the user back
       to the candidate screen without forcing
       them to type the ID again.
    */

    if (state.candidateLoaded) {

        showScreen("start");

        setConnectionStatus(
            "connected"
        );

        showCandidateLookupMessage(
            "Candidate is ready. You can start a new interview.",
            "success"
        );

    } else {

        showScreen("start");

        setConnectionStatus(
            "ready"
        );

    }


    showToast(
        "Ready for a new interview.",
        "✓"
    );

}


/* ============================================================
   CLEAR CONVERSATION
============================================================ */

function clearConversation() {

    if (
        elements.conversation
    ) {

        elements.conversation.innerHTML =
            "";

    }

}


/* ============================================================
   CONNECTION STATUS
============================================================ */

function setConnectionStatus(
    status
) {

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
   TOPIC
============================================================ */

function updateTopic(
    topic
) {

    if (
        !topic ||
        !elements.topicBadge
    ) {

        return;

    }


    elements.topicBadge.textContent =
        `🧠 ${topic}`;

}


/* ============================================================
   TOAST
============================================================ */

let toastTimeout =
    null;


function showToast(
    message,
    icon = "✓"
) {

    if (
        !elements.toast
    ) {

        return;

    }


    elements.toastMessage.textContent =
        message;


    elements.toastIcon.textContent =
        icon;


    elements.toast.classList.add(
        "show"
    );


    clearTimeout(
        toastTimeout
    );


    toastTimeout =
        setTimeout(
            () => {

                elements.toast.classList.remove(
                    "show"
                );

            },
            3500
        );

}


/* ============================================================
   ERROR HANDLING
============================================================ */

function getCandidateErrorMessage(
    error
) {

    const message =
        error?.message ||
        "Unable to find candidate.";


    if (
        message.includes("404") ||
        message.toLowerCase().includes("not found")
    ) {

        return (
            "Candidate not found. Please check the Candidate ID."
        );

    }


    if (
        message.includes("Failed to fetch")
    ) {

        return (
            "Unable to connect to the backend. " +
            "Make sure FastAPI is running on port 8000."
        );

    }


    return message;

}


function getErrorMessage(
    error
) {

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
        message.includes("Failed to fetch")
    ) {

        return (
            "Unable to connect to the backend. " +
            "Make sure the FastAPI server is running."
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


    if (
        savedTheme === "dark"
    ) {

        document.documentElement
            .setAttribute(
                "data-theme",
                "dark"
            );


        elements.themeToggle.textContent =
            "☀️";


    } else {

        document.documentElement
            .removeAttribute(
                "data-theme"
            );


        elements.themeToggle.textContent =
            "🌙";

    }

}


function toggleTheme() {

    const isDark =
        document.documentElement
            .getAttribute(
                "data-theme"
            ) === "dark";


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
   ONLINE / OFFLINE
============================================================ */

window.addEventListener(
    "online",
    () => {

        setConnectionStatus(
            "ready"
        );

    }
);


window.addEventListener(
    "offline",
    () => {

        setConnectionStatus(
            "error"
        );


        showToast(
            "You appear to be offline.",
            "!"
        );

    }
);