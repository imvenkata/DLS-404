# Agentic RAG System Architecture

## Overview

The agentic RAG system in this repository is built on **Semantic Kernel** and provides an intelligent, action-oriented approach to retrieval-augmented generation. Unlike traditional RAG systems that only answer questions, this system can understand user intent, execute complex workflows, and take actions based on user queries.

## Core Architecture Components

### 1. KnowledgeAssistant (`knowledge_assistant.py`)

The **KnowledgeAssistant** serves as the main orchestrator that coordinates all agentic workflows:

- **Central Coordinator**: Manages the entire agentic workflow pipeline
- **Semantic Kernel Integration**: Hosts the Semantic Kernel instance with Azure OpenAI integration
- **Intent Recognition**: Routes user queries to appropriate specialized agents
- **Plugin Management**: Registers and manages various plugins and functions
- **Fallback Handling**: Ensures system resilience when components fail

```python
class KnowledgeAssistant:
    def __init__(self, ...):
        self.kernel = sk.Kernel()
        self.setup_kernel()
        self.gitlab_actions = GitLabEnhancedActions()
        self.epic_status_agent = EpicStatusReportAgent()
        self.issue_agent = GitLabIssueAgent()
```

### 2. Specialized Agents

The system employs multiple specialized agents, each handling specific domains:

#### **EpicStatusReportAgent** (`epic_status_agent.py`)
- **Purpose**: Generates comprehensive GitLab epic status reports
- **Capabilities**: 
  - Epic metrics aggregation (issue counts, assignees, labels)
  - Progress tracking and completion analysis
  - Formatted report generation
  - MCP server integration with fallback to direct GitLab API

#### **GitLabIssueAgent** (`gitlab_issue_agent.py`)
- **Purpose**: Handles issue creation workflows with user review
- **Capabilities**:
  - Multi-step issue creation process
  - User story decomposition
  - Draft review and confirmation workflows
  - Template-based issue generation

#### **GitLabMCPAgent** (`gitlab_mcp_agent.py`)
- **Purpose**: Manages GitLab operations through MCP protocol
- **Capabilities**:
  - MCP-based GitLab operations
  - Enhanced data retrieval
  - Protocol standardization

#### **GitLabEnhancedActions** (`gitlab_enhanced.py`)
- **Purpose**: Provides advanced GitLab operations
- **Capabilities**:
  - Epic issue count and management
  - User story creation with structured format
  - Technical question answering with GitLab context
  - Status report generation

### 3. MCP (Model Context Protocol) Integration

#### **MCPConnector** (`mcp_connector.py`)
- **Purpose**: Standardized interface for external content providers
- **Features**:
  - Resource listing and management
  - Content retrieval and search
  - Authentication and session management
  - Error handling and retry logic

#### **GitLabMCPClient** (`mcp_connector.py`)
- **Purpose**: GitLab-specific MCP client implementation
- **Capabilities**:
  - GitLab resource access through MCP
  - Epic and issue data retrieval
  - Project and group management

## Plugin Architecture

### Semantic Plugins

Located in `rag/agentic/plugins/semantic/`:

#### **Extract Info Plugin** (`extract_info/`)
- **Purpose**: Extracts structured information from technical documents
- **Configuration**:
  - Temperature: 0.1 (for consistent, factual extraction)
  - Max tokens: 1000
  - Top-p: 0.5
- **Use Cases**: Technical documentation analysis, requirement extraction

#### **Summarize Plugin** (`summarize/`)
- **Purpose**: Analyzes and summarizes technical content
- **Configuration**:
  - Temperature: 0.2 (for content analysis)
  - Max tokens: 1000
  - Top-p: 0.5
- **Use Cases**: Code review summaries, documentation analysis

## Workflow Architecture

### Workflow Setup & Initialization

The workflow system is built on a foundation of **Semantic Kernel** and **AI-powered functions** that are registered during system initialization:

#### **Component Initialization**
```python
def __init__(self, ...):
    # Initialize core components
    self.gitlab_auth = GitLabAuth(config_file=gitlab_auth_config)
    self.gitlab_actions = GitLabEnhancedActions()
    self.epic_status_agent = EpicStatusReportAgent()
    self.issue_agent = GitLabIssueAgent()
    
    # Setup Semantic Kernel
    self.kernel = sk.Kernel()
    self.setup_kernel()
    
    # Initialize search client
    self.search_client = EnhancedAzureSearchClient(...)
```

#### **Semantic Function Registration**
The system registers multiple AI-powered functions during setup:

