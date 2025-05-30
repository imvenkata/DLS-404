#!/usr/bin/env python
"""
Script to fix syntax errors in the agent.py file.
"""
import os
import sys
import re

# Path to the agent.py file
AGENT_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              "rag", "agentic", "agent.py")

def fix_agent_file():
    """Fix syntax errors in the agent.py file."""
    print(f"Fixing syntax errors in {AGENT_FILE_PATH}")
    
    # Read the current content
    with open(AGENT_FILE_PATH, 'r') as f:
        content = f.read()
    
    # Make a backup of the original file
    backup_path = AGENT_FILE_PATH + ".bak"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Created backup at {backup_path}")
    
    # Fix the generate_response method
    fixed_content = fix_generate_response_method(content)
    
    # Write the fixed content back to the file
    with open(AGENT_FILE_PATH, 'w') as f:
        f.write(fixed_content)
    
    print("Syntax errors fixed successfully")

def fix_generate_response_method(content):
    """Fix the generate_response method in the agent.py file."""
    # Define the new implementation of the generate_response method
    new_method = '''    async def generate_response(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]], 
        action_results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a response based on the query, retrieved information, and action results.
        
        Args:
            query: User query string
            search_results: Retrieved documents
            action_results: Results of executed actions
            
        Returns:
            Generated response
        """
        logger.info("Generating response")
        
        # Prepare context for response generation
        context = self._prepare_context(search_results, action_results)
        
        # Create prompt for the language model
        prompt = f"""
        You are an AI assistant that helps users find information and perform actions related to GitLab and software development.
        
        USER QUERY: {query}
        
        RETRIEVED INFORMATION:
        {context.get('retrieved_info', 'No information retrieved.')}
        
        ACTIONS TAKEN:
        {context.get('actions_info', 'No actions taken.')}
        
        Based on the above information, provide a helpful response to the user query.
        If you don't have enough information, acknowledge that and suggest what might help.
        Format your response in a clear, concise manner. If the information comes from GitLab, make sure to highlight key details like status, assignees, and dates.
        """
        
        # Try different methods to generate a response
        try:
            # Last resort: try direct OpenAI API call
            try:
                from openai import AzureOpenAI
                import os
                
                # Get the base endpoint without any path components
                base_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
                # Remove trailing slash if present
                if base_endpoint and base_endpoint.endswith('/'):
                    base_endpoint = base_endpoint[:-1]
                    
                logger.info(f"Using Azure OpenAI base endpoint for chat: {base_endpoint}")
                
                # Use AzureOpenAI client which handles the URL construction correctly
                client = AzureOpenAI(
                    api_key=os.environ.get("AZURE_OPENAI_KEY"),
                    azure_endpoint=base_endpoint,
                    api_version="2023-05-15"
                )
                
                response = client.chat.completions.create(
                    model=os.environ.get("AZURE_OPENAI_COMPLETION_DEPLOYMENT"),
                    messages=[
                        {"role": "system", "content": "You are an AI assistant that helps users find information and perform actions related to GitLab and software development."},
                        {"role": "user", "content": prompt}
                    ]
                ).choices[0].message.content
                
                logger.info("Response generated using direct OpenAI API call")
                return response
            except Exception as openai_error:
                logger.warning(f"Direct OpenAI API call failed: {str(openai_error)}")
                # Fall through to final fallback
            
            # Fallback to a simple response based on retrieved information
            response = f"Based on the information I found about '{query}':\\n\\n"
            
            for i, doc in enumerate(search_results[:3]):
                content = doc.get("content", "No content available")
                source = doc.get("source_id", "Unknown source")
                response += f"Source {i+1}: {source}\\n{content}\\n\\n"
                
            if action_results:
                response += "\\nActions taken:\\n"
                for action in action_results:
                    response += f"- {action.get('action', 'Unknown action')}\\n"
            
            logger.info("Response generated using fallback method")
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"I apologize, but I encountered an error while generating a response: {str(e)}"
'''
    
    # Find the start of the generate_response method
    pattern = r'async def generate_response\('
    match = re.search(pattern, content)
    
    if not match:
        print("Could not find the generate_response method")
        return content
    
    start_pos = match.start()
    
    # Find the end of the method (start of the next method)
    next_method_pattern = r'\n    def _prepare_context\('
    next_match = re.search(next_method_pattern, content)
    
    if not next_match:
        print("Could not find the _prepare_context method")
        return content
    
    end_pos = next_match.start()
    
    # Replace the method with the new implementation
    fixed_content = content[:start_pos] + new_method + content[end_pos:]
    
    return fixed_content

if __name__ == "__main__":
    fix_agent_file()
