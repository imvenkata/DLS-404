# 📊 Epic Status Report Agent

## Overview

The Epic Status Report Agent is a new intelligent component that generates comprehensive, formatted status reports for GitLab epics. It leverages the secure GitLab MCP (Managed Content Provider) server connection to fetch real-time data and uses AI-powered semantic functions to generate professional markdown reports.

## 🏗️ Architecture

The agent follows a clean **two-step workflow**:

### Step 1: Data Fetching 
- **`GitLabMCPAgent.get_epic_status_data()`** connects to GitLab via the secure MCP server
- Gathers comprehensive epic data including:
  - Epic title, description, and URLs
  - Total issue counts (open vs closed)
  - All unique assignees across issues
  - Common labels used
  - Completion percentage calculations

### Step 2: Report Generation
- **`GenerateEpicStatusReport`** semantic function processes the raw data
- Uses AI to synthesize information into a clean, human-readable format
- Generates professional markdown with:
  - Progress bars (visual completion indicators)
  - Summary statistics
  - Contributor lists
  - Actionable insights and next steps

## 🚀 Features

### ✨ **Intelligent Intent Recognition**
- Automatically detects status report requests from natural language
- Supports various query formats:
  - "Generate a status report for epic 42"
  - "How is epic 5 progressing?"
  - "Show me the progress of epic 12"
  - "Status report for epic 1"

### 📈 **Comprehensive Reporting**
- **Summary Statistics**: Total, open, and closed issue counts
- **Progress Visualization**: Text-based progress bars (█████░░░░░)
- **Completion Percentage**: Automatically calculated percentages
- **Team Insights**: All contributors and assignees
- **Label Analysis**: Common labels across epic issues
- **Actionable Takeaways**: AI-generated insights about current state

### 🔒 **Secure Integration**
- Uses established GitLab MCP server for secure API access
- No direct API token handling in the agent code
- Leverages existing authentication and authorization

### 🎯 **Professional Output**
- Clean markdown formatting for easy sharing
- Clickable links to GitLab resources
- Consistent structure across all reports
- Business-ready language and insights

## 📋 Usage Examples

### Basic Status Report
```
User: "Generate a status report for epic 42"

AI Response:
### Epic Status Report: User Authentication & Authorization

**Summary**
- **Total Issues:** 10
- **Open Issues:** 4  
- **Closed Issues:** 6

**Progress**
- **Completion:** 60%
- ██████░░░░

**Contributors**
- vchintal
- jdoe  
- asmith

**Labels**
- authentication
- security
- user-story

**Key Takeaway**
The epic is over halfway complete with strong momentum, requiring focus on the remaining 4 authentication-related issues to reach full completion.

**Link:**
[View Epic on GitLab](https://gitlab.com/groups/dls-404/-/epics/42)
```

### Error Handling
```
User: "Create a status report"

AI Response:
To generate a status report, please provide an epic ID. 

**Examples:**
- "Status report for epic 42"
- "Generate a report for epic 1" 
- "How is epic 5 progressing?"
- "Show me the progress of epic 12"

I'll fetch the latest data from GitLab and create a comprehensive status report.
```

## 🔧 Implementation Details

### Files Modified

#### 1. `rag/agentic/gitlab_mcp_agent.py`
```python
@kernel_function
def get_epic_status_data(self, group_id: str, epic_iid: str) -> str:
    """
    Fetches and aggregates data for a specific epic, including 
    issue counts, statuses, and unique assignees.
    """
```

#### 2. `rag/agentic/mcp_connector.py`
```python
def get_epic_data(self, group_id: str, epic_iid: int) -> Dict[str, Any]:
    """
    Get comprehensive epic data including associated issues.
    """
```

#### 3. `rag/agentic/knowledge_assistant.py`
- Added `STATUS_REPORT` intent recognition
- Added `GenerateEpicStatusReport` semantic function
- Added `_process_status_report_request()` orchestration method

### Intent Recognition Update
```python
Intent Guidelines:
- STATUS_REPORT: User wants to see progress reports, status updates, or epic summaries. 
  Keywords: "status", "report", "progress", "summary", "epic status", "how is epic", "completion"
```

### Data Flow
```
User Query → Intent Recognition → Epic ID Extraction → 
GitLab MCP Agent → Raw Data → Semantic Function → 
Formatted Report → User Response
```

## 🧪 Testing

### Running Tests
```bash
# Run the test script
python test_status_report.py
```

### Test Coverage
- ✅ Basic epic status reports
- ✅ Various query formats
- ✅ Error handling (missing epic ID)
- ✅ Intent recognition accuracy
- ✅ Markdown formatting validation

## 🔮 Future Enhancements

### Planned Features
- **Multi-Epic Reports**: Compare multiple epics in one report
- **Historical Trends**: Show progress over time
- **Team Performance**: Individual contributor metrics
- **Custom Filters**: Filter by labels, assignees, or date ranges
- **Export Options**: PDF, Excel, or email delivery
- **Automated Scheduling**: Regular report generation

### Technical Improvements
- **Caching**: Cache epic data to reduce API calls
- **Batch Processing**: Handle multiple epics efficiently
- **Custom Templates**: User-defined report formats
- **Integration**: Slack/Teams notifications

## 🛠️ Configuration

### Prerequisites
1. ✅ GitLab MCP server configured and accessible
2. ✅ Azure OpenAI services for semantic functions
3. ✅ Proper GitLab group/project permissions

### Environment Variables
```bash
# MCP Server Configuration
MCP_SERVER_URL=your_mcp_server_url
MCP_API_KEY=your_mcp_api_key

# Azure OpenAI Configuration  
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_COMPLETION_DEPLOYMENT=your_deployment
```

## 📈 Benefits

### For Project Managers
- **Real-time Insights**: Always up-to-date epic progress
- **Professional Reports**: Ready for stakeholder meetings
- **Trend Analysis**: Track completion patterns
- **Resource Planning**: Identify bottlenecks and reassign work

### For Development Teams
- **Quick Status**: Instant epic progress visibility
- **Contribution Tracking**: See individual and team contributions
- **Milestone Monitoring**: Track toward epic completion
- **Issue Prioritization**: Focus on remaining open issues

### For Stakeholders
- **Executive Summaries**: High-level progress updates
- **Predictable Format**: Consistent reporting structure
- **Actionable Insights**: Clear next steps and blockers
- **Direct Links**: Easy access to detailed GitLab data

## 🚨 Error Handling

The agent includes comprehensive error handling for:
- **Invalid Epic IDs**: Clear error messages with examples
- **Network Issues**: Graceful MCP server connection failures
- **Permission Errors**: Helpful authentication guidance
- **Data Parsing**: Robust JSON processing with fallbacks
- **AI Generation**: Fallback responses when report generation fails

## 🔗 Integration

### Chainlit Frontend
The agent integrates seamlessly with the existing Chainlit frontend:
- Appears as "Status Reports" in the action buttons
- Supports natural language queries through the chat interface
- Provides rich markdown formatting in responses

### Existing Workflows
- Complements epic decomposition features
- Works alongside issue creation workflows
- Integrates with knowledge discovery capabilities

---

*Built with secure GitLab MCP integration and AI-powered semantic functions for reliable, professional epic status reporting.* 