```python
def _register_semantic_functions(self):
    # Intent Recognition Function
    intent_recognition_function = KernelFunction.from_prompt(...)
    self.kernel.add_function(plugin_name="IntentRecognition", function=intent_recognition_function)
    
    # Knowledge Discovery Function
    knowledge_discovery_function = KernelFunction.from_prompt(...)
    self.kernel.add_function(plugin_name="KnowledgeDiscovery", function=knowledge_discovery_function)
    
    # Code Generation Function
    code_gen_function = KernelFunction.from_prompt(...)
    self.kernel.add_function(plugin_name="CodeGeneration", function=code_gen_function)
    
    # Epic Decomposition Function
    epic_decomp_function = KernelFunction.from_prompt(...)
    self.kernel.add_function(plugin_name="GitLabIssueAgent", function=epic_decomp_function)
    
    # Status Report Generation Function
    report_gen_function = KernelFunction.from_prompt(...)
    self.kernel.add_function(plugin_name="StatusReporting", function=report_gen_function)
```

### Main Workflow Pipeline

#### **Entry Point: `process_query()`**
The main workflow starts with the `process_query()` method:

```python
async def process_query(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    # 1. Check if issue agent is awaiting confirmation
    if self.issue_agent.is_awaiting_confirmation():
        return await self._handle_issue_confirmation(query)
    
    # 2. Intent Recognition & Routing
    intent_context = KernelArguments(input=query)
    intent_result = await self.kernel.invoke(
        plugin_name="IntentRecognition", 
        function_name="recognize_intent", 
        arguments=intent_context
    )
    
    # 3. Route to appropriate workflow based on intent
    if intent == "ISSUE_CREATION":
        return await self._process_issue_creation(query)
    elif intent == "CODE_GENERATION":
        return await self._process_context_aware_code_generation(query)
    elif intent == "STATUS_REPORT":
        return await self._process_status_report_request(query)
    else:
        return await self._process_knowledge_discovery(query, metadata)
```

### Intent Recognition & Routing

The system employs AI-powered intent recognition that categorizes user queries into:

1. **KNOWLEDGE_DISCOVERY**
   - **Keywords**: "what is", "how does", "explain", "charter", "documentation"
   - **Purpose**: Information retrieval and documentation queries

2. **ISSUE_CREATION**
   - **Keywords**: "create issue", "user story", "epic", "as a [role] I want"
   - **Purpose**: GitLab issue and user story creation

3. **CODE_GENERATION**
   - **Keywords**: "create", "generate", "write", "implement", "terraform"
   - **Purpose**: Code writing and implementation requests

4. **STATUS_REPORT**
   - **Keywords**: "status", "report", "progress", "summary", "epic status"
   - **Purpose**: Progress reports and epic status queries

5. **GENERAL_QUERY**
   - **Purpose**: Miscellaneous queries that don't fit other categories

### Specialized Workflow Implementations

#### **1. Issue Creation Workflow** (`_process_issue_creation`)

This workflow has **three distinct paths**:

##### **Path A: Epic Decomposition**
```python
if (epic_match or epic_url_match) and not has_story_details:
    epic_iid = int(epic_match.group(1))
    if has_specific_story_type:
        return await self._create_specific_story_for_epic(query, epic_iid)
    else:
        return await self._decompose_epic_workflow(epic_iid)
```

##### **Path B: Single Issue Creation**
```python
elif has_story_details:
    # Extract user story components using regex
    story_match = re.search(r'as a ([^,]+),\s*i want to ([^,]+)(?:,\s*so that (.+))?', query.lower())
    # Create single issue workflow
```

##### **Path C: Specific Story Type for Epic**
```python
if has_specific_story_type:
    return await self._create_specific_story_for_epic(query, epic_iid)
```

#### **2. Epic Decomposition Workflow** (`_decompose_epic_workflow`)

```python
async def _decompose_epic_workflow(self, epic_iid: int) -> str:
    # 1. Fetch Epic Details via GitLab API
    epic_details_str = await self.kernel.invoke(
        plugin_name="GitLabEnhancedActions", 
        function_name="get_epic_details", 
        arguments=KernelArguments(group_id=group_id, epic_iid=epic_iid)
    )
    
    # 2. Decompose Epic into Stories using AI
    story_list_str = await self.kernel.invoke(
        plugin_name="GitLabIssueAgent", 
        function_name="DecomposeEpicIntoStories", 
        arguments=decomp_args
    )
    
    # 3. Hand off to issue agent for batch confirmation
    return self.issue_agent.start_epic_decomposition_flow(epic_context, decomposed_stories)
```

#### **3. Code Generation Workflow** (`_process_context_aware_code_generation`)

