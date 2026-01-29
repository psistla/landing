Now I have comprehensive information to create a detailed Customer Chatbot architecture. Let me structure this response.

---

## Customer Chatbot: Detailed Architecture with Azure AI Foundry Integration

### High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              CUSTOMER CHATBOT ARCHITECTURE                               │
│                    (Copilot Studio + Azure AI Foundry Integration)                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND LAYER                                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                           │
│    │   Customer   │     │   Customer   │     │    Direct    │                           │
│    │   Website    │     │    Portal    │     │     Line     │                           │
│    │   (iframe)   │     │   (Custom)   │     │     API      │                           │
│    └──────┬───────┘     └──────┬───────┘     └──────┬───────┘                           │
│           │                    │                    │                                    │
│           └────────────────────┼────────────────────┘                                    │
│                                ▼                                                         │
│                    ┌───────────────────────┐                                             │
│                    │    Microsoft Entra    │                                             │
│                    │    ID Authentication  │                                             │
│                    │    (OAuth 2.0/SSO)    │                                             │
│                    └───────────┬───────────┘                                             │
└────────────────────────────────┼────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         COPILOT STUDIO ORCHESTRATION LAYER                               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│    ┌─────────────────────────────────────────────────────────────────────────────┐      │
│    │                         CUSTOMER SUPPORT AGENT                               │      │
│    │                                                                              │      │
│    │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │      │
│    │   │ Generative  │  │   Topics    │  │   Actions   │  │   Tools     │        │      │
│    │   │ Orchestrator│  │   Engine    │  │   Engine    │  │   Registry  │        │      │
│    │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │      │
│    │          │                │                │                │               │      │
│    │          └────────────────┴────────────────┴────────────────┘               │      │
│    │                                    │                                         │      │
│    └────────────────────────────────────┼─────────────────────────────────────────┘      │
│                                         │                                                │
│    ┌────────────────────────────────────┼────────────────────────────────────────┐      │
│    │                        KNOWLEDGE SOURCES                                     │      │
│    │                                                                              │      │
│    │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │      │
│    │   │ SharePoint  │  │   Azure AI  │  │  Dataverse  │  │   Files     │        │      │
│    │   │  (Customer  │  │   Search    │  │  (License   │  │ (Uploaded   │        │      │
│    │   │   Docs)     │  │  (Vector)   │  │   Data)     │  │   PDFs)     │        │      │
│    │   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │      │
│    └─────────────────────────────────────────────────────────────────────────────┘      │
│                                                                                          │
└────────────────────────────────┬────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
┌───────────────────────────────┐  ┌───────────────────────────────────────────────────────┐
│   POWER PLATFORM LAYER        │  │              AZURE AI FOUNDRY LAYER                   │
├───────────────────────────────┤  ├───────────────────────────────────────────────────────┤
│                               │  │                                                       │
│  ┌─────────────────────────┐  │  │  ┌─────────────────────────────────────────────────┐  │
│  │     Power Automate      │  │  │  │              FOUNDRY PROJECT                    │  │
│  │      Agent Flows        │  │  │  │                                                 │  │
│  │                         │  │  │  │  ┌─────────────┐  ┌─────────────────────────┐   │  │
│  │  ┌───────────────────┐  │  │  │  │  │   Azure     │  │   Foundry Agent Service │   │  │
│  │  │ License Lookup    │  │  │  │  │  │   OpenAI    │  │   (Contract Drafting    │   │  │
│  │  │ Flow              │  │  │  │  │  │  (GPT-4.1)  │  │    Agent)               │   │  │
│  │  └───────────────────┘  │  │  │  │  └──────┬──────┘  └───────────┬─────────────┘   │  │
│  │  ┌───────────────────┐  │  │  │  │         │                    │                 │  │
│  │  │ Renewal Request   │  │  │  │  │         └────────────────────┘                 │  │
│  │  │ Flow              │  │  │  │  │                    │                           │  │
│  │  └───────────────────┘  │  │  │  │  ┌─────────────────┼─────────────────────────┐ │  │
│  │  ┌───────────────────┐  │  │  │  │  │           TOOLS & KNOWLEDGE              │ │  │
│  │  │ Support Ticket    │  │  │  │  │  │                                          │ │  │
│  │  │ Flow              │  │  │  │  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │  │
│  │  └───────────────────┘  │  │  │  │  │  │ Azure AI │ │ Function │ │  Logic   │  │ │  │
│  │                         │  │  │  │  │  │  Search  │ │ Calling  │ │  Apps    │  │ │  │
│  │                         │  │  │  │  │  └──────────┘ └──────────┘ └──────────┘  │ │  │
│  └─────────────────────────┘  │  │  │  └──────────────────────────────────────────┘ │  │
│                               │  │  │                                                 │  │
│  ┌─────────────────────────┐  │  │  │  ┌─────────────────────────────────────────┐   │  │
│  │      Dataverse          │  │  │  │  │        RESPONSIBLE AI                   │   │  │
│  │   (License Records)     │  │  │  │  │  ┌──────────┐  ┌──────────────────────┐ │   │  │
│  └─────────────────────────┘  │  │  │  │  │ Content  │  │ Groundedness Check   │ │   │  │
│                               │  │  │  │  │ Filter   │  │ (Citation Required)  │ │   │  │
│                               │  │  │  │  └──────────┘  └──────────────────────┘ │   │  │
│                               │  │  │  └─────────────────────────────────────────┘   │  │
│                               │  │  └─────────────────────────────────────────────────┘  │
└───────────────────────────────┘  └───────────────────────────────────────────────────────┘
                    │                         │
                    └────────────┬────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              DATA STORAGE LAYER                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│   │   Azure     │  │   Azure     │  │   Azure     │  │  SharePoint │  │   Azure     │   │
