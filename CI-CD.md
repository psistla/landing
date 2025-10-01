
# Comprehensive Guide to CI/CD Support in Microsoft Fabric

## Executive Summary

Microsoft Fabric provides lifecycle management tools to facilitate continuous integration and continuous deployment, enabling data and analytics teams to deliver value at scale while ensuring production-ready changes [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/cicd-overview) . The platform offers **two main CI/CD components**: Git integration for version control and Deployment Pipelines for automated content delivery across environments.

---

## 1. Different Ways to Achieve CI/CD in Microsoft Fabric

### **A. Native Fabric Tools**

#### **Git Integration**
Git integration in Fabric enables developers to integrate development processes, tools, and best practices directly into the platform, allowing them to backup and version work, revert to previous stages, and collaborate using Git branches [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration) . 

**Supported Git Providers:**
- Azure DevOps (Azure Repos)
- GitHub

**Key Capabilities:**
- Incremental workspace updates can be made frequently and reliably by multiple developers through Git integration, and when ready, content can be delivered to deployment pipelines for testing and distribution [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/cicd-overview)
- Workspace-level integration with folder structure preservation
- Commit, update, and sync operations

#### **Deployment Pipelines**
Microsoft Fabric's deployment pipelines tool provides content creators with a production environment where they can collaborate to manage the lifecycle of organizational content, enabling them to develop and test content before it reaches users [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines) .

**Features:**
- 2-10 customizable stages (default: Development, Test, Production)
- Visual UI for deployment management
- Deployment rules for environment-specific configurations
- Selective deployment of specific items

### **B. API-Driven Approaches**

#### **Fabric REST APIs**
The deployment pipelines Fabric REST APIs enable integration of Fabric into organization automation processes, allowing teams to integrate into DevOps tools like Azure DevOps or GitHub Actions, schedule automatic deployments, deploy multiple pipelines simultaneously, and cascade dependent pipeline deployments [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/pipeline-automation-fabric) .

**Available API Operations:**
- Pipeline management (create, update, delete)
- Stage management
- Deploy content (full or selective)
- User management
- Git operations (connect, commit, update)

#### **PowerShell & Azure DevOps Integration**
- PowerShell scripts for automation
- Power BI automation tools extension for Azure DevOps
- Service Principal support for secure authentication

### **C. Third-Party Tools**

