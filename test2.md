
Enterprise Multi-Tier Chatbot Platform
Architecture Options & Implementation Plan
Microsoft Copilot Studio | Azure AI Foundry | Azure DevOps
12-Week Delivery | 2 Resources
Document Date: 1/13/2026
 
Executive Summary
This document presents three architectural approaches for implementing a multi-tier enterprise chatbot platform serving public, customer, and internal audiences. The recommended approach prioritizes low-code development using Microsoft Copilot Studio as the primary platform, with Azure AI Foundry integration for advanced scenarios requiring custom AI capabilities.

Recommendation
Option 2: Hybrid Copilot Studio + Azure AI Foundry is recommended as the best balance of rapid delivery, extensibility, and enterprise governance for the 12-week timeline with 2 resources.

Requirements Summary
Chatbot	Audience	Key Capabilities
Public	Website visitors, prospects	General Q&A from knowledge base, product information
Customer	Licensed customers (authenticated)	Confidential data access, contract drafting from templates, license management
Internal	Employees	License management automation, knowledge Q&A, support workflow automation
 
Option 1: Copilot Studio Only (Pure Low-Code)
Build all three chatbots entirely within Microsoft Copilot Studio, leveraging native connectors, SharePoint knowledge sources, and Power Automate integration for document generation workflows.

Architecture Overview
•	All chatbots built in Copilot Studio using generative AI orchestration
•	Knowledge grounded in SharePoint document libraries with semantic search
•	Power Automate flows for document generation using Word templates
•	Dataverse for license and customer data management
•	Direct Line channel for website deployment, Teams channel for internal

Pros
•	Fastest time-to-value: 8-10 weeks achievable with single resource
•	Minimal Azure infrastructure management required
•	Built-in Microsoft Purview compliance and governance
•	Copilot Credits model provides predictable consumption-based pricing ($200/25K credits)
•	Native SharePoint integration respects existing document permissions (ACLs)
•	GPT-5 Chat now available in Copilot Studio (GA Dec 2025)

Cons
•	Limited customization for complex RAG scenarios beyond SharePoint semantic search
•	Web channel authentication constraints: No authentication option required for embedded chatbots, limiting customer portal security architecture
•	Document generation requires Power Automate Premium connector license
•	Cannot use custom fine-tuned models or alternative LLMs
•	Less control over prompt engineering and response orchestration

Authentication Limitations (Critical)
Web Channel Security Constraint
For website embedding, Copilot Studio requires 'No authentication' setting on the custom website channel. Authenticated agents (Entra ID) can only be securely deployed to Microsoft-managed channels like Teams, SharePoint, and M365 Copilot. Customer portal authentication must be handled by the hosting application, with the chatbot operating in a secure backend context.

Cost Estimate (Monthly)
Component	Estimate
Copilot Studio Credits (2-3 packs)	$400-600/month
Power Automate Premium (2 users)	$40/month
SharePoint storage	Included in M365
Dataverse (if not existing)	$40/user/month
Total	$500-800/month
 
Option 2: Hybrid Copilot Studio + Azure AI Foundry (RECOMMENDED)
Use Copilot Studio as the conversational front-end with Azure AI Foundry providing advanced backend capabilities for complex scenarios like custom RAG, document processing, and specialized reasoning.

Why This Approach
Copilot Studio serves as the 'front door' providing user-friendly chat interfaces across channels. Azure AI Foundry acts as the 'engine room' for heavy lifting: advanced reasoning, searching large knowledge bases, and custom AI models. This pattern is explicitly recommended by Microsoft for enterprise scenarios (Build 2025).

