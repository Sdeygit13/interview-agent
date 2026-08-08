# 🎯 The Interview Agent

> **AI-powered adaptive technical interview platform for the ABTalks AI Cohort**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![JavaScript](https://img.shields.io/badge/JavaScript-Frontend-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Gemini](https://img.shields.io/badge/Google_Gemini-AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![HTML5](https://img.shields.io/badge/HTML5-Frontend-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-UI-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)

---

## ✨ Overview

**The Interview Agent** is an AI-powered adaptive technical interview platform designed for the **ABTalks AI Cohort**.

Instead of presenting every candidate with the same fixed set of questions, the system uses the candidate's learning journey and previous responses to conduct a **dynamic, multi-turn technical interview**.

The AI interviewer evaluates the candidate's answers and adapts subsequent questions according to their demonstrated technical understanding.

The AI interviewer analyzes:

- 👤 Candidate profile
- 📚 Learning journey
- 🧠 Previous answers
- 🎯 Technical understanding
- 📈 Interview progression
- 🔍 Knowledge gaps

and dynamically determines what to ask next.

> **The goal is simple:**
>
> ### Don't just ask questions.
> ### Understand the candidate.

---

# ⚡ The Core Concept

```mermaid
flowchart LR

A["👤 Candidate"] --> B["🪪 Candidate ID"]

B --> C["🔎 Candidate Lookup"]

C --> D["📋 Candidate Profile"]

D --> E["🚀 Start Interview"]

E --> F["🤖 AI Interviewer"]

F --> G["❓ Technical Question"]

G --> H["💬 Candidate Answer"]

H --> I["🧠 AI Evaluation"]

I --> J{"📊 Understanding"}

J -->|Strong| K["🔥 Increase Depth"]
J -->|Moderate| L["🎯 Explore Concept"]
J -->|Weak| M["📚 Clarify Fundamentals"]

K --> G
L --> G
M --> G

I --> N["🏁 Interview Complete"]

N --> O["📊 Final Evaluation"]

O --> P["💪 Strengths"]
O --> Q["🎯 Knowledge Gaps"]
O --> R["🚀 Recommended Next Steps"]

style A fill:#4F46E5,color:#fff
style F fill:#7C3AED,color:#fff
style I fill:#0891B2,color:#fff
style N fill:#059669,color:#fff
style O fill:#F59E0B,color:#fff