#### **fabric-cicd Python Library**
Fabric-cicd is a code-first solution for deploying Microsoft Fabric items from a repository into a workspace, with capabilities intentionally simplified for streamlining script-based deployments [Microsoft Fabric](https://blog.fabric.microsoft.com/en-us/blog/introducing-fabric-cicd-deployment-tool/) .

**Key Features:**
- Open-source Python library maintained by Microsoft's Azure Data team
- Supports deployment automation without direct API interaction
- Parameterization and find-replace functionality
- Service Principal authentication support

#### **Terraform Provider**
The Terraform Provider for Microsoft Fabric enables broader Infrastructure as Code coverage, allowing teams to standardize automated deployment, strengthen governance with automated role assignments, and enable collaboration by treating Fabric configurations as versioned code [Microsoft Fabric](https://blog.fabric.microsoft.com/en-us/blog/september-2025-fabric-feature-summary/) .

---

## 2. CI/CD Workflow Options

There are different options for building release processes in Fabric, and many organizations take a hybrid approach [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/manage-deployment) :

### **Option 1: Git-Based Deployment (Branch per Environment)**
- Each stage (Dev, Test, Prod) has a dedicated Git branch
- Deployments trigger from Git using Fabric Git APIs
- Requires build environments for testing and configuration changes

### **Option 2: Single Branch with Build Pipelines**
- All deployments originate from one branch (e.g., Main)
- Build pipelines run tests and modify configurations
- Uses Fabric's Update Item Definition APIs

### **Option 3: Hybrid (Git + Deployment Pipelines)**
- Git connected only to Dev stage
- From the dev stage, deployments happen directly between workspaces using Fabric deployment pipelines, with developers able to use deployment pipeline APIs to orchestrate deployment as part of Azure release pipelines or GitHub workflows [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/manage-deployment)

---

## 3. Supported Items and Capabilities

### **What You CAN Do**

#### **Items Supporting Git Integration & Deployment Pipelines:**
Data pipelines, Warehouses, and Spark Environments are now available in both git integration and deployment pipelines, while Spark Job Definitions are available in git integration [Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/fabric-ci-cd-announcements-supporting-new-items-and-much-more/) .

**Full List of Supported Items:**
- **Data Engineering**: Notebooks, Lakehouses, Spark Job Definitions, Spark Environments
- **Data Factory**: Data Pipelines, Dataflow Gen2 (with CI/CD support)
- **Data Warehouse**: Warehouses
- **Power BI**: Reports, Semantic Models (excluding specific types)
- **Real-Time Intelligence**: Eventstreams, Eventhouses, KQL Databases, KQL Querysets, Real-Time Dashboards, Activator
- **Data Science**: ML Models, Experiments

#### **Advanced Capabilities:**
- **Deployment Rules**: Configure environment-specific parameters
- **Selective Deployment**: Deploy only changed items
- **Backward Deployment**: Deploy to previous stages
- **Parameterization**: Dynamic configuration across environments
- **Variable Libraries**: Variable library is a bucket of variables to be used by items across the workspace, allowing dynamic values to be retrieved based on the release stage, is git supported and can be automated [Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/whats-new-with-fabric-ci-cd-may-2025/)

### **What You CANNOT Do**

#### **Unsupported Items:**
Power BI Datasets connected to Analysis Services aren't supported, push datasets and live connections to Analysis Services aren't supported, and PBIR reports aren't supported [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process)

#### **Key Limitations:**

**Git Integration:**
- B2B isn't supported, duplicating names isn't allowed even if Power BI allows name duplication, and conflict resolution is partially done in Git [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration)
- Cross-tenant support for Azure DevOps is in preview
- Works with limited items; unsupported items are ignored

**Deployment Pipelines:**
- Maximum of 300 items can be deployed in a single deployment, downloading a PBIX file after deployment isn't supported, and Microsoft 365 groups aren't supported as pipeline admins [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process)
- When deploying Power BI items for the first time, if another item in the target stage has the same name and type, the deployment fails [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process)
- Circular or self-dependencies cause deployment failure

**Item-Specific Limitations:**
- **Dataflows**: If a dataflow is being refreshed during deployment, the deployment fails, and autobinding isn't supported for dataflows Gen2 [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process)
- **Direct Lake Semantic Models**: When a Direct Lake semantic model is deployed, it doesn't automatically bind to items in the target stage and requires datasource rules to bind to items in the target stage [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process)
- **Spark Environments**: Custom pools aren't supported in deployment pipelines, and environments keep showing diff even if deployment is done successfully [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/environment-git-and-deployment-pipeline)
- **Warehouses**: When warehouse tables are modified such as adding new columns, the entire table is dropped and recreated during deployment, which can result in data loss [Anyonconsulting](https://anyonconsulting.com/cloud-services/how-to-optimize-deployment-pipelines-in-microsoft-fabric-key-considerations-limitations-and-future-enhancements/)

---

## 4. Ease of Implementation

### **Difficulty Assessment: MODERATE to COMPLEX**

#### **For Basic Scenarios** (Easier):
- Setting up native deployment pipelines via UI: **Easy**
- Connecting workspace to Git: **Easy to Moderate**
- Deploying Power BI reports and semantic models: **Moderate**

#### **For Advanced Scenarios** (More Complex):
- You need a build environment with custom scripts to alter workspace-specific attributes like connectionId and lakehouseId before deployment, and need a release pipeline with custom scripts to retrieve item content from git and call corresponding Fabric Item APIs [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/manage-deployment)
- Multi-environment orchestration: **Complex**
- Custom parameterization and deployment rules: **Moderate to Complex**
- API-based automation with service principals: **Complex**

### **Planning Considerations:**

**Prerequisites:**
- A Fabric capacity is required to use all supported Fabric items, and tenant switches must be enabled from the Admin portal [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-get-started)
- Proper permissions in both workspace and Git repository
- Service Principal setup for automation
- Understanding of workspace-item relationships

**Time Investment:**
- Initial setup: 1-2 weeks for basic implementation
- Full automation: 4-8 weeks depending on complexity
- Learning curve for teams: 2-4 weeks

---

## 5. Critical Pitfalls with Situational Examples

### **Pitfall 1: Permission Management Complexity**

**Situation**: A team sets up a deployment pipeline with three workspaces (Dev, Test, Prod). Developers have admin access in Dev but only contributor access in Test.

**Problem**: To deploy content in the GCC environment, you need to be at least a member of both the source and target workspace, with deploying as a contributor not supported yet [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process) .

**Impact**: Deployments fail unexpectedly, blocking releases.

**Mitigation**: Ensure consistent permission levels across all pipeline stages and document permission requirements clearly.

---

### **Pitfall 2: Item Dependencies and Circular References**

**Situation**: A Lakehouse references a Notebook, which in turn references the same Lakehouse for metadata operations.

**Problem**: The deployment fails if any items have circular or self dependencies [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process) .

**Impact**: Unable to deploy critical interdependent components.

**Mitigation**: Design architecture to avoid circular dependencies; use deployment rules to handle cross-references appropriately.

---

### **Pitfall 3: Data Loss in Warehouse Deployments**

**Situation**: A data warehouse table in Dev has new columns added. The team deploys this change to Production where the table contains critical business data.

**Problem**: The entire table is dropped and recreated during deployment, resulting in data loss if the table contains important data [Anyonconsulting](https://anyonconsulting.com/cloud-services/how-to-optimize-deployment-pipelines-in-microsoft-fabric-key-considerations-limitations-and-future-enhancements/) .

**Impact**: Production data loss, business disruption, potential compliance issues.

**Mitigation**: Implement separate data migration strategy; use incremental deployment approaches; maintain data backup procedures; consider manual schema changes for production databases.

---

### **Pitfall 4: Dataflow Refresh Conflicts**

**Situation**: An automated deployment pipeline runs every night at 2 AM. A scheduled dataflow refresh also runs at 2 AM.

**Problem**: If a dataflow is being refreshed during deployment, the deployment fails [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process) .

**Impact**: Deployment failures requiring manual intervention and re-runs.

**Mitigation**: Coordinate deployment schedules with refresh schedules; implement retry logic in deployment scripts; add pre-deployment checks for active refreshes.

---

### **Pitfall 5: Direct Lake Semantic Model Binding Issues**

**Situation**: A Direct Lake semantic model points to a Lakehouse in Dev. Both are deployed to Test environment.

**Problem**: The DirectLake semantic model in the target stage will still be bound to the LakeHouse in the source stage and doesn't automatically bind to items in the target stage [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process) .

**Impact**: Test environment reports show Dev data; incorrect testing results; potential production issues.

**Mitigation**: Always configure datasource rules for Direct Lake models; verify bindings post-deployment; implement automated validation scripts.

---

### **Pitfall 6: Environment-Specific Configuration Management**

**Situation**: A Data Pipeline in Dev connects to a development SQL database. The pipeline needs to connect to production SQL database when deployed to Prod.

**Problem**: Dataflow Gen2 doesn't support dynamic reconfiguration of data source connections, and if your Dataflow connects to sources like SQL databases using parameters, those connections are statically bound and can't be altered using workspace variables or parameterization [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-factory/dataflow-gen2-deployment-pipelines) .

**Impact**: Production pipelines pointing to Dev databases; data corruption risks.

**Mitigation**: Use deployment rules extensively; implement connection parameterization at pipeline level; leverage Variable Libraries where supported; manual connection updates for unsupported scenarios.

---

### **Pitfall 7: Git Commit Size Limitations**

**Situation**: A Spark Environment contains custom libraries totaling 200 MB. The team attempts to commit to Git.

**Problem**: Each commit has an upper limit of 150 MB, and custom libraries larger than 150 MB aren't supported through Git [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/environment-git-and-deployment-pipeline) .

**Impact**: Unable to version control critical environment configurations.

**Mitigation**: Store large libraries externally (Azure Blob, artifact repositories); reference libraries rather than embedding them; split environments into smaller, manageable units.

---

### **Pitfall 8: Name Duplication Across Environments**

**Situation**: Dev workspace has two reports with the same name (Power BI allows this). Team attempts to deploy to Test.

**Problem**: Duplicating names isn't allowed, and even if Power BI allows name duplication, the update, commit, or undo action fails [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-get-started) .

**Impact**: Deployment failures; confusion about which item is which.

**Mitigation**: Enforce unique naming conventions across all environments; implement naming standards in development guidelines; use automated validation before commits.

---

### **Pitfall 9: Workspace Identity Dependencies**

**Situation**: A workspace uses workspace identity to access firewall-protected storage. This configuration is committed to Git and deployed to a different workspace.

**Problem**: If you use a workspace identity in one artifact and commit it to Git, it can be updated back to a fabric workspace only in a workspace connected to the same identity [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-get-started) .

**Impact**: Deployment failures or access denied errors in target environments.

**Mitigation**: Plan workspace identity strategy carefully; document identity requirements; ensure target workspaces have proper identity configurations before deployment.

---

### **Pitfall 10: Staging Lakehouse Synchronization Issues**

**Situation**: A Lakehouse deployment includes the staging lakehouse object, which is supposed to be hidden.

**Problem**: The staging lakehouse can cause synchronization issues where Fabric creates a new staging lakehouse instead of using the existing one, leading to inconsistencies across stages [Anyonconsulting](https://anyonconsulting.com/cloud-services/how-to-optimize-deployment-pipelines-in-microsoft-fabric-key-considerations-limitations-and-future-enhancements/) .

**Impact**: Data inconsistencies between environments; unexpected storage costs.

**Mitigation**: Exclude staging lakehouses from deployments; implement post-deployment validation; monitor for duplicate staging objects.

---

## 6. Available Packages and Libraries

### **Official Microsoft Tools:**

1. **Fabric REST APIs** (Native)
   - Full deployment pipeline management
   - Git integration APIs
   - Item management APIs
   - Workspace APIs

2. **Power BI Automation Tools Extension** (Azure DevOps)
   - Open-source extension
   - Pre-built deployment tasks
   - Service Principal support

3. **fabric-cicd Python Library** (Microsoft Open Source)
   - PyPI package: `pip install fabric-cicd`
   - Supports code-first CI/CD automations to seamlessly integrate source controlled workspaces into a deployment framework [GitHub](https://microsoft.github.io/fabric-cicd/latest/)
   - GitHub: microsoft/fabric-cicd

4. **Terraform Provider for Microsoft Fabric**
   - Infrastructure as Code support
   - Resource management
   - Automated role assignments

### **Community & Third-Party:**
- PowerShell scripts (various GitHub repositories)
- Custom Azure DevOps extensions
- GitHub Actions workflows

---

## 7. Best Practices & Recommendations

### **Architecture Best Practices:**

1. **Workspace Strategy**: Consider having separate workspaces for different teams, as each team can have different permissions, work with different source control repos, and ship content to production in different cadence [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/best-practices-cicd)

2. **Parameterization**: Whenever possible, add parameters to any definition that might change between dev/test/prod stages, and use deployment pipelines parameter rules to set different values for each deployment stage [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/best-practices-cicd)

3. **Isolated Development**: Git best practice is for developers to work in isolation outside of shared workspaces, either using client tools or separate Fabric workspaces with their own branches [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/manage-branches)

4. **Deployment Rules**: Deployment rules are a powerful way to ensure data in production is always connected and available to users, with deployment rules applied ensuring deployments can run while customers see relevant information without disturbance [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/best-practices-cicd)

### **Security Considerations:**
- Use Service Principals for automation
- Implement proper RBAC across all environments
- Protect production workspaces with restrictive permissions
- Enable MFA where required

### **Operational Recommendations:**
- Start simple with UI-based pipelines, then evolve to automation
- Implement comprehensive testing in pre-production stages
- Document all deployment procedures and configurations
- Establish rollback procedures for production issues
- Monitor deployment success rates and failure patterns

---

## Conclusion

Microsoft Fabric's CI/CD capabilities are **maturing rapidly** but still have notable limitations. The platform is **most suitable** for organizations willing to:
- Invest in understanding both native and API-based approaches
- Implement careful planning around item dependencies
- Accept certain manual intervention requirements
- Work within current item support constraints

**Complexity Rating**: **6/10** for basic implementations, **8/10** for enterprise-scale automation

**Recommendation**: Start with native deployment pipelines for immediate value, then progressively implement API-based automation and tools like fabric-cicd as needs grow more complex. Always maintain thorough testing procedures and fallback plans given current platform limitations.

Citations:
- [Introduction to CI/CD in Microsoft Fabric - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/cicd-overview)
- [Overview of Fabric Git integration - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration)
- [Overview of Fabric deployment pipelines - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines)
- [Automate deployment pipeline by using Fabric APIs - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/pipeline-automation-fabric)
- [Introducing fabric-cicd Deployment Tool | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en-us/blog/introducing-fabric-cicd-deployment-tool/)
- [Fabric September 2025 Feature Summary | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en-us/blog/september-2025-fabric-feature-summary/)
- [CI/CD workflow options in Fabric - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/manage-deployment)
- [Fabric CI/CD announcements- supporting new items and much more! | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/fabric-ci-cd-announcements-supporting-new-items-and-much-more/)
- [What’s new with Fabric CI/CD – May 2025 | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/whats-new-with-fabric-ci-cd-may-2025/)
- [The Microsoft Fabric deployment pipelines process - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process)
- [Fabric Environment Git Integration and Deployment Pipeline - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/environment-git-and-deployment-pipeline)
- [How to Optimize Deployment Pipelines in Microsoft Fabric: Key Considerations, Limitations, and Future Enhancements %](https://anyonconsulting.com/cloud-services/how-to-optimize-deployment-pipelines-in-microsoft-fabric-key-considerations-limitations-and-future-enhancements/)
- [Get started with Git integration - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-get-started)
- [CI/CD and ALM solution architectures for Dataflow Gen2 - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-factory/dataflow-gen2-deployment-pipelines)
- [fabric-cicd](https://microsoft.github.io/fabric-cicd/latest/)
- [Best practices for lifecycle management in Fabric - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/best-practices-cicd)
- [Git integration workspaces - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/manage-branches)

More sources:
- [Get started using deployment pipelines, the Fabric Application lifecycle management (ALM) tool - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/get-started-with-deployment-pipelines)
- [CI/CD for pipelines in Data Factory - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-factory/cicd-pipelines)
- [Automate deployment pipelines with APIs for Power BI items - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/pipeline-automation)
- [Operationalize fabric-cicd to work with Microsoft Fabric and Azure DevOps - K Chant](https://www.kevinrchant.com/2025/03/11/operationalize-fabric-cicd-to-work-with-microsoft-fabric-and-azure-devops/)
- [Solved: New Fabric items supported for Git integration (da... - Microsoft Fabric Community](https://community.fabric.microsoft.com/t5/Fabric-platform/New-Fabric-items-supported-for-Git-integration-data-warehouse/m-p/3808055)
- [Git integration process - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-integration-process)
- [Git integration and deployment pipelines - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/git-deployment-pipelines)
- [What is Microsoft Fabric Git integration?](https://github.com/MicrosoftDocs/fabric-docs/blob/main/docs/cicd/git-integration/intro-to-git-integration.md)
- [Introducing git integration in Microsoft Fabric for seamless source control management | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/introducing-git-integration-in-microsoft-fabric-for-seamless-source-control-management/)
- [GitHub - microsoft/fabric-cicd: Jumpstart CICD deployments in Microsoft Fabric](https://github.com/microsoft/fabric-cicd)
- [fabric-cicd - Microsoft Open Source](https://microsoft.github.io/fabric-cicd/0.1.19/)
- [fabric-cicd · PyPI](https://pypi.org/project/fabric-cicd/)
- [Operationalize fabric-cicd to work with Microsoft Fabric and YAML Pipelines - K Chant](https://www.kevinrchant.com/2025/03/18/operationalize-fabric-cicd-to-work-with-microsoft-fabric-and-yaml-pipelines/)
- [Initial tests of fabric-cicd - K Chant](https://www.kevinrchant.com/2025/02/27/initial-tests-of-fabric-cicd/)
- [Optimizing for CI/CD in Microsoft Fabric | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/optimizing-for-ci-cd-in-microsoft-fabric/)
- [Fabric May 2025 Feature Summary | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/fabric-may-2025-feature-summary/)
- [Data Factory limitations overview - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-factory/data-factory-limitations)
- [Microsoft Fabric REST APIs for automation and embedded analytics - Microsoft Fabric REST APIs | Microsoft Learn](https://learn.microsoft.com/en-us/rest/api/fabric/articles/using-fabric-apis)
- [REST API capabilities for Fabric Data Factory - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-factory/pipeline-rest-api-capabilities)
- [Microsoft Fabric REST API references - Microsoft Fabric REST APIs | Microsoft Learn](https://learn.microsoft.com/en-us/rest/api/fabric/articles/)
- [Fabric May 2025 Feature Summary | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en-us/blog/fabric-may-2025-feature-summary/)
- [Fabric API quickstart - Microsoft Fabric REST APIs | Microsoft Learn](https://learn.microsoft.com/en-us/rest/api/fabric/articles/get-started/fabric-api-quickstart)
- [Process automation using Microsoft Fabric REST API](https://msfabric.pl/en/blog/education/process-automation-using-microsoft-fabric-rest-api)