Architecture Design
Public Chatbot
•	Copilot Studio with public website knowledge sources
•	No authentication (Direct Line channel)
•	Embedded via iframe or Microsoft 365 Agents SDK
•	Knowledge from public SharePoint sites or uploaded documents
Customer Chatbot
•	Copilot Studio frontend deployed to customer portal
•	Azure AI Foundry Agent for confidential document processing
•	Custom RAG with Azure AI Search for contract knowledge
•	Power Automate for Word template-based contract generation
•	Integration via MCP (Model Context Protocol) or REST API
Internal Chatbot
•	Copilot Studio deployed to Teams/SharePoint
•	Authenticate with Microsoft (SSO)
•	SharePoint knowledge with semantic search (requires M365 Copilot license)
•	Power Automate for license management workflows
•	Dataverse integration for structured data

Integration Pattern
Azure AI Foundry agents are exposed via Azure Functions with HTTP triggers. Copilot Studio invokes these as Agent Flow tools or HTTP actions within topics. The pattern is: Copilot Studio receives user input → routes to Azure Function → Azure AI Foundry agent processes with custom knowledge → response returned to Copilot Studio → displayed to user.

Pros
•	Best of both worlds: rapid low-code development with enterprise AI capabilities
•	Access to 11,000+ models in Azure AI Foundry including GPT-4.1, Llama, DeepSeek
•	Custom RAG with Azure AI Search for precise document retrieval
•	Future-proof: can add fine-tuned models, computer vision, speech services
•	MCP (Model Context Protocol) enables seamless agent-to-agent communication
•	Scalable architecture for high-volume customer scenarios
•	Unified governance via Microsoft Purview across both platforms

Cons
•	Higher complexity: requires Azure development skills
•	Additional Azure consumption costs for AI Foundry services
•	Two platforms to manage and monitor
•	12 weeks tight for 2 resources (recommend prioritizing public + internal first)

Cost Estimate (Monthly)
Component	Estimate
Copilot Studio Credits (2-3 packs)	$400-600/month
Azure AI Foundry (platform)	Free (pay per service)
Azure OpenAI (GPT-4o)	$100-300/month (varies by usage)
Azure AI Search (Basic)	$75/month
Azure Functions (Consumption)	$10-50/month
Power Automate Premium	$40/month
Total	$625-1,065/month
 
Option 3: Azure AI Foundry Only (Code-First)
Build all chatbots using Azure AI Foundry Agent Service with custom UIs. This approach provides maximum flexibility but requires significant development effort.

Architecture Overview
•	Azure AI Foundry agents for all three chatbots
•	Custom React/Angular frontends or Bot Framework Web Chat
•	Azure AI Search for all knowledge retrieval
•	Azure Functions for orchestration and business logic
•	Azure App Service for frontend hosting
•	Full CI/CD pipeline in Azure DevOps

Pros
•	Maximum control over AI behavior and prompt engineering
•	Custom UI/UX tailored to each audience
•	No Copilot Studio credit consumption
•	Full flexibility for custom integrations
•	Single platform for all AI development

Cons
•	12 weeks insufficient for 2 resources (estimate 16-20 weeks)
•	Requires experienced Azure/Python developers
•	Custom authentication implementation required
•	Higher infrastructure management overhead
•	Missing Copilot Studio native governance features
•	Document generation requires custom development

Timeline Risk
This approach is NOT recommended for the 12-week timeline with 2 resources. A minimum of 16-20 weeks with 3-4 developers would be required to deliver production-ready solutions across all three chatbots.

Cost Estimate (Monthly)
Component	Estimate
Azure OpenAI (GPT-4o)	$200-500/month
Azure AI Search (Standard)	$250/month
Azure App Service (B2)	$100/month
Azure Functions	$50-100/month
Azure Storage	$20/month
Total	$620-970/month
 
Options Comparison Matrix
Criteria	Option 1	Option 2	Option 3
Development Speed	Fastest (8-10 wks)	Moderate (12 wks)	Slowest (16-20 wks)
Skill Requirement	Low-code makers	Mixed team	Azure developers
Customization	Limited	High	Maximum
Enterprise Governance	Built-in	Built-in + custom	Custom only
Cost Predictability	High (credits)	Moderate	Variable
Future Extensibility	Limited	High	Highest
12-Week Feasibility	Yes (with margin)	Yes (tight)	No
Recommendation	Simple scenarios	RECOMMENDED	Complex/long-term
 
