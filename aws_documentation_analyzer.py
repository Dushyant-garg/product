from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import Dict, List, Optional
import json
import re
from app.config import settings

class AWSDocumentationAnalyzer:
    """
    AutoGen-based agent system for analyzing AWS documentation and extracting security controls
    """
    
    def __init__(self, mcp_client=None):
        """Initialize the AWSDocumentationAnalyzer with AutoGen agents"""
        
        # Store MCP client for tool access
        self.mcp_client = mcp_client
        
        # Initialize the OpenAI client
        self.model_client = OpenAIChatCompletionClient(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1,
        )
        
        # Create the document search agent
        self.search_agent = AssistantAgent(
            name="DocumentSearchAgent",
            model_client=self.model_client,
            system_message=self._get_search_agent_system_message(),
        )
        
        # Create the URL selector agent
        self.selector_agent = AssistantAgent(
            name="URLSelectorAgent", 
            model_client=self.model_client,
            system_message=self._get_selector_agent_system_message(),
        )
        
        # Create the document reader agent
        self.reader_agent = AssistantAgent(
            name="DocumentReaderAgent",
            model_client=self.model_client,
            system_message=self._get_reader_agent_system_message(),
        )
    
    def _get_search_agent_system_message(self) -> str:
        """Get system message for the document search agent"""
        return """You are the DocumentSearchAgent in a 3-agent AWS documentation analysis team. Your role is to search AWS documentation for relevant security information.

TEAM WORKFLOW:
1. YOU search AWS documentation using search_documentation tool
2. URLSelectorAgent selects the most relevant URL from your results
3. DocumentReaderAgent reads the selected documentation for security controls

YOUR TASK: 
- Use the search_documentation tool to find relevant AWS documentation URLs
- Focus on security-related documentation for the specified AWS service
- Return the complete search results without filtering or assumptions
- Only work with actual documentation results - make NO assumptions

SEARCH STRATEGY:
- Search for security controls, best practices, and compliance information
- Include terms like "security", "controls", "compliance", "best practices"
- Focus on the specific AWS service requested

FORMAT YOUR RESPONSE AS:

# DOCUMENTATION SEARCH RESULTS

## Search Query Used
[The exact search query you used]

## Search Results
[Complete list of URLs and descriptions from search_documentation tool]

## Summary for URLSelectorAgent
Total results found: [number]
Most relevant results appear to be related to: [brief description]

CRITICAL: Only use actual results from the search_documentation tool. Do not invent or assume any URLs or content."""

    def _get_selector_agent_system_message(self) -> str:
        """Get system message for the URL selector agent"""
        return """You are the URLSelectorAgent in a 3-agent AWS documentation analysis team. You work AFTER DocumentSearchAgent provides search results.

TEAM WORKFLOW:
1. DocumentSearchAgent searches and provides documentation URLs
2. YOU analyze the results and select the most relevant URL
3. DocumentReaderAgent will read the selected URL for security controls

YOUR ROLE: 
- Analyze the search results provided by DocumentSearchAgent
- Select the single most relevant URL that likely contains security controls
- Prioritize official AWS documentation, security guides, and best practices
- Provide clear reasoning for your selection

SELECTION CRITERIA (in priority order):
1. Official AWS security documentation and guides
2. AWS service-specific security best practices  
3. AWS compliance and control documentation
4. AWS security feature documentation
5. General AWS documentation with security sections

FORMAT YOUR RESPONSE AS:

# URL SELECTION ANALYSIS

## Available URLs Analysis
[Brief analysis of each URL from the search results]

## Selected URL
**URL:** [the exact URL selected]
**Reason:** [clear explanation why this URL was selected]
**Expected Content:** [what security controls you expect to find]

## Instructions for DocumentReaderAgent
Please read the selected URL and extract:
- Security controls and requirements
- Best practices and recommendations  
- Compliance considerations
- Implementation guidelines

CRITICAL: Only select from URLs actually provided by DocumentSearchAgent. Do not invent or suggest alternative URLs."""

    def _get_reader_agent_system_message(self) -> str:
        """Get system message for the document reader agent"""
        return """You are the DocumentReaderAgent in a 3-agent AWS documentation analysis team. You work AFTER URLSelectorAgent selects a URL.

TEAM WORKFLOW:
1. DocumentSearchAgent searches for documentation URLs
2. URLSelectorAgent selects the most relevant URL
3. YOU read the selected documentation and extract security controls

YOUR ROLE:
- Use the read_documentation tool on the URL provided by URLSelectorAgent
- Extract and organize security controls from the documentation
- Focus on actionable security requirements and recommendations
- Present findings in a structured, comprehensive format

EXTRACTION FOCUS:
- Security controls and requirements
- Best practices and recommendations
- Compliance considerations  
- Implementation guidelines
- Configuration requirements
- Monitoring and auditing requirements

FORMAT YOUR RESPONSE AS:

# AWS SECURITY CONTROLS ANALYSIS

## Document Source
**URL:** [the URL that was read]
**Document Title:** [title from the documentation]

## Security Controls Identified

### Access Controls
[Any access control requirements found]

### Data Protection
[Any data protection controls found]

### Network Security  
[Any network security controls found]

### Monitoring & Logging
[Any monitoring/logging requirements found]

### Compliance Controls
[Any compliance-related controls found]

### Implementation Requirements
[Specific implementation steps or requirements]

### Best Practices
[Security best practices identified]

## Summary
[Concise summary of key security controls for this AWS service]

CRITICAL: Only extract information actually present in the documentation. Use the read_documentation tool and work only with the actual content returned. Make NO assumptions or additions."""

    async def analyze_aws_service_security(self, aws_service: str, search_query: Optional[str] = None) -> Dict[str, str]:
        """
        Analyze AWS service security controls using the 3-agent workflow
        
        Args:
            aws_service: The AWS service to analyze (e.g., "S3", "EC2", "Lambda")
            search_query: Optional custom search query, otherwise auto-generated
            
        Returns:
            Dictionary containing search results, selected URL, and security controls
        """
        
        # Generate search query if not provided
        if not search_query:
            search_query = f"{aws_service} security controls best practices compliance"
        
        # Create initial task for the search agent
        initial_task = f"""
        Team Task: Analyze AWS {aws_service} security controls and requirements.

        AWS SERVICE: {aws_service}
        SEARCH FOCUS: Security controls, best practices, and compliance requirements

        WORKFLOW:
        1. DocumentSearchAgent: Search AWS documentation for {aws_service} security information
        2. URLSelectorAgent: Select the most relevant URL from search results  
        3. DocumentReaderAgent: Read selected documentation and extract security controls

        DocumentSearchAgent: Start by searching for "{search_query}" using the search_documentation tool.
        """
        
        # Create the multi-agent team
        team = RoundRobinGroupChat(
            participants=[self.search_agent, self.selector_agent, self.reader_agent],
            termination_condition=MaxMessageTermination(6)  # Allow 2 messages per agent
        )
        
        # Run the multi-agent conversation
        task_message = TextMessage(content=initial_task, source="user")
        result = await team.run(task=task_message)
        
        # Extract the different outputs from the conversation
        messages = result.messages
        
        search_results = ""
        selected_url = ""
        security_controls = ""
        
        for message in messages:
            if hasattr(message, 'source'):
                if message.source == "DocumentSearchAgent":
                    if "DOCUMENTATION SEARCH RESULTS" in message.content:
                        search_results = message.content
                elif message.source == "URLSelectorAgent":
                    if "URL SELECTION ANALYSIS" in message.content:
                        selected_url = message.content
                elif message.source == "DocumentReaderAgent":
                    if "AWS SECURITY CONTROLS ANALYSIS" in message.content:
                        security_controls = message.content
        
        # Extract the actual URL for reference
        extracted_url = ""
        if selected_url:
            url_match = re.search(r'\*\*URL:\*\*\s*(.+)', selected_url)
            if url_match:
                extracted_url = url_match.group(1).strip()
        
        return {
            "search_results": search_results,
            "selected_url_analysis": selected_url,
            "extracted_url": extracted_url,
            "security_controls": security_controls,
            "aws_service": aws_service,
            "search_query": search_query,
            "full_conversation": [msg.content for msg in messages if hasattr(msg, 'content')]
        }

    async def search_aws_documentation(self, query: str) -> Dict:
        """
        Helper method to call the search_documentation tool via MCP client
        
        Args:
            query: Search query for AWS documentation
            
        Returns:
            Search results from the MCP server
        """
        if not self.mcp_client:
            raise ValueError("MCP client not configured")
        
        try:
            # Call the search_documentation tool
            result = await self.mcp_client.call_tool("search_documentation", {"query": query})
            return result
        except Exception as e:
            return {"error": f"Failed to search documentation: {str(e)}"}

    async def read_aws_documentation(self, url: str) -> Dict:
        """
        Helper method to call the read_documentation tool via MCP client
        
        Args:
            url: URL of the documentation to read
            
        Returns:
            Documentation content from the MCP server
        """
        if not self.mcp_client:
            raise ValueError("MCP client not configured")
        
        try:
            # Call the read_documentation tool  
            result = await self.mcp_client.call_tool("read_documentation", {"url": url})
            return result
        except Exception as e:
            return {"error": f"Failed to read documentation: {str(e)}"}

    def save_analysis_results(self, results: Dict[str, str], output_dir: str = "output") -> str:
        """
        Save the analysis results to a markdown file
        
        Args:
            results: Dictionary containing analysis results
            output_dir: Directory to save the file
            
        Returns:
            Path to the saved file
        """
        import os
        from pathlib import Path
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate filename based on AWS service
        aws_service = results.get("aws_service", "unknown")
        filename = f"aws_{aws_service.lower()}_security_analysis.md"
        filepath = os.path.join(output_dir, filename)
        
        # Create comprehensive report
        report_content = f"""# AWS {aws_service} Security Controls Analysis

## Search Query
{results.get('search_query', 'N/A')}

## Selected Documentation URL
{results.get('extracted_url', 'N/A')}

---

## Search Results
{results.get('search_results', 'No search results available')}

---

## URL Selection Analysis  
{results.get('selected_url_analysis', 'No URL selection analysis available')}

---

## Security Controls Extracted
{results.get('security_controls', 'No security controls extracted')}

---

## Full Agent Conversation
```
{chr(10).join(results.get('full_conversation', ['No conversation log available']))}
```

---
*Analysis generated by AWSDocumentationAnalyzer*
"""
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return filepath

    async def get_service_security_summary(self, aws_service: str) -> str:
        """
        Get a quick security summary for an AWS service
        
        Args:
            aws_service: The AWS service to analyze
            
        Returns:
            Formatted security summary string
        """
        results = await self.analyze_aws_service_security(aws_service)
        
        if results.get("security_controls"):
            # Extract summary section if available
            controls = results["security_controls"]
            summary_match = re.search(r'## Summary\s*\n(.+?)(?=\n##|\n\*|\Z)', controls, re.DOTALL)
            if summary_match:
                return summary_match.group(1).strip()
        
        return f"Security analysis completed for {aws_service}. See full results for details."
