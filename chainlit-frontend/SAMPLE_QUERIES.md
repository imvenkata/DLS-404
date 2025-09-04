# 📝 Sample Queries for Testing

## 🔍 **Knowledge Discovery Queries**
Test the RAG (Retrieval-Augmented Generation) capabilities:

```markdown
**Project Information:**
- "What is the DLS-404 project about?"
- "Show me the project charter and objectives"
- "What are the main components of this system?"

**Technical Documentation:**
- "How does the chunking system work?"
- "Explain the embedding generation process"
- "What is the Azure Search integration strategy?"

**Architecture Questions:**
- "Describe the agentic workflow architecture"
- "How does the knowledge assistant route queries?"
- "What are the different types of agents available?"
```

## 📋 **GitLab Issue Management Queries**
Test GitLab integration and issue creation:

```markdown
**Single Issue Creation:**
- "As a developer, I want to implement user authentication, so that users can securely access the system"
- "As a QA engineer, I want to create test cases, so that we can validate functionality"
- "As a DevOps engineer, I want to set up CI/CD pipeline, so that we can automate deployments"

**Epic Decomposition:**
- "Decompose epic 1 into user stories"
- "Create stories for epic 42 in project DLS-404"
- "Break down epic 'Implement RAG System' into actionable stories"

**Specific Story Types:**
- "Create UAT testing story for epic 1"
- "Create security testing story for epic 2"
- "Create performance testing story for epic 3"
- "Create documentation story for epic 1"
```

## 💻 **Code Generation Queries**
Test context-aware code generation:

```markdown
**Python Development:**
- "Create a Python function to process GitLab issues"
- "Generate a data processing script for CSV files"
- "Write a configuration management class"

**Infrastructure as Code:**
- "Create a Terraform template for Azure OpenAI service"
- "Generate Azure Search index configuration"
- "Write a Docker Compose file for the application"

**API Development:**
- "Create a FastAPI endpoint for user management"
- "Generate a REST client for GitLab API"
- "Write authentication middleware"
```

## 📊 **Status Report Queries**
Test epic status reporting:

```markdown
**Epic Progress:**
- "Generate status report for epic 1"
- "Show me the progress of epic 42"
- "What's the current status of the RAG implementation epic?"

**Project Overview:**
- "Give me a summary of all active epics"
- "Show project completion status"
- "What are the bottlenecks in our current epics?"
```

## 🔧 **Technical Support Queries**
Test troubleshooting and help capabilities:

```markdown
**System Information:**
- "What Azure services are configured?"
- "Show me the current configuration settings"
- "What are the system requirements?"

**Error Resolution:**
- "How do I fix import errors?"
- "What should I do if the search index is empty?"
- "How to troubleshoot GitLab connection issues?"
```

## 📚 **Documentation Queries**
Test documentation search and generation:

```markdown
**Search Documentation:**
- "Find information about the chunking strategy"
- "Show me documentation about the embedding system"
- "What are the best practices for this project?"

**Generate Documentation:**
- "Create a README for the new feature"
- "Generate API documentation for the search endpoint"
- "Write deployment instructions for the system"
```

## 🎯 **Query Categories by Intent**

### **KNOWLEDGE_DISCOVERY** (Default)
- Information retrieval from project documentation
- Code explanation and analysis
- Best practices and guidelines

### **ISSUE_CREATION**
- GitLab issue generation
- User story creation
- Epic decomposition workflows

### **CODE_GENERATION**
- Context-aware code creation
- Pattern-consistent implementations
- Infrastructure as code templates

### **STATUS_REPORT**
- Epic progress reports
- Project completion summaries
- Performance metrics

### **GENERAL_QUERY**
- System information
- Configuration details
- Help and troubleshooting

## 🧪 **Testing Workflow**

1. **Start with Simple Queries:**
   ```
   "Hello, what can you help me with?"
   "What is this project about?"
   ```

2. **Test Knowledge Discovery:**
   ```
   "Explain the RAG system architecture"
   "How does the chunking work?"
   ```

3. **Test GitLab Integration:**
   ```
   "Create a user story for implementing authentication"
   "Decompose epic 1 into stories"
   ```

4. **Test Code Generation:**
   ```
   "Generate a Python function for data processing"
   "Create a Terraform template for Azure services"
   ```

5. **Test Advanced Features:**
   ```
   "Upload and analyze this document"
   "Generate a status report for epic 1"
   ```

## 📋 **Expected Responses**

- **Knowledge Queries**: Detailed answers with source citations
- **Issue Creation**: Structured GitLab issues with confirmation
- **Code Generation**: Context-aware code with explanations
- **Status Reports**: Formatted progress summaries
- **Error Handling**: Helpful error messages with suggestions

---

## 🚀 **Quick Test Commands**

### **Basic Knowledge Discovery:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the DLS-404 project about?", "metadata": {}}'
```

### **GitLab Issue Creation:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Create UAT testing story for epic 1", "metadata": {}}'
```

### **Code Generation:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a Python function to process GitLab issues", "metadata": {}}'
```

### **Status Report:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Generate status report for epic 1", "metadata": {}}'
```