Detailed Project Plan: Option 2 (Recommended)
This 12-week implementation plan assumes 2 full-time resources and prioritizes delivering working chatbots incrementally using an agile approach.

Team Composition
Role	Responsibilities	Allocation
Lead Consultant / Architect	Solution design, Azure AI Foundry development, integration, CI/CD	100%
Power Platform Developer	Copilot Studio development, Power Automate flows, SharePoint configuration	100%

Phase 1: Foundation (Weeks 1-3)
Week 1: Project Setup & Architecture
1.	Environment provisioning: Power Platform environment, Azure AI Foundry project, Azure DevOps project
2.	Architecture design sessions with client stakeholders
3.	Security and governance framework definition
4.	Knowledge source audit: inventory existing documents for each chatbot
5.	Deliverable: Architecture Design Document, Environment Setup Complete
Week 2: Knowledge Infrastructure
6.	Configure SharePoint document libraries for public knowledge
7.	Deploy Azure AI Search instance with indexer configuration
8.	Create Dataverse tables for license management data model
9.	Establish data refresh/sync procedures
10.	Deliverable: Knowledge Infrastructure Ready
Week 3: Authentication & Security
11.	Configure Entra ID app registrations for customer portal integration
12.	Set up Copilot Studio authentication providers
13.	Implement Direct Line channel security with secrets/tokens
14.	Define DLP policies in Power Platform admin center
15.	Deliverable: Security Framework Implemented

Phase 2: Public Chatbot (Weeks 4-5)
Week 4: Public Chatbot Development
16.	Create Copilot Studio agent with generative AI orchestration
17.	Configure public website URLs as knowledge sources
18.	Design conversation topics for common public queries
19.	Implement fallback handling and escalation paths
20.	Initial testing in Copilot Studio test pane
Week 5: Public Chatbot Deployment
21.	Configure custom website channel (No authentication)
22.	Generate embed code for client website
23.	UAT with client stakeholders
24.	Performance tuning and response quality optimization
25.	Deliverable: Public Chatbot LIVE

Phase 3: Internal Chatbot (Weeks 6-7)
Week 6: Internal Chatbot Development
26.	Create Copilot Studio agent with Authenticate with Microsoft
27.	Configure SharePoint knowledge with semantic search
28.	Build Dataverse actions for license data queries
29.	Design automation topics for common support tasks
30.	Enable Tenant graph grounding for enhanced search
Week 7: Internal Chatbot Deployment
31.	Deploy to Teams channel
32.	Configure SharePoint channel deployment (one-click)
33.	Build Power Automate flows for license status updates
34.	UAT with internal support team
35.	Deliverable: Internal Chatbot LIVE

Phase 4: Customer Chatbot (Weeks 8-10)
Week 8: Azure AI Foundry Agent Development
36.	Create Azure AI Foundry project and agent
37.	Configure Azure AI Search with customer document index
38.	Develop custom RAG prompt for confidential queries
39.	Build Azure Function wrapper for Copilot Studio integration
40.	Test agent responses with sample customer scenarios
Week 9: Contract Generation Workflow
41.	Design Word document templates with content controls
42.	Build Power Automate flow: Populate template → Save to OneDrive → Return link
43.	Create Copilot Studio topic with agent flow tool
44.	Implement prompt action for extracting contract parameters
45.	End-to-end testing of document generation
Week 10: Customer Chatbot Integration
46.	Integrate Copilot Studio with Azure AI Foundry agent via HTTP action
47.	Configure customer authentication flow
48.	Build license request/renewal topics
49.	Deploy to customer portal integration
50.	Deliverable: Customer Chatbot LIVE (Beta)

Phase 5: Hardening & Handover (Weeks 11-12)
Week 11: Testing & Optimization
51.	Comprehensive end-to-end testing across all chatbots
52.	Performance optimization and response time tuning
53.	Security penetration testing
54.	Analytics dashboard configuration
55.	Bug fixes and refinements based on UAT feedback
Week 12: Documentation & Handover
56.	Administrator documentation and runbooks
57.	Knowledge transfer sessions with client team
58.	Operational support playbook
59.	Final demo and sign-off
60.	Deliverable: All Documentation, Training Complete, Project Closure
 