```python
async def _process_context_aware_code_generation(self, query: str) -> str:
    # 1. Retrieve relevant code snippets from search index
    search_results = self.search_client.search(
        query=query, 
        embedding=query_embedding, 
        source_types=['code'],  # Prioritize code files
        top=5,  # Get top 5 most relevant code chunks
        use_vector_search=True
    )
    
    # 2. Assemble context from retrieved code
    context_string = self._format_code_context(search_results)
    
    # 3. Generate new code using AI with context
    result = await self.kernel.invoke(
        plugin_name="CodeGeneration",
        function_name="GenerateFromContext",
        arguments=KernelArguments(request=query, context=context_string)
    )
```

#### **4. Knowledge Discovery Workflow** (`_process_knowledge_discovery`)

```python
async def _process_knowledge_discovery(self, query: str, metadata: Dict[str, Any]) -> str:
    # 1. Generate query embedding
    query_embedding = embeddings_generator.generate_embedding(query)
    
    # 2. Perform hybrid search (vector + keyword)
    search_results = self.search_client.search(
        query=query, 
        embedding=query_embedding, 
        use_vector_search=True
    )
    
    # 3. Fallback to keyword-only search if no results
    if not search_results:
        search_results = self.search_client.search(query=query, use_vector_search=False)
    
    # 4. Format results with citations
    context = self._format_search_results(search_results)
    
    # 5. Generate AI-powered answer with context
    answer_result = await self.kernel.invoke(
        plugin_name="KnowledgeDiscovery",
        function_name="answer_knowledge_query",
        arguments=KernelArguments(input=query, context=context)
    )
```

### Multi-Step Workflows

#### **Issue Creation Workflow**
```
User Request → Intent Recognition → Issue Agent → Draft Generation → User Review → Confirmation → Issue Creation
```

#### **Epic Status Workflow**
```
User Query → Epic Parsing → Data Retrieval → Metrics Aggregation → Report Generation → Formatted Output
```

#### **Knowledge Discovery Workflow**
```
User Question → Intent Recognition → Context Retrieval → AI Analysis → Citation Generation → Response
```

### Confirmation Workflow System

#### **Multi-Step Confirmation Handling**

The system implements a sophisticated confirmation workflow:

```python
async def _handle_issue_confirmation(self, query: str) -> str:
    if self.issue_agent.get_state() == "awaiting_batch_confirmation":
        # Handle batch confirmation for epic decomposition
        if "yes" in query.lower():
            # Create all issues in batch
            for draft in drafts:
                result = await self.gitlab_mcp_agent.create_issue(...)
        elif "no" in query.lower():
            self.issue_agent.reset()
            return "❌ Cancelled the batch issue creation."
    
    elif self.issue_agent.get_state() == "awaiting_confirmation":
        # Handle single issue confirmation
        if "yes" in query.lower():
            # Create single issue
            result = await self.gitlab_mcp_agent.create_issue(...)
```

### Workflow Architecture Benefits

#### **1. Modular Design**
- Each workflow is implemented as a separate method
- Easy to add new workflows or modify existing ones
- Clear separation of concerns

#### **2. AI-Powered Decision Making**
- Intent recognition using LLM
- Context-aware code generation
- Intelligent epic decomposition

#### **3. Fallback Mechanisms**
- Multiple search strategies (vector + keyword)
- Graceful error handling
- Component isolation

#### **4. State Management**
- Issue agent maintains workflow state
- Confirmation workflows with user interaction
- Batch vs. single operation handling

#### **5. Integration Points**
- GitLab API integration
- MCP server support
- Azure services integration
- Search index integration

## Fallback & Resilience Architecture

### Graceful Degradation Strategy

#### **MCP Fallback Mechanism**
1. **Primary Path**: MCP server integration for enhanced capabilities
2. **Fallback Path**: Direct GitLab API integration for core functionality
3. **Error Handling**: Comprehensive logging and graceful failure handling

#### **Import Safety**
- **Graceful Import Handling**: Prevents system crashes from missing dependencies
- **Component Isolation**: Individual component failures don't affect the entire system
- **Logging & Monitoring**: Comprehensive error tracking and system health monitoring

### Dual Integration Paths

```
┌─────────────────┐    ┌─────────────────┐
│   MCP Server    │    │  Direct GitLab  │
│   Integration   │    │     API         │
│   (Primary)     │    │   (Fallback)    │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│         Agentic RAG System             │
│         (Unified Interface)            │
└─────────────────────────────────────────┘
```

## Technical Implementation

### Semantic Kernel Integration

#### **Function Registration**
- **Dynamic Registration**: Functions are registered at runtime based on configuration
- **Plugin Management**: Modular plugin architecture for extensibility
- **Context Management**: Intelligent context handling for improved responses