│   │  Cosmos DB  │  │   Storage   │  │  AI Search  │  │   Online    │  │  Key Vault  │   │
│   │ (Chat State)│  │   (Docs)    │  │   (Index)   │  │  (Customer) │  │  (Secrets)  │   │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Azure AI Foundry Components in Detail

#### 1. **Azure AI Foundry Project**

The Foundry Project serves as the central container for all AI resources.

**Configuration:**
```json
{
  "projectName": "contoso-customer-chatbot",
  "resourceGroup": "rg-contoso-ai",
  "location": "eastus",
  "hub": {
    "name": "hub-contoso-ai",
    "sku": "Standard"
  },
  "connections": {
    "azureOpenAI": "aoai-contoso-prod",
    "azureAISearch": "search-contoso-customer",
    "azureStorage": "stcontosocustomerdocs"
  }
}
```

**Components Created:**
- **Foundry Hub:** Container for shared resources (Cognitive Services, Key Vault)
- **Foundry Project:** Workspace for the customer chatbot agents
- **Managed Identity:** System-assigned identity for secure resource access

---

#### 2. **Azure OpenAI Service (Models)**

You can access a diverse portfolio of AI models, including cutting-edge open-source solutions, industry-specific models, and task-based AI capabilities—all within the trusted, scalable, and enterprise-ready platform of Copilot Studio. [Microsoft Learn](https://learn.microsoft.com/en-us/ai-builder/byom-for-your-prompts)

**Model Deployments:**

| Model | Deployment Name | Purpose | TPM |
|-------|-----------------|---------|-----|
| GPT-4.1 | gpt-41-customer | Primary reasoning, contract drafting | 60K |
| GPT-4o-mini | gpt-4o-mini-fallback | Cost-effective fallback | 30K |
| text-embedding-3-large | embedding-customer | Document vectorization | 30K |

**Contract Drafting Model Configuration:**
```python
# Azure AI Foundry Model Deployment
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project_client = AIProjectClient.from_connection_string(
    conn_str=os.environ["AIPROJECT_CONNECTION_STRING"],
    credential=DefaultAzureCredential()
)

# Deploy GPT-4.1 for contract drafting
model_config = {
    "model": "gpt-4.1",
    "deployment_name": "gpt-41-contract-drafter",
    "sku": {
        "name": "Standard",
        "capacity": 60  # 60K TPM
    },
    "rai_policy": "Microsoft.Default"  # Content filtering
}
```

---

#### 3. **Foundry Agent Service (Contract Drafting Agent)**

Equip your agent with tools. These tools let the agent access enterprise knowledge (such as Bing, SharePoint, and Azure AI Search) and take real-world actions (via Azure Logic Apps, Azure Functions, OpenAPI, and more). [Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview?view=foundry-classic)

**Agent Configuration:**
```python
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    AzureAISearchTool,
    FunctionTool,
    CodeInterpreterTool
)

# Create the Contract Drafting Agent
contract_agent = project_client.agents.create_agent(
    model="gpt-41-contract-drafter",
    name="ContractDraftingAgent",
    instructions="""You are a contract drafting assistant for licensed customers.

    RULES:
    1. Always retrieve customer license data before drafting
    2. Use contract templates from the knowledge base
    3. Include all required legal clauses based on license type
    4. Never include terms outside the customer's license scope
    5. Always cite the source template and applicable terms
    
    WORKFLOW:
    1. Retrieve customer license details using the license_lookup tool
    2. Search for applicable contract templates
    3. Draft the contract with customer-specific terms
    4. Return the draft with citations
    """,
    tools=[
        AzureAISearchTool(
            index_connection_id=search_connection.id,
            index_name="customer-contracts-index"
        ),
        FunctionTool(functions=[
            {
                "name": "license_lookup",
                "description": "Retrieves customer license details from Dataverse",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The authenticated customer's ID"
                        }
                    },
                    "required": ["customer_id"]
                }
            },
            {
                "name": "generate_document",
                "description": "Generates a Word document from the drafted contract",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "contract_content": {"type": "string"},
                        "template_id": {"type": "string"},
                        "customer_name": {"type": "string"}
                    },
                    "required": ["contract_content", "template_id", "customer_name"]
                }
            }
        ])
    ],
    tool_resources={
        "azure_ai_search": {
            "indexes": [
                {"index_connection_id": search_connection.id, "index_name": "customer-contracts-index"}
            ]
        }
    }
)
```

---

#### 4. **Azure AI Search (Vector Index)**

Copilot Studio supports vectorized indexes using integrated vectorization. Prepare your data and choose an embedded model, then use Import and vectorize data in Azure AI Search to create vector indexes. [Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/knowledge-azure-ai-search)

**Index Schema for Customer Documents:**
```json
{
  "name": "customer-contracts-index",
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true},
    {"name": "title", "type": "Edm.String", "searchable": true},
    {"name": "content", "type": "Edm.String", "searchable": true},
    {"name": "content_vector", "type": "Collection(Edm.Single)", 
     "dimensions": 3072, "vectorSearchProfile": "vector-profile-1"},
    {"name": "document_type", "type": "Edm.String", "filterable": true},
    {"name": "license_tier", "type": "Edm.String", "filterable": true},
    {"name": "effective_date", "type": "Edm.DateTimeOffset", "filterable": true},
    {"name": "source_url", "type": "Edm.String", "retrievable": true},
    {"name": "customer_segment", "type": "Collection(Edm.String)", "filterable": true}
  ],
  "vectorSearch": {
    "algorithms": [
      {
        "name": "hnsw-algorithm",
        "kind": "hnsw",
        "hnswParameters": {
          "metric": "cosine",
          "m": 4,
          "efConstruction": 400,
          "efSearch": 500
        }
      }
    ],
    "profiles": [
      {
        "name": "vector-profile-1",
        "algorithm": "hnsw-algorithm",
        "vectorizer": "text-embedding-3-large"
      }
    ],
    "vectorizers": [
      {
        "name": "text-embedding-3-large",
        "kind": "azureOpenAI",
        "azureOpenAIParameters": {
          "resourceUri": "https://aoai-contoso-prod.openai.azure.com",
          "deploymentId": "embedding-customer",
          "modelName": "text-embedding-3-large"
        }
      }
    ]
  },
  "semantic": {
    "configurations": [
      {
        "name": "semantic-config",
        "prioritizedFields": {
          "contentFields": [{"fieldName": "content"}],
          "titleField": {"fieldName": "title"}
        }
      }
    ]
  }
}
```

**Copilot Studio Knowledge Source Connection:**
Enter the Azure AI Search vector index to be used. Only one vector index can be added. Select Add to complete the connection. [Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/knowledge-azure-ai-search)

---

#### 5. **Function Calling (Azure Functions)**

The Azure AI Foundry Agent Service integrates with Azure Functions, enabling you to create intelligent, event-driven applications with minimal overhead. This combination allows AI-driven workflows to leverage the scalability and flexibility of serverless computing. [Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/azure-functions)

**License Lookup Function:**
```python
# Azure Function: license_lookup
import azure.functions as func
import json
from azure.identity import DefaultAzureCredential
from azure.data.tables import TableServiceClient

app = func.FunctionApp()

@app.function_name(name="LicenseLookup")
@app.route(route="license/{customer_id}", methods=["GET"])
async def license_lookup(req: func.HttpRequest) -> func.HttpResponse:
    """
    Retrieves customer license information from Dataverse/Table Storage
    Called by: Foundry Agent Service via function calling
    Auth: Managed Identity
    """
    customer_id = req.route_params.get('customer_id')
    
    # Connect to Dataverse via Table API
    credential = DefaultAzureCredential()
    table_client = TableServiceClient(
        endpoint="https://org.crm.dynamics.com",
        credential=credential
    ).get_table_client("cr_customerlicenses")
    
    # Query license data
    license_data = table_client.get_entity(
        partition_key="licenses",
        row_key=customer_id
    )
    
    return func.HttpResponse(
        json.dumps({
            "customer_id": customer_id,
            "license_type": license_data["LicenseType"],
            "tier": license_data["Tier"],
            "start_date": license_data["StartDate"],
            "end_date": license_data["EndDate"],
            "entitled_products": license_data["EntitledProducts"],
            "renewal_status": license_data["RenewalStatus"],
            "contract_templates": license_data["AllowedTemplates"]
        }),
        mimetype="application/json"
    )
```

**Contract Generation Function:**
```python
@app.function_name(name="GenerateContract")
@app.route(route="contracts/generate", methods=["POST"])
async def generate_contract(req: func.HttpRequest) -> func.HttpResponse:
    """
    Generates a Word document from contract content
    Uses python-docx to create professional contracts
    """
    body = req.get_json()
    
    from docx import Document
    from docx.shared import Inches, Pt
    from azure.storage.blob import BlobServiceClient
    import io
    
    # Create document from template
    doc = Document()
    
    # Add header
    doc.add_heading(f"License Agreement - {body['customer_name']}", 0)
    
    # Add contract content
    for section in body['contract_content'].split('\n\n'):
        doc.add_paragraph(section)
    
    # Save to blob storage
    credential = DefaultAzureCredential()
    blob_client = BlobServiceClient(
        account_url="https://stcontosocustomerdocs.blob.core.windows.net",
        credential=credential
    ).get_blob_client(
        container="generated-contracts",
        blob=f"{body['customer_name']}_{datetime.now().strftime('%Y%m%d')}.docx"
    )
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    blob_client.upload_blob(buffer, overwrite=True)
    
    return func.HttpResponse(
        json.dumps