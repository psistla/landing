Low-Code Architecture Reference

3 Chatbots using Microsoft Copilot Studio


---

1. Architecture Pattern

Pattern:

> Copilot Studio as Orchestration + Azure AI for Knowledge & Actions



Copilot Studio acts as:

User experience layer

Conversation orchestration

Authentication surface

Action and workflow router


Custom code is used only when Copilot Studio capabilities are insufficient.


---

2. Logical Architecture (Low-Code)

Users
│
├── Public Users (Anonymous Web Chat)
├── Customer Users (Entra ID B2C)
└── Internal Users (Entra ID / M365)
        │
        ▼
Microsoft Copilot Studio
- Topics & flows
- Authentication
- System instructions
- Safety controls
        │
        ├── Knowledge Sources
        │     ├── Public Knowledge
        │     ├── Customer Knowledge
        │     └── Internal Knowledge
        │
        ├── Actions (Low-Code)
        │     ├── Power Automate
        │     └── Azure Functions (when needed)
        │
        ▼
Azure AI (via Copilot Studio)
- GPT models
- Grounding & safety


---

3. Core Services Used

Purpose	Service

Bot UX & Orchestration	Microsoft Copilot Studio
Knowledge Grounding	Copilot Studio Knowledge
Automation	Power Automate
Custom Logic (minimal)	Azure Functions
Identity	Entra ID / Entra ID B2C
Hosting	Microsoft-managed



---

4. Bot-by-Bot Architecture

1️⃣ Public Copilot

Access

Anonymous web chat

Embedded on public website


Knowledge

Public FAQs

Product information

Policy documents


Capabilities

Read-only Q&A

Suggested prompts

No memory persistence


Code Level

100% Copilot Studio (no custom code)



---

2️⃣ Customer Copilot

Access

Entra ID B2C authentication


Knowledge

Customer-facing documentation

Contract templates

Licensing policies


Capabilities

Contract drafting (guided prompts)

License requests

Renewal notices


Automation

Power Automate flows:

Submit license request

Notify support

Create ticket or email



Code Level

Low-code (Copilot Studio + Power Automate)



---

3️⃣ Internal Copilot

Access

Entra ID (employees only)

Optional Microsoft Teams integration


Knowledge

Internal knowledge base

SOPs

License records (read-only)


Capabilities

Answer internal questions

Trigger support tasks

Retrieve license information


Automation

Power Automate

Azure Functions only if advanced logic is required



---

5. Knowledge Architecture

Bot	Knowledge Source

Public	Copilot Studio public files / URLs
Customer	SharePoint / OneDrive / uploaded documents
Internal	Internal Share