Project Schedule Overview
Phase	Weeks	Primary Deliverables
1. Foundation	1-3	Architecture, environments, security framework
2. Public Chatbot	4-5	Public website chatbot LIVE
3. Internal Chatbot	6-7	Teams/SharePoint chatbot LIVE
4. Customer Chatbot	8-10	Customer portal chatbot LIVE (Beta)
5. Hardening	11-12	Testing, documentation, handover
 
Critical Pitfalls & Mitigations

PITFALL 1: Web Authentication Limitations
Copilot Studio web channel requires 'No authentication' for embedding. Customer authentication must be handled by the hosting application. Plan architecture around this constraint from day one. For customer chatbot, use backend API integration rather than direct embed.

PITFALL 2: SharePoint File Size Limits
Without M365 Copilot license in tenant, SharePoint knowledge sources limited to 7MB files. With semantic search enabled (requires M365 Copilot), limit increases to 200MB. Verify client licensing before architecture design.

PITFALL 3: Copilot Credits Consumption
Credits don't roll over month-to-month. Monitor usage closely in Power Platform admin center. Configure environment-level quotas to prevent overage. Generative answers consume 4 credits each vs. 1 for classic responses.

PITFALL 4: Document Generation Complexity
Power Automate 'Populate Word Template' action requires Premium license. Repeating sections (line items) require JSON parsing. Test template thoroughly before committing to design. Consider dedicated document generation sprint.

PITFALL 5: Azure AI Search Index Latency
Initial indexing and updates are not real-time. Configure indexer schedules appropriately. For customer-facing confidential data, ensure refresh frequency meets SLA requirements.

PITFALL 6: Cross-Geo Data Residency
Azure AI Foundry services may process data outside primary region. Configure cross-geo consent settings in Power Platform admin center. Document data flows for compliance review.

Risk Register
Risk	Impact	Probability	Mitigation
Knowledge source quality issues	High	Medium	Early content audit, define minimum quality standards
Integration complexity underestimated	High	Medium	Allocate buffer in Week 10, prioritize MVP features
Client stakeholder availability	Medium	Medium	Schedule all UAT sessions in Week 1
Azure service quota limits	Medium	Low	Request quota increases before Week 8
Power Platform DLP policy conflicts	Medium	Low	Engage IT admin in Week 1 security discussions
 
CI/CD Implementation (Optional Enhancement)
While CI/CD is optional for this project, implementing basic ALM practices will significantly improve maintainability and enable future enhancements.

Recommended Minimal CI/CD
•	Power Platform: Use Solutions for packaging Copilot Studio agents
•	Azure Pipelines: Export solution from Dev → Import to Prod
•	Azure AI Foundry: Infrastructure-as-Code with Bicep templates
•	Source Control: Azure Repos for all configuration and code

Future Enhancement Roadmap
•	Multi-agent orchestration using Copilot Studio Connected Agents
•	WhatsApp channel deployment (available July 2025)
•	Custom fine-tuned models in Azure AI Foundry
•	Autonomous agents for proactive license renewal notifications
•	Advanced analytics with Power BI embedded dashboards

Conclusion
Option 2 (Hybrid Copilot Studio + Azure AI Foundry) provides the optimal balance of rapid delivery, enterprise governance, and future extensibility for this engagement. The low-code-first approach with Copilot Studio enables the 2-resource team to deliver working solutions within the 12-week timeline, while Azure AI Foundry integration ensures the platform can scale to meet evolving requirements.

Key success factors:
•	Early engagement with client IT/security teams on authentication architecture
•	Rigorous knowledge source audit in Week 1
•	Incremental delivery with working chatbots at Week 5, 7, and 10
•	Clear scope boundaries to maintain 12-week delivery

— End of Document —
