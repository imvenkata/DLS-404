"""
AI-Powered Knowledge Assistant with Agentic Workflow.

This module implements a Knowledge Assistant with Semantic Kernel that:
1. Provides robust GitLab integration
2. Enables agentic workflows for knowledge discovery and generation
3. Supports interactive issue creation with user review and confirmation
"""
import os
import re
import logging
import json
from typing import Dict, List, Any, Optional

import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.prompt_template.input_variable import InputVariable

from config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_COMPLETION_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION
)
from rag.agentic.gitlab_enhanced import GitLabEnhancedActions
from rag.agentic.gitlab_auth import GitLabAuth
from rag.agentic.gitlab_mcp_agent import GitLabMCPAgent
from rag.agentic.gitlab_issue_agent import GitLabIssueAgent
from search.enhanced_azure_search import EnhancedAzureSearchClient
from processors.embeddings_generator import EmbeddingsGenerator
from config.mcp_config import is_mcp_configured

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeAssistant:
    def __init__(
        self,
        openai_endpoint: str = AZURE_OPENAI_ENDPOINT,
        openai_api_key: str = AZURE_OPENAI_KEY,
        openai_deployment: str = AZURE_OPENAI_COMPLETION_DEPLOYMENT,
        search_endpoint: Optional[str] = None,
        search_key: Optional[str] = None,
        search_index_name: Optional[str] = None,
        gitlab_auth_config: Optional[str] = None
    ):
        self.openai_endpoint = openai_endpoint
        self.openai_api_key = openai_api_key
        self.openai_deployment = openai_deployment
        
        logger.info(f"Azure OpenAI Endpoint: {self.openai_endpoint}")
        logger.info(f"Azure OpenAI Deployment: {self.openai_deployment}")
        
        self.gitlab_auth = GitLabAuth(config_file=gitlab_auth_config)
        self.gitlab_actions = GitLabEnhancedActions()
        
        self.gitlab_mcp_agent = None
        if is_mcp_configured():
            try:
                self.gitlab_mcp_agent = GitLabMCPAgent()
                logger.info("GitLab MCP agent initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize GitLab MCP agent: {str(e)}")
        
        # Initialize GitLab Issue Agent for issue creation workflows
        self.issue_agent = GitLabIssueAgent()
        
        self.kernel = sk.Kernel()
        self.setup_kernel()
        
        self.search_client = None
        if search_endpoint and search_key and search_index_name:
            self.search_client = EnhancedAzureSearchClient(
                endpoint=search_endpoint,
                api_key=search_key,
                index_name=search_index_name
            )
            logger.info("Initialized enhanced Azure Search client")
        
    def setup_kernel(self):
        try:
            if not self.openai_endpoint or not self.openai_api_key or not self.openai_deployment:
                raise ValueError("Missing Azure OpenAI configuration.")
                
            self.kernel.add_service(
                AzureChatCompletion(
                    service_id="default",
                    deployment_name=self.openai_deployment,
                    endpoint=self.openai_endpoint,
                    api_key=self.openai_api_key,
                    api_version=AZURE_OPENAI_API_VERSION
                )
            )
            logger.info(f"Added Azure OpenAI chat service with deployment {self.openai_deployment}")
            
            self.kernel.add_plugin(self.gitlab_actions, "GitLabActions")
            logger.info("Registered GitLab enhanced actions plugin")
            
            self._register_semantic_functions()
            logger.info("Registered semantic functions for agentic workflows")
            
        except Exception as e:
            logger.error(f"Error initializing Knowledge Assistant: {str(e)}")
            raise
    
    def _register_semantic_functions(self):
        """Registers functions that use prompts to interact with the AI."""
        
        # A more constrained prompt for intent recognition.
        intent_recognition_prompt = """
You are an AI assistant that categorizes user queries.
User query: {{$input}}

Analyze the query and select the most appropriate intent from this list: [KNOWLEDGE_DISCOVERY, ISSUE_CREATION, CODE_GENERATION, STATUS_REPORT, GENERAL_QUERY].

Intent Guidelines:
- ISSUE_CREATION: User wants to create GitLab issues, user stories, or decompose epics. Keywords: "create issue", "user story", "epic", "as a [role] I want", "create stories", "decompose epic"
- CODE_GENERATION: User wants to generate, create, write, or implement code. Keywords: "create", "generate", "write", "implement", "terraform", "function", "script", "code"
- STATUS_REPORT: User wants to see progress reports, status updates, or epic summaries. Keywords: "status", "report", "progress", "summary", "epic status", "how is epic", "completion"
- KNOWLEDGE_DISCOVERY: User wants to find information, documentation, or project details. Keywords: "what is", "how does", "explain", "charter", "documentation"
- GENERAL_QUERY: All other queries that don't fit the above categories.

Output ONLY a JSON object with the following structure:
{
    "intent": "SELECTED_INTENT_FROM_LIST"
}
"""
        try:
            prompt_config = PromptTemplateConfig(
                template=intent_recognition_prompt,
                description="Recognize the intent of a user query",
                input_variables=[InputVariable(name="input", is_required=True)],
                execution_settings={"default": {"max_tokens": 150, "temperature": 0.0}}
            )
            
            intent_recognition_function = KernelFunction.from_prompt(
                function_name="recognize_intent",
                plugin_name="IntentRecognition",
                prompt=intent_recognition_prompt,
                prompt_template_config=prompt_config,
            )
            self.kernel.add_function(plugin_name="IntentRecognition", function=intent_recognition_function)
            logger.info("Successfully registered intent recognition function")

        except Exception as e:
            logger.error(f"Failed to register intent recognition function: {str(e)}")

        knowledge_discovery_prompt = """
You are an AI assistant providing knowledge discovery with cited answers.
User question: {{$input}}
Retrieved information:
{{$context}}
CRITICAL INSTRUCTIONS:
1. NEVER generate an answer that's not explicitly found in the retrieved information.
2. ONLY use facts, code, and information directly from the retrieved knowledge sources.
3. ALWAYS provide clear citations for every piece of information using the format [Source: path/to/file](URL).
If the retrieved information is not relevant, state that you couldn't find any information.
"""
        try:
            knowledge_discovery_config = PromptTemplateConfig(
                template=knowledge_discovery_prompt,
                description="Answer knowledge discovery queries with cited information",
                input_variables=[InputVariable(name="input", is_required=True), InputVariable(name="context", is_required=True)],
                execution_settings={"default": {"max_tokens": 1500}}
            )
            
            knowledge_discovery_function = KernelFunction.from_prompt(
                function_name="answer_knowledge_query",
                plugin_name="KnowledgeDiscovery",
                prompt=knowledge_discovery_prompt,
                prompt_template_config=knowledge_discovery_config
            )
            self.kernel.add_function(plugin_name="KnowledgeDiscovery", function=knowledge_discovery_function)
            logger.info("Successfully registered knowledge discovery function")

        except Exception as e:
            logger.error(f"Failed to register knowledge discovery function: {str(e)}")

        # A generic, context-aware code generation prompt
        contextual_code_gen_prompt = """
Act as an expert pair programmer. Your goal is to write new code that is consistent with the style, patterns, and libraries found in the user's existing codebase.

User Request: "{{$request}}"

---
Relevant Code from Existing Codebase (Context):
{{$context}}
---

CRITICAL INSTRUCTIONS:
1.  Analyze the provided "Context" to understand the project's conventions (e.g., libraries used, variable naming, function structure, error handling).
2.  Generate a new, complete, and well-commented piece of code that directly fulfills the "User Request".
3.  **IMPORTANT**: Prioritize using the exact same libraries and patterns from the "Context". For example, if the context uses `requests` for HTTP calls, use `requests` in your answer, not `httpx` or `urllib`.
4.  If the "Context" is empty or not relevant, generate the code based on general industry best practices for the language requested.
5.  Provide a brief explanation of *why* you wrote the code this way, referencing the context if possible. For example: "I used the `redis` library as it's already in use in `utils/cache.py`."
6.  Wrap the final code in a single markdown code block with the correct language identifier (e.g., ```python, ```javascript, ```hcl).
"""
        try:
            code_gen_config = PromptTemplateConfig(
                template=contextual_code_gen_prompt,
                description="Generates code consistent with existing codebase patterns.",
                input_variables=[
                    InputVariable(name="request", description="The user's code request", is_required=True),
                    InputVariable(name="context", description="Relevant code snippets from the user's codebase", is_required=True)
                ],
                execution_settings={"default": {"max_tokens": 2000}}
            )
            
            code_gen_function = KernelFunction.from_prompt(
                function_name="GenerateFromContext",
                plugin_name="CodeGeneration",
                prompt=contextual_code_gen_prompt,
                prompt_template_config=code_gen_config
            )
            self.kernel.add_function(plugin_name="CodeGeneration", function=code_gen_function)
            logger.info("Successfully registered context-aware code generation function.")

        except Exception as e:
            logger.error(f"Failed to register code generation function: {e}")

        # Epic decomposition function for issue creation agent
        epic_decomposition_prompt = """
Act as an expert Agile Product Manager. Your task is to decompose a high-level epic into a set of smaller, actionable user stories.

Analyze the epic's title and description provided below. Based on the requirements and goals described, generate a list of user stories in the format "As a [role], I want to [action], so that [benefit]".

**Epic Title:**
{{$epic_title}}

**Epic Description:**
{{$epic_description}}

---
INSTRUCTIONS:
- Identify distinct features or pieces of work within the epic.
- For each piece of work, create a user story with a clear role, action, and benefit.
- The 'role' should be inferred from the context (e.g., 'Software Engineer', 'Data Scientist', 'End User', 'System Administrator').
- Focus on creating 3-8 meaningful user stories that cover the epic's scope.
- Each story should be independent and deliverable.
- Output ONLY a single JSON array of objects, where each object represents one user story.

EXAMPLE OUTPUT:
[
    {
        "role": "Software Engineer",
        "action": "Set up the initial CI/CD pipeline structure",
        "benefit": "we can automate testing and deployment for the project"
    },
    {
        "role": "Data Scientist",
        "action": "Develop the data cleaning and preprocessing script",
        "benefit": "the model has a high-quality dataset for training"
    }
]
"""
        try:
            epic_decomp_config = PromptTemplateConfig(
                template=epic_decomposition_prompt,
                description="Decomposes an epic into a list of user stories.",
                input_variables=[
                    InputVariable(name="epic_title", description="The title of the epic", is_required=True),
                    InputVariable(name="epic_description", description="The description of the epic", is_required=True)
                ],
                execution_settings={"default": {"max_tokens": 2000}}
            )
            
            epic_decomp_function = KernelFunction.from_prompt(
                function_name="DecomposeEpicIntoStories",
                plugin_name="GitLabIssueAgent",
                prompt=epic_decomposition_prompt,
                prompt_template_config=epic_decomp_config,
            )
            self.kernel.add_function(plugin_name="GitLabIssueAgent", function=epic_decomp_function)
            logger.info("Successfully registered epic decomposition function.")

        except Exception as e:
            logger.error(f"Failed to register epic decomposition function: {e}")

        # Epic status report generation function
        report_generation_prompt = """
Act as a senior project manager providing a clear and concise status report.
Based on the JSON data provided below, generate a formatted markdown report.

**JSON Data:**
{{$epic_data}}

---
**Report Format:**

### Epic Status Report: [Epic Title]

**Summary**
- **Total Issues:** [Total Issues]
- **Open Issues:** [Open Issues]  
- **Closed Issues:** [Closed Issues]

**Progress**
- **Completion:** [Calculate and show percentage]%
- [Create a text-based progress bar using █ and ░ characters showing completion percentage]

**Contributors**
- List all unique assignees involved in this epic (if any)

**Labels**
- List common labels used across issues (if any)

**Key Takeaway**
- Provide a brief, one-sentence summary of the epic's current state focusing on progress and next steps.

**Link:**
[View Epic on GitLab]([Epic URL])

---
**INSTRUCTIONS:**
1. Parse the JSON data carefully
2. Calculate completion percentage: (closed_issues / total_issues) * 100
3. Create progress bar: For every 10% completion, use one █ character, fill remaining with ░ (total 10 characters)
4. If no assignees or labels, state "None assigned" or "No labels"
5. Keep the key takeaway concise and actionable
6. Use the exact JSON field names provided
"""
        try:
            report_gen_config = PromptTemplateConfig(
                template=report_generation_prompt,
                description="Generates a formatted status report from epic data.",
                input_variables=[InputVariable(name="epic_data", is_required=True)],
                execution_settings={"default": {"max_tokens": 1000}}
            )
            
            report_gen_function = KernelFunction.from_prompt(
                function_name="GenerateEpicStatusReport",
                plugin_name="StatusReporting", 
                prompt=report_generation_prompt,
                prompt_template_config=report_gen_config,
            )
            self.kernel.add_function(plugin_name="StatusReporting", function=report_gen_function)
            logger.info("Successfully registered epic status report generation function.")

        except Exception as e:
            logger.error(f"Failed to register epic status report function: {e}")

    async def process_query(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process a user query with improved intent routing."""
        logger.info(f"Processing query: {query}")
        if metadata is None:
            metadata = {}
        
        # Handle GitLab Issue Agent confirmations first
        if self.issue_agent.is_awaiting_confirmation():
            return await self._handle_issue_confirmation(query)
        
        try:
            intent_context = KernelArguments(input=query)
            intent_result = await self.kernel.invoke(plugin_name="IntentRecognition", function_name="recognize_intent", arguments=intent_context)
            
            intent = "KNOWLEDGE_DISCOVERY" # Default to knowledge discovery
            try:
                intent_str = str(intent_result).strip()
                # Use regex to find a JSON object within the string, making it more robust
                json_match = re.search(r'\{.*\}', intent_str, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(0)
                    intent_data = json.loads(json_str)
                    intent = intent_data.get("intent", "KNOWLEDGE_DISCOVERY")
                
                logger.info(f"Detected intent: {intent}")

            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Error parsing intent result: {e}. Raw: '{intent_result}'. Defaulting to KNOWLEDGE_DISCOVERY.")
            
            # More robust routing logic. Default to a knowledge search for any unrecognized intent.
            if intent == "ISSUE_CREATION":
                return await self._process_issue_creation(query)
            elif intent == "CODE_GENERATION":
                return await self._process_context_aware_code_generation(query)
            elif intent == "STATUS_REPORT":
                return await self._process_status_report_request(query)
            else: # Handles KNOWLEDGE_DISCOVERY, GENERAL_QUERY, and any other case
                logger.info(f"Routing intent '{intent}' to knowledge discovery.")
                return await self._process_knowledge_discovery(query, metadata)

        except Exception as e:
            logger.error(f"An error occurred during intent processing: {str(e)}")
            logger.warning("Falling back to knowledge discovery due to the error.")
            return await self._process_knowledge_discovery(query, metadata)

    async def _handle_issue_confirmation(self, query: str) -> str:
        """Handle confirmation responses for issue creation workflows."""
        logger.info(f"Handling issue confirmation for query: {query}")
        
        if self.issue_agent.get_state() == "awaiting_batch_confirmation":
            # Handle BATCH confirmation for epic decomposition
            if "yes" in query.lower():
                drafts = self.issue_agent.get_drafts()
                if not drafts:
                    self.issue_agent.reset()
                    return "There was an error; no issue drafts were found. Please start over."

                logger.info(f"User confirmed. Creating {len(drafts)} issues via GitLab.")
                
                created_count = 0
                error_count = 0
                results = []

                for draft in drafts:
                    try:
                        # Use GitLab MCP agent or enhanced actions to create each issue
                        if self.gitlab_mcp_agent:
                            result = await self.gitlab_mcp_agent.create_issue(
                                project_id=draft["project_id"],
                                title=draft["title"],
                                description=draft["description"],
                                labels=draft.get("labels", [])
                            )
                        else:
                            # Use enhanced actions to actually create the issue in GitLab
                            story_json = json.dumps({
                                "title": draft["title"],
                                "description": draft["description"],
                                "epic_iid": draft.get("epic_id"),
                                "group_path": draft["project_id"].split("/")[0] if "/" in draft["project_id"] else "dls-404"
                            })
                            result = self.gitlab_actions.submit_user_story(
                                story_json=story_json,
                                project_id=draft["project_id"]
                            )
                            
                            # Parse result to check for errors
                            result_data = json.loads(result) if isinstance(result, str) else result
                            if "error" in result_data:
                                raise Exception(result_data["error"])
                        
                        results.append(result)
                        created_count += 1
                        logger.info(f"Successfully created issue: {draft['title']}")
                        
                    except Exception as e:
                        logger.error(f"Failed to create issue '{draft['title']}': {e}")
                        error_count += 1
                
                self.issue_agent.reset()
                
                # Generate epic link from the first draft's context
                epic_link = ""
                if drafts and "epic_id" in drafts[0]:
                    epic_id = drafts[0]["epic_id"]
                    project_id = drafts[0].get("project_id", "dls-404/DLS-404")
                    # Extract group name from project_id
                    group_name = project_id.split("/")[0] if "/" in project_id else "dls-404"
                    epic_link = f"\n\n🔗 **View Epic:** [Epic #{epic_id}](https://gitlab.com/groups/{group_name}/-/epics/{epic_id})"
                
                return f"✅ Batch creation complete!\n\n**Results:**\n- Successfully created: {created_count} issues\n- Failed to create: {error_count} issues\n\nAll user stories have been added to GitLab and linked to the epic.{epic_link}"
            
            elif "no" in query.lower():
                self.issue_agent.reset()
                return "❌ Cancelled the batch issue creation. No issues were created in GitLab."
            
            else:
                return "I am awaiting confirmation for the batch creation. Please respond with **'yes'** to proceed or **'no'** to cancel."
        
        elif self.issue_agent.get_state() == "awaiting_confirmation":
            # Handle single issue confirmation
            if "yes" in query.lower():
                draft = self.issue_agent.get_single_draft()
                if not draft:
                    self.issue_agent.reset()
                    return "There was an error; no issue draft was found. Please start over."

                try:
                    if self.gitlab_mcp_agent:
                        result = await self.gitlab_mcp_agent.create_issue(
                            project_id=draft["project_id"],
                            title=draft["title"],
                            description=draft["description"],
                            labels=draft.get("labels", [])
                        )
                    else:
                        # Use enhanced actions to actually create the issue in GitLab
                        story_json = json.dumps({
                            "title": draft["title"],
                            "description": draft["description"],
                            "epic_iid": draft.get("epic_id"),
                            "group_path": draft["project_id"].split("/")[0] if "/" in draft["project_id"] else "dls-404"
                        })
                        result = self.gitlab_actions.submit_user_story(
                            story_json=story_json,
                            project_id=draft["project_id"]
                        )
                        
                        # Parse result to check for errors
                        result_data = json.loads(result) if isinstance(result, str) else result
                        if "error" in result_data:
                            raise Exception(result_data["error"])
                    
                    self.issue_agent.reset()
                    
                    # Generate epic link if issue is linked to an epic
                    epic_link = ""
                    if "epic_id" in draft and draft["epic_id"]:
                        epic_id = draft["epic_id"]
                        project_id = draft.get("project_id", "dls-404/DLS-404")
                        group_name = project_id.split("/")[0] if "/" in project_id else "dls-404"
                        epic_link = f"\n\n🔗 **View Epic:** [Epic #{epic_id}](https://gitlab.com/groups/{group_name}/-/epics/{epic_id})"
                    
                    return f"✅ Issue created successfully!\n\n**Title:** {draft['title']}\n\nThe user story has been added to GitLab.{epic_link}"
                    
                except Exception as e:
                    logger.error(f"Failed to create single issue: {e}")
                    self.issue_agent.reset()
                    return f"❌ Failed to create the issue: {str(e)}"
            
            elif "no" in query.lower():
                self.issue_agent.reset()
                return "❌ Cancelled the issue creation. No issue was created in GitLab."
            
            else:
                return "I am awaiting confirmation for the issue creation. Please respond with **'yes'** to proceed or **'no'** to cancel."
        
        # Should not reach here
        self.issue_agent.reset()
        return "There was an error with the confirmation workflow. Please start over."

    async def _process_issue_creation(self, query: str) -> str:
        """
        Handles the start of the issue creation workflow.
        It now decides whether to create a single issue or decompose an epic.
        """
        logger.info("Processing issue creation request")
        
        # A simple regex to find an epic URL or reference
        epic_match = re.search(r'(?:epic|epics/)(?:\s*)(\d+)', query, re.IGNORECASE)
        epic_url_match = re.search(r'https://gitlab\.com/groups/[^/]+/-/epics/(\d+)', query)
        
        # A simple check to see if the user is providing story details directly
        has_story_details = "as a" in query.lower() and "i want to" in query.lower()
        
        # Check if user is asking for a specific type of story (UAT, testing, etc.)
        specific_story_type_keywords = ["uat", "testing", "test", "qa", "quality assurance", "validation", "verification"]
        has_specific_story_type = any(keyword in query.lower() for keyword in specific_story_type_keywords)

        if (epic_match or epic_url_match) and not has_story_details:
            epic_iid = int(epic_match.group(1)) if epic_match else int(epic_url_match.group(1))
            
            if has_specific_story_type:
                # --- NEW WORKFLOW: CREATE SPECIFIC STORY TYPE FOR EPIC ---
                return await self._create_specific_story_for_epic(query, epic_iid)
            else:
                # --- EXISTING WORKFLOW: DECOMPOSE EPIC ---
                return await self._decompose_epic_workflow(epic_iid)
        
        elif has_story_details:
            # --- OLD WORKFLOW: CREATE SINGLE ISSUE ---
            logger.info("Starting single issue creation flow.")
            
            # Extract user story components using regex
            story_match = re.search(
                r'as a ([^,]+),\s*i want to ([^,]+)(?:,\s*so that (.+))?', 
                query.lower()
            )
            
            if story_match:
                role = story_match.group(1).strip()
                action = story_match.group(2).strip()
                benefit = story_match.group(3).strip() if story_match.group(3) else "achieve project goals"
                
                # Default project configuration
                issue_data = {
                    "project_id": "dls-404/DLS-404",
                    "epic_id": None,
                    "user_story": {
                        "role": role.title(),
                        "action": action,
                        "benefit": benefit
                    }
                }
                
                return self.issue_agent.start_single_issue_flow(issue_data)
            else:
                return "❌ I couldn't parse the user story format. Please use the format: 'As a [role], I want to [action], so that [benefit]'"
        
        else:
            return """To create issues, please either:

1. **For Epic Decomposition:** Provide an epic reference like:
   - "Create stories for epic 42"
   - "Decompose epic https://gitlab.com/groups/dls-404/-/epics/42"

2. **For Specific Story Types:** Be specific about what you want:
   - "Create UAT testing story for epic 1"
   - "Create security testing story for epic 2"

3. **For Single Issue:** Provide a complete user story like:
   - "As a developer, I want to implement authentication, so that users can securely access the system" """

    async def _create_specific_story_for_epic(self, query: str, epic_iid: int) -> str:
        """Create a specific type of story for an epic based on the user's request."""
        logger.info(f"Creating specific story type for epic {epic_iid}")
        
        # Default group and project IDs
        group_id = "dls-404"
        project_id = "dls-404/DLS-404"
        
        try:
            # 1. Fetch Epic Details
            epic_details_str = await self.kernel.invoke(
                plugin_name="GitLabActions", 
                function_name="get_epic_details", 
                arguments=KernelArguments(group_id=group_id, epic_iid=epic_iid)
            )
            
            epic_details = json.loads(str(epic_details_str))
            if "error" in epic_details:
                return f"❌ Error retrieving epic details: {epic_details['error']}"

            logger.info(f"Retrieved epic: {epic_details['title']}")

            # 2. Create a targeted story based on the user's request
            story_type = "testing"
            if "uat" in query.lower():
                story_type = "UAT testing"
            elif "security" in query.lower():
                story_type = "security testing"
            elif "performance" in query.lower():
                story_type = "performance testing"
            elif any(word in query.lower() for word in ["qa", "quality"]):
                story_type = "quality assurance"
            
            specific_story_prompt = f"""
Create a single, specific user story for {story_type} based on this request: "{query}"

Epic context:
- Epic Title: {epic_details['title']}
- Epic Description: {epic_details['description'] or 'No description provided'}

Generate ONE user story in this exact JSON format that focuses on {story_type}:
{{
    "role": "Quality Assurance Engineer",
    "action": "design and execute {story_type} for the {epic_details['title']} functionality",
    "benefit": "ensure the {epic_details['title']} meets all acceptance criteria and quality standards"
}}

The story should be about TESTING/VALIDATING the functionality described in the epic, NOT about implementing it.
Focus on verification, validation, and quality assurance activities.
"""
            
            # Use the kernel to generate the specific story
            story_args = KernelArguments(
                epic_title=epic_details['title'], 
                epic_description=specific_story_prompt
            )
            story_result = await self.kernel.invoke(
                plugin_name="GitLabIssueAgent", 
                function_name="DecomposeEpicIntoStories", 
                arguments=story_args
            )
            
            try:
                # Parse the generated story
                story_response = str(story_result).strip()
                # Look for JSON object instead of array
                json_match = re.search(r'\{.*\}', story_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    specific_story = json.loads(json_str)
                    # Wrap in array for consistency
                    decomposed_stories = [specific_story]
                else:
                    # Fallback: try to find JSON array
                    json_match = re.search(r'\[.*\]', story_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        decomposed_stories = json.loads(json_str)
                        # Take only the first story
                        decomposed_stories = decomposed_stories[:1]
                    else:
                        raise json.JSONDecodeError("No JSON found", story_response, 0)
                        
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing specific story: {e}")
                return f"❌ I had trouble generating the specific story. Please try rephrasing your request."

            if not decomposed_stories:
                return f"❌ I couldn't generate a specific story for your request. Please try being more specific."

            # 3. Present the single story for confirmation
            epic_context = {"project_id": project_id, "epic_id": epic_iid}
            return self.issue_agent.start_epic_decomposition_flow(epic_context, decomposed_stories)
            
        except Exception as e:
            logger.error(f"Error in specific story creation: {str(e)}")
            return f"❌ I encountered an error while creating the specific story: {str(e)}"

    async def _decompose_epic_workflow(self, epic_iid: int) -> str:
        """Handle full epic decomposition workflow."""
        # Default group and project IDs - these should be configurable
        group_id = "dls-404"
        project_id = "dls-404/DLS-404"

        logger.info(f"Starting epic decomposition for epic iid: {epic_iid}")
        
        try:
            # 1. Fetch Epic Details
            epic_details_str = await self.kernel.invoke(
                plugin_name="GitLabActions", 
                function_name="get_epic_details", 
                arguments=KernelArguments(group_id=group_id, epic_iid=epic_iid)
            )
            
            epic_details = json.loads(str(epic_details_str))
            if "error" in epic_details:
                return f"❌ Error retrieving epic details: {epic_details['error']}"

            logger.info(f"Retrieved epic: {epic_details['title']}")

            # 2. Decompose Epic into Stories
            decomp_args = KernelArguments(
                epic_title=epic_details['title'], 
                epic_description=epic_details['description'] or "No description provided"
            )
            story_list_str = await self.kernel.invoke(
                plugin_name="GitLabIssueAgent", 
                function_name="DecomposeEpicIntoStories", 
                arguments=decomp_args
            )
            
            try:
                # Clean the response to extract JSON
                story_response = str(story_list_str).strip()
                json_match = re.search(r'\[.*\]', story_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    decomposed_stories = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON array found", story_response, 0)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing decomposed stories: {e}")
                return f"❌ I had trouble analyzing the epic to create stories. The AI returned an invalid format. Please try again or provide a different epic."

            if not decomposed_stories:
                return f"❌ I analyzed the epic '{epic_details['title']}' but could not identify any clear user stories to create. The epic description might need more detail."

            # 3. Hand off to the issue agent to ask for batch confirmation
            epic_context = {"project_id": project_id, "epic_id": epic_iid}
            return self.issue_agent.start_epic_decomposition_flow(epic_context, decomposed_stories)
            
        except Exception as e:
            logger.error(f"Error in epic decomposition workflow: {str(e)}")
            return f"❌ I encountered an error while processing the epic: {str(e)}"

    async def _process_knowledge_discovery(self, query: str, metadata: Dict[str, Any]) -> str:
        """Process a knowledge discovery query with a simplified and robust search."""
        logger.info(f"Processing knowledge discovery for query: {query}")
        
        if not self.search_client:
            return "Search client is not configured. Cannot perform knowledge discovery."

        try:
            embeddings_generator = EmbeddingsGenerator(
                endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            query_embedding = embeddings_generator.generate_embedding(query)
            
            logger.info("Performing hybrid search.")
            search_results = self.search_client.search(query=query, embedding=query_embedding, use_vector_search=True)

            if not search_results:
                logger.info("No results from hybrid search. Falling back to keyword-only search.")
                search_results = self.search_client.search(query=query, use_vector_search=False)
        except Exception as e:
            logger.error(f"An error occurred during search: {str(e)}")
            return f"I encountered an error while searching for information: {str(e)}"
        
        if search_results:
            formatted_results = []
            for result in search_results:
                content = result.get("content", "")
                source_name = result.get("source_name", "Unknown Source")
                file_path = result.get("path") or result.get("file_path", "Unknown Path")
                web_url = result.get("web_url") or result.get("source_uri")

                if not web_url and file_path != "Unknown Path":
                    web_url = f"https://gitlab.com/dls-404/DLS-404/-/blob/master/{file_path}"

                citation = f"[Source: {file_path or source_name}]({web_url or 'about:blank'})"
                formatted_results.append(f"{citation}\n{content}\n")
            
            context = "\n\n---\n\n".join(formatted_results)
            logger.info(f"Retrieved and formatted {len(search_results)} search results.")
        else:
            logger.info("No search results found for the query.")
            context = "No relevant information was found in the connected knowledge sources to answer your question."

        qa_context = KernelArguments(input=query, context=context)
        
        try:
            logger.info("Invoking knowledge discovery function to generate an answer.")
            answer_result = await self.kernel.invoke(
                plugin_name="KnowledgeDiscovery",
                function_name="answer_knowledge_query",
                arguments=qa_context
            )
            return str(answer_result)
        except Exception as e:
            error_str = str(e).lower()
            logger.error(f"Error invoking knowledge discovery function: {error_str}")
            if "rate limit" in error_str or "429" in error_str:
                logger.warning("Rate limiting detected. Returning formatted search results directly.")
                return (
                    "**The system is currently experiencing high demand and could not generate an AI summary.**\n\n"
                    "However, here is the relevant information retrieved directly from the knowledge base:\n\n"
                    f"---\n\n{context}"
                )
            else:
                return f"I encountered an error generating a response. Please try again. Error: {str(e)}"

    async def _process_context_aware_code_generation(self, query: str) -> str:
        """
        Performs Retrieval-Augmented Generation (RAG) for a coding request.
        1. Retrieves relevant code snippets from the search index.
        2. Passes them as context to the LLM to generate a new piece of code.
        """
        logger.info("Starting context-aware code generation workflow.")
        
        if not self.search_client:
            return "I cannot provide coding suggestions without a connection to the code search index."

        # 1. Retrieve context - Search for code relevant to the user's query
        logger.info(f"Searching for code context related to: '{query}'")
        try:
            # We specifically search for source_type 'code' to get the best context
            embeddings_generator = EmbeddingsGenerator(
                endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            query_embedding = embeddings_generator.generate_embedding(query)
            search_results = self.search_client.search(
                query=query, 
                embedding=query_embedding, 
                source_types=['code'], # Prioritize code files
                top=5, # Get the top 5 most relevant code chunks
                use_vector_search=True
            )
        except Exception as e:
            logger.error(f"Error retrieving context from search index: {e}")
            return "I encountered an error while searching for code examples in your project."

        # 2. Assemble the context
        context_string = ""
        if search_results:
            logger.info(f"Found {len(search_results)} relevant code snippets.")
            formatted_snippets = []
            for result in search_results:
                file_path = result.get('path', 'unknown_file')
                code_snippet = result.get('content', '')
                formatted_snippets.append(f"--- From file: {file_path} ---\n```\n{code_snippet}\n```")
            context_string = "\n\n".join(formatted_snippets)
        else:
            logger.info("No relevant code snippets found in the index. The model will use general best practices.")
            context_string = "No relevant code examples were found in the project."

        # 3. Generate the new code using the context
        logger.info("Invoking code generation function with retrieved context.")
        code_gen_args = KernelArguments(
            request=query,
            context=context_string
        )
        
        try:
            result = await self.kernel.invoke(
                plugin_name="CodeGeneration",
                function_name="GenerateFromContext",
                arguments=code_gen_args
            )
            return str(result)
        except Exception as e:
            logger.error(f"Error during final code generation: {e}")
            return "I failed to generate the code after retrieving context. Please try again."

    async def _process_status_report_request(self, query: str) -> str:
        """Orchestrates the fetching and generation of an epic status report."""
        logger.info(f"Processing status report request for query: {query}")
        
        # A simple regex to find an epic ID and optionally a group/project
        epic_match = re.search(r'(?:epic|epics/)\s*(\d+)', query, re.IGNORECASE)
        
        if not epic_match:
            return """To generate a status report, please provide an epic ID. 

**Examples:**
- "Status report for epic 42"
- "Generate a report for epic 1" 
- "How is epic 5 progressing?"
- "Show me the progress of epic 12"

I'll fetch the latest data from GitLab and create a comprehensive status report."""
            
        epic_iid = epic_match.group(1)
        # For simplicity, group_id is hardcoded. In a real app, this would be dynamic.
        group_id = "dls-404"
        logger.info(f"Starting status report for epic {epic_iid} in group {group_id}.")

        # Check if we have GitLab MCP agent available
        if not self.gitlab_mcp_agent:
            return "❌ GitLab MCP agent is not configured. Cannot generate status reports."

        try:
            # 1. Fetch raw data using the MCP agent
            logger.info(f"Fetching epic data for epic {epic_iid}")
            epic_data_str = self.gitlab_mcp_agent.get_epic_status_data(
                group_id=group_id, 
                epic_iid=epic_iid
            )
            
            # Parse the JSON response
            epic_data = json.loads(epic_data_str)
            if "error" in epic_data:
                return f"❌ **Error getting epic data:** {epic_data['error']}\n\nPlease check that the epic exists and you have access to it."

            # 2. Generate the report using the semantic function
            logger.info("Generating formatted status report")
            report_args = KernelArguments(epic_data=epic_data_str)
            formatted_report = await self.kernel.invoke(
                "StatusReporting", 
                "GenerateEpicStatusReport", 
                report_args
            )
            
            if not formatted_report:
                return "❌ Failed to generate the status report. Please try again."
            
            logger.info(f"Successfully generated status report for epic {epic_iid}")
            return str(formatted_report)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing epic data JSON: {str(e)}")
            return f"❌ Error parsing epic data. Please try again."
        except Exception as e:
            logger.error(f"Error generating status report for epic {epic_iid}: {str(e)}")
            return f"❌ **Error generating status report:** {str(e)}\n\nPlease check the epic ID and try again."

    async def _retrieve_status_report_data(self) -> Dict[str, Any]:
        """Retrieve status report data from the search index."""
        logger.info("Retrieving status report data from the search index.")
        
        if not self.search_client:
            return None

        try:
            # Implement the logic to retrieve status report data from the search index
            # This is a placeholder and should be replaced with the actual implementation
            # For example, you can use the search_client to search for relevant data
            # and return it as a dictionary
            return {}
        except Exception as e:
            logger.error(f"Error retrieving status report data: {str(e)}")
            return None

    async def _generate_status_report(self, data: Dict[str, Any]) -> str:
        """Generate a status report based on the retrieved data."""
        logger.info("Generating status report based on the retrieved data.")
        
        if not data:
            return "No data found to generate a status report."

        try:
            # Implement the logic to generate a status report based on the retrieved data
            # This is a placeholder and should be replaced with the actual implementation
            # For example, you can use the kernel to generate a report based on the data
            return "Status report generated successfully."
        except Exception as e:
            logger.error(f"Error generating status report: {str(e)}")
            return None