#### **Kernel Configuration**
```python
def setup_kernel(self):
    self.kernel.add_service(AzureChatCompletion(...))
    self.kernel.add_plugin(self.gitlab_actions, "GitLabEnhancedActions")
    self._register_semantic_functions()
```

### Azure Services Integration

#### **Azure OpenAI**
- **Chat Completion**: For LLM capabilities and conversation management
- **Embeddings**: For semantic search and context understanding
- **Configuration**: Environment-based deployment and API key management

#### **Azure AI Search**
- **Intelligent Retrieval**: Vector and keyword search capabilities
- **Context Enhancement**: Provides relevant information for agent decisions
- **Performance Optimization**: Efficient search with result ranking

#### **Azure Blob Storage**
- **Data Persistence**: Stores extracted and processed data
- **Context Storage**: Maintains conversation and workflow state
- **Scalability**: Handles large volumes of GitLab data

## Data Flow Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ User Query  │───▶│ Intent Recognition│───▶│ Agent Selection │───▶│ Context Retrieval│
└─────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │                       │
                                                      ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Response        │◀───│ Response        │◀───│ Action          │◀───│ Azure AI        │
│ Generation      │    │ Formatting      │    │ Execution       │    │ Search +        │
└─────────────────┘    └─────────────────┘    └─────────────────┘    │ Context         │
                                                                     └─────────────────┘
```

### Detailed Flow Steps

1. **User Query Input**: User submits a natural language query
2. **Intent Recognition**: AI-powered analysis determines query intent
3. **Agent Selection**: System routes to appropriate specialized agent
4. **Context Retrieval**: Relevant information is gathered from Azure AI Search
5. **Action Execution**: Agent executes appropriate actions (GitLab operations, etc.)
6. **Response Generation**: AI generates comprehensive response with context
7. **Response Formatting**: Output is formatted and presented to user

## Key Architectural Benefits

### 1. **Modularity**
- Each agent handles specific domains independently
- Easy to add new capabilities without affecting existing functionality
- Clear separation of concerns

### 2. **Extensibility**
- Plugin-based architecture supports easy growth
- New agents can be added without system modifications
- Semantic plugins can be extended for new use cases

### 3. **Resilience**
- Multiple fallback mechanisms ensure system availability
- Graceful degradation when components fail
- Comprehensive error handling and logging

### 4. **Intelligence**
- AI-powered intent recognition and routing
- Context-aware decision making
- Adaptive response generation

### 5. **Integration**
- Seamless GitLab integration through multiple paths
- MCP protocol support for external services
- Azure services integration for scalability

### 6. **Scalability**
- Plugin-based architecture supports growth
- Stateless design for horizontal scaling
- Efficient resource utilization

## Configuration & Environment

### Required Environment Variables

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_KEY=your_openai_key
AZURE_OPENAI_COMPLETION_DEPLOYMENT=gpt-35-turbo
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your_search_key
AZURE_SEARCH_INDEX_NAME=gitlab-index

# GitLab Configuration
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your_gitlab_token

# MCP Server Configuration (Optional)
MCP_SERVER_URL=your_mcp_server_url
MCP_API_KEY=your_mcp_api_key
```

### Dependencies

- **Semantic Kernel**: Core AI orchestration framework
- **Azure OpenAI**: LLM and embedding services
- **Azure AI Search**: Intelligent information retrieval
- **python-gitlab**: Direct GitLab API integration
- **requests**: HTTP client for MCP server communication

## Future Enhancements

### Planned Architectural Improvements

1. **Multi-Agent Orchestration**: Enhanced coordination between multiple agents
2. **Advanced Plugin System**: More sophisticated plugin management and versioning
3. **Performance Optimization**: Caching and optimization strategies
4. **Enhanced Monitoring**: Comprehensive system health and performance monitoring
5. **API Gateway**: Centralized API management and rate limiting

### Extension Points

1. **New Agent Types**: Additional specialized agents for different domains
2. **Custom Plugins**: User-defined semantic plugins
3. **Integration APIs**: Standardized interfaces for external systems
4. **Workflow Engine**: Visual workflow design and management

## Conclusion

The agentic RAG system represents a significant evolution beyond traditional RAG implementations. By combining Semantic Kernel's AI orchestration capabilities with specialized agents and a robust plugin architecture, the system provides:

- **Intelligent Query Understanding**: AI-powered intent recognition and routing
- **Action-Oriented Capabilities**: Ability to execute complex workflows and take actions
- **Resilient Architecture**: Multiple fallback mechanisms and graceful degradation
- **Extensible Design**: Easy addition of new capabilities and integrations

This architecture transforms the system from a simple question-answering tool into an intelligent, action-oriented assistant that can understand complex user needs, execute sophisticated workflows, and provide comprehensive solutions for GitLab project management and knowledge discovery.
