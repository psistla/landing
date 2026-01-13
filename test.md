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
Internal	Internal SharePoint / repositories


Rule:
Public, customer, and internal knowledge must never be mixed in the same copilot.


---

6. Identity & Trust Boundaries

Bot	Authentication	Boundary Enforcement

Public	None	Topic and knowledge scope
Customer	Entra ID B2C	Auth + knowledge separation
Internal	Entra ID	Tenant boundary


Identity enforcement is handled natively by Copilot Studio.


---

7. CI/CD (Minimal, Low-Code)

Included

Manual export/import of copilots

Environment separation (Dev → Prod)

Power Platform solutions


Excluded

YAML pipelines

Automated testing

Prompt regression testing


This is acceptable for a low-code MVP.


---

8. 12-Week Execution Plan (2 Resources)

Weeks 1–2

Create three copilots

Define system instructions

Upload and validate knowledge sources


Weeks 3–4

Public copilot live

Website embed

UX tuning


Weeks 5–6

Customer copilot

B2C authentication

Contract drafting prompts


Weeks 7–8

Power Automate workflows

License request automation


Weeks 9–10

Internal copilot

Internal knowledge grounding


Weeks 11–12

Testing

Go-live

Documentation and handoff



---

9. What This Architecture Intentionally Avoids

Advanced RAG tuning

Search index management

Prompt versioning

Complex DevOps

Autonomous agents


This keeps the solution maintainable by a small team.


---

10. Required Safeguards

1. Separate copilots per audience


2. No cross-knowledge sharing


3. Locked system instructions


4. Clear legal disclaimers


5. Confirmation for write actions




---

11. When This Architecture Is Appropriate

Small delivery team

Fast time-to-market

Business-led iteration

Minimal engineering overhead



---

12. When This Architecture Is Not Appropriate

Heavy regulatory requirements

High transaction volumes

Complex system integrations

Strict CI/CD enforcement



---

RFP-Ready Summary Statement

> “The solution uses Microsoft Copilot Studio as a low-code orchestration layer with native identity, knowledge grounding, and Power Automate integrations to deliver public, customer, and internal copilots.”