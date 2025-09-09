from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import Dict, List, Optional
import json
import re
import csv
import io
from app.config import settings

class AWSDocumentationAnalyzer:
    """
    AutoGen-based agent system for analyzing AWS documentation and extracting structured security controls
    Now includes 5 agents: Search -> Selector -> Reader -> Processor -> Validator
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
        
        # Create the security controls processor agent
        self.processor_agent = AssistantAgent(
            name="SecurityControlsProcessor",
            model_client=self.model_client,
            system_message=self._get_processor_agent_system_message(),
        )
        
        # Create the CSV validator agent
        self.validator_agent = AssistantAgent(
            name="CSVValidator",
            model_client=self.model_client,
            system_message=self._get_validator_agent_system_message(),
        )
    
    def _get_search_agent_system_message(self) -> str:
        """Get system message for the document search agent"""
        return """You are the DocumentSearchAgent in a 5-agent AWS documentation analysis team. Your role is to search AWS documentation for relevant security information.

TEAM WORKFLOW:
1. YOU search AWS documentation using search_documentation tool
2. URLSelectorAgent selects the most relevant URL from your results
3. DocumentReaderAgent reads the selected documentation for security controls
4. SecurityControlsProcessor structures the controls into CSV format
5. CSVValidator validates the final CSV output

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
        return """You are the URLSelectorAgent in a 5-agent AWS documentation analysis team. You work AFTER DocumentSearchAgent provides search results.

TEAM WORKFLOW:
1. DocumentSearchAgent searches and provides documentation URLs
2. YOU analyze the results and select the most relevant URL
3. DocumentReaderAgent will read the selected URL for security controls
4. SecurityControlsProcessor structures the controls into CSV format
5. CSVValidator validates the final CSV output

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
        return """You are the DocumentReaderAgent in a 5-agent AWS documentation analysis team. You work AFTER URLSelectorAgent selects a URL.

TEAM WORKFLOW:
1. DocumentSearchAgent searches for documentation URLs
2. URLSelectorAgent selects the most relevant URL
3. YOU read the selected documentation and extract security controls
4. SecurityControlsProcessor will structure your findings into CSV format
5. CSVValidator will validate the final CSV output

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

    def _get_processor_agent_system_message(self) -> str:
        """Get system message for the security controls processor agent"""
        return """You are the SecurityControlsProcessor in a 5-agent AWS documentation analysis team. You work AFTER DocumentReaderAgent extracts security controls.

TEAM WORKFLOW:
1. DocumentSearchAgent searches for documentation URLs
2. URLSelectorAgent selects the most relevant URL
3. DocumentReaderAgent reads and extracts security controls
4. YOU process and structure the controls into CSV format
5. CSVValidator will validate your CSV output

YOUR ROLE:
- Take the unstructured security controls from DocumentReaderAgent
- Extract and structure each control with required fields
- Generate a properly formatted CSV with specific columns
- Ensure each security control has all required data fields

REQUIRED CSV COLUMNS:
- controlId: Unique identifier for the control (generate if not provided)
- controlName: Descriptive name of the security control
- severity: Risk level (Critical, High, Medium, Low)
- policies: Related policies or frameworks
- awsConfig: AWS configuration requirements
- implementation: Implementation steps or requirements
- relatedRequirements: Related compliance or security requirements

FORMAT YOUR RESPONSE AS:

# STRUCTURED SECURITY CONTROLS

## Processing Summary
Total controls processed: [number]
CSV format validation: [status]

## CSV Output
```csv
controlId,controlName,severity,policies,awsConfig,implementation,relatedRequirements
[CSV data rows]
```

PROCESSING RULES:
1. Extract distinct security controls from the documentation content
2. Generate unique controlId if not explicitly provided (format: AWS-{SERVICE}-{NUMBER})
3. Determine severity based on security impact (Critical for data breaches, High for access controls, etc.)
4. Map AWS configuration details from implementation sections
5. Include all relevant compliance frameworks mentioned
6. Ensure no empty cells - use "Not specified" if information is unavailable

CRITICAL: Only use information actually extracted by DocumentReaderAgent. Do not add information not present in the documentation."""

    def _get_validator_agent_system_message(self) -> str:
        """Get system message for the CSV validator agent"""
        return """You are the CSVValidator in a 5-agent AWS documentation analysis team. You work AFTER SecurityControlsProcessor creates CSV output.

TEAM WORKFLOW:
1. DocumentSearchAgent searches for documentation URLs
2. URLSelectorAgent selects the most relevant URL  
3. DocumentReaderAgent reads and extracts security controls
4. SecurityControlsProcessor structures controls into CSV format
5. YOU validate the CSV format and data quality

YOUR ROLE:
- Validate the CSV format from SecurityControlsProcessor
- Check data integrity and completeness
- Verify required columns are present
- Ensure proper CSV formatting
- Report any issues and provide corrected version if needed

VALIDATION CRITERIA:
1. **Format Validation:**
   - Proper CSV syntax (commas, quotes, escaping)
   - Consistent column count across all rows
   - Valid header row with required columns

2. **Required Columns Check:**
   - controlId (must be unique)
   - controlName (must not be empty)
   - severity (must be: Critical, High, Medium, Low)
   - policies (can be "Not specified")
   - awsConfig (can be "Not specified")
   - implementation (can be "Not specified")
   - relatedRequirements (can be "Not specified")

3. **Data Quality Validation:**
   - No completely empty rows
   - controlId uniqueness
   - Severity values from allowed list
   - Reasonable length limits for text fields

FORMAT YOUR RESPONSE AS:

# CSV VALIDATION REPORT

## Validation Status
**Overall Status:** [PASSED/FAILED]
**Total Rows Validated:** [number]
**Issues Found:** [number]

## Validation Details

### Format Validation
- CSV Syntax: [PASSED/FAILED]
- Column Count: [PASSED/FAILED]
- Header Row: [PASSED/FAILED]

### Required Columns
- controlId: [PASSED/FAILED]
- controlName: [PASSED/FAILED]  
- severity: [PASSED/FAILED]
- policies: [PASSED/FAILED]
- awsConfig: [PASSED/FAILED]
- implementation: [PASSED/FAILED]
- relatedRequirements: [PASSED/FAILED]

### Data Quality
- Unique Control IDs: [PASSED/FAILED]
- Valid Severity Values: [PASSED/FAILED]
- No Empty Required Fields: [PASSED/FAILED]

## Issues Found
[List any specific issues with row numbers and descriptions]

## Corrected CSV (if needed)
```csv
[Provide corrected CSV only if validation failed]
```

## Final Validated CSV
```csv
[Provide the final validated CSV that passed all checks]
```

CRITICAL: Only validate the actual CSV provided by SecurityControlsProcessor. Provide specific, actionable feedback for any issues found."""

    async def analyze_aws_service_security(self, aws_service: str, search_query: Optional[str] = None) -> Dict[str, str]:
        """
        Analyze AWS service security controls using the 5-agent workflow
        
        Args:
            aws_service: The AWS service to analyze (e.g., "S3", "EC2", "Lambda")
            search_query: Optional custom search query, otherwise auto-generated
            
        Returns:
            Dictionary containing all agent outputs including validated CSV
        """
        
        # Generate search query if not provided
        if not search_query:
            search_query = f"{aws_service} security controls best practices compliance"
        
        # Create initial task for the search agent
        initial_task = f"""
        Team Task: Analyze AWS {aws_service} security controls and generate structured CSV output.

        AWS SERVICE: {aws_service}
        SEARCH FOCUS: Security controls, best practices, and compliance requirements

        COMPLETE WORKFLOW:
        1. DocumentSearchAgent: Search AWS documentation for {aws_service} security information
        2. URLSelectorAgent: Select the most relevant URL from search results  
        3. DocumentReaderAgent: Read selected documentation and extract security controls
        4. SecurityControlsProcessor: Structure the controls into CSV format with required fields
        5. CSVValidator: Validate the CSV format and data quality

        FINAL OUTPUT REQUIRED:
        - Validated CSV with columns: controlId, controlName, severity, policies, awsConfig, implementation, relatedRequirements

        DocumentSearchAgent: Start by searching for "{search_query}" using the search_documentation tool.
        """
        
        # Create the multi-agent team with all 5 agents
        team = RoundRobinGroupChat(
            participants=[
                self.search_agent, 
                self.selector_agent, 
                self.reader_agent,
                self.processor_agent,
                self.validator_agent
            ],
            termination_condition=MaxMessageTermination(10)  # Allow 2 messages per agent
        )
        
        # Run the multi-agent conversation
        task_message = TextMessage(content=initial_task, source="user")
        result = await team.run(task=task_message)
        
        # Extract the different outputs from the conversation
        messages = result.messages
        
        search_results = ""
        selected_url = ""
        security_controls = ""
        processed_controls = ""
        validation_report = ""
        final_csv = ""
        
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
                elif message.source == "SecurityControlsProcessor":
                    if "STRUCTURED SECURITY CONTROLS" in message.content:
                        processed_controls = message.content
                elif message.source == "CSVValidator":
                    if "CSV VALIDATION REPORT" in message.content:
                        validation_report = message.content
        
        # Extract the actual URL for reference
        extracted_url = ""
        if selected_url:
            url_match = re.search(r'\*\*URL:\*\*\s*(.+)', selected_url)
            if url_match:
                extracted_url = url_match.group(1).strip()
        
        # Extract final CSV from validation report
        if validation_report:
            # Look for final validated CSV
            csv_match = re.search(r'## Final Validated CSV\s*```csv\s*(.+?)```', validation_report, re.DOTALL)
            if csv_match:
                final_csv = csv_match.group(1).strip()
        
        return {
            "search_results": search_results,
            "selected_url_analysis": selected_url,
            "extracted_url": extracted_url,
            "security_controls": security_controls,
            "processed_controls": processed_controls,
            "validation_report": validation_report,
            "final_csv": final_csv,
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
        Save the comprehensive analysis results to a markdown file
        
        Args:
            results: Dictionary containing analysis results from 5-agent workflow
            output_dir: Directory to save the file
            
        Returns:
            Path to the saved markdown file
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

## Executive Summary
**Service Analyzed:** {aws_service}
**Search Query:** {results.get('search_query', 'N/A')}
**Documentation Source:** {results.get('extracted_url', 'N/A')}
**CSV Records Generated:** {len(results.get('final_csv', '').split('\n')) - 1 if results.get('final_csv') else 0}

---

## 1. Documentation Search Results
{results.get('search_results', 'No search results available')}

---

## 2. URL Selection Analysis  
{results.get('selected_url_analysis', 'No URL selection analysis available')}

---

## 3. Security Controls Extracted
{results.get('security_controls', 'No security controls extracted')}

---

## 4. Structured Security Controls
{results.get('processed_controls', 'No processed controls available')}

---

## 5. CSV Validation Report
{results.get('validation_report', 'No validation report available')}

---

## 6. Final CSV Output

### CSV Data
```csv
{results.get('final_csv', 'No validated CSV available')}
```

### CSV Summary
- **Format:** Comma-separated values
- **Columns:** controlId, controlName, severity, policies, awsConfig, implementation, relatedRequirements
- **Purpose:** Structured security controls for compliance and implementation tracking

---

## 7. Complete Agent Workflow Log

### Agent Interaction Summary
1. **DocumentSearchAgent** → Found documentation URLs
2. **URLSelectorAgent** → Selected most relevant URL
3. **DocumentReaderAgent** → Extracted security controls
4. **SecurityControlsProcessor** → Structured data into CSV format
5. **CSVValidator** → Validated format and data quality

### Full Conversation Log
```
{chr(10).join(results.get('full_conversation', ['No conversation log available']))}
```

---

## 8. Usage Instructions

### Import CSV Data
The generated CSV can be imported into:
- Compliance management systems
- Risk assessment tools
- Security frameworks (SOC2, ISO27001, etc.)
- Project management tools

### Implementation Tracking
Use the CSV to:
1. Track implementation status of each control
2. Assign ownership and due dates
3. Monitor compliance gaps
4. Generate compliance reports

---
*Analysis generated by AWSDocumentationAnalyzer - 5 Agent Workflow*
*Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
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

    def save_csv_results(self, results: Dict[str, str], output_dir: str = "output") -> str:
        """
        Save the validated CSV results to a CSV file
        
        Args:
            results: Dictionary containing analysis results with final_csv
            output_dir: Directory to save the file
            
        Returns:
            Path to the saved CSV file
        """
        import os
        from pathlib import Path
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate filename based on AWS service
        aws_service = results.get("aws_service", "unknown")
        filename = f"aws_{aws_service.lower()}_security_controls.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Get the final CSV content
        csv_content = results.get("final_csv", "")
        
        if not csv_content:
            # Fallback: create basic CSV structure if no validated CSV available
            csv_content = "controlId,controlName,severity,policies,awsConfig,implementation,relatedRequirements\n"
            csv_content += f"AWS-{aws_service.upper()}-001,No security controls extracted,Medium,Not specified,Not specified,Review documentation manually,Check {results.get('extracted_url', 'AWS documentation')}"
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_content)
        
        return filepath

    def validate_csv_format(self, csv_content: str) -> Dict[str, any]:
        """
        Validate CSV format programmatically
        
        Args:
            csv_content: The CSV content as string
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "is_valid": True,
            "issues": [],
            "row_count": 0,
            "column_count": 0,
            "required_columns": ["controlId", "controlName", "severity", "policies", "awsConfig", "implementation", "relatedRequirements"]
        }
        
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            headers = csv_reader.fieldnames
            
            # Check required columns
            if not headers:
                validation_results["is_valid"] = False
                validation_results["issues"].append("No headers found in CSV")
                return validation_results
            
            missing_columns = set(validation_results["required_columns"]) - set(headers)
            if missing_columns:
                validation_results["is_valid"] = False
                validation_results["issues"].append(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Count columns
            validation_results["column_count"] = len(headers)
            
            # Validate rows
            control_ids = set()
            row_num = 1
            
            for row in csv_reader:
                row_num += 1
                validation_results["row_count"] += 1
                
                # Check for empty required fields
                if not row.get("controlId", "").strip():
                    validation_results["is_valid"] = False
                    validation_results["issues"].append(f"Row {row_num}: Empty controlId")
                
                if not row.get("controlName", "").strip():
                    validation_results["is_valid"] = False
                    validation_results["issues"].append(f"Row {row_num}: Empty controlName")
                
                # Check duplicate control IDs
                control_id = row.get("controlId", "").strip()
                if control_id in control_ids:
                    validation_results["is_valid"] = False
                    validation_results["issues"].append(f"Row {row_num}: Duplicate controlId '{control_id}'")
                else:
                    control_ids.add(control_id)
                
                # Check severity values
                severity = row.get("severity", "").strip()
                if severity and severity not in ["Critical", "High", "Medium", "Low"]:
                    validation_results["is_valid"] = False
                    validation_results["issues"].append(f"Row {row_num}: Invalid severity '{severity}'. Must be Critical, High, Medium, or Low")
        
        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["issues"].append(f"CSV parsing error: {str(e)}")
        
        return validation_results

    def extract_csv_from_text(self, text: str) -> str:
        """
        Extract CSV content from text that may contain markdown formatting
        
        Args:
            text: Text content that may contain CSV within markdown code blocks
            
        Returns:
            Extracted CSV content as string
        """
        # Look for CSV content in markdown code blocks
        csv_patterns = [
            r'```csv\s*(.+?)```',
            r'```\s*(.+?)```',
            r'CSV Output[:\s]*(.+?)(?=\n##|\n\*|\Z)',
            r'Final Validated CSV[:\s]*```csv\s*(.+?)```'
        ]
        
        for pattern in csv_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                csv_content = match.group(1).strip()
                # Basic validation that it looks like CSV
                if ',' in csv_content and '\n' in csv_content:
                    return csv_content
        
        return ""

    async def analyze_and_save_all(self, aws_service: str, search_query: Optional[str] = None, output_dir: str = "output") -> Dict[str, str]:
        """
        Complete workflow: analyze AWS service and save both CSV and markdown results
        
        Args:
            aws_service: The AWS service to analyze
            search_query: Optional custom search query
            output_dir: Directory to save files
            
        Returns:
            Dictionary with analysis results and file paths
        """
        # Run the complete 5-agent analysis
        results = await self.analyze_aws_service_security(aws_service, search_query)
        
        # Save markdown analysis
        markdown_path = self.save_analysis_results(results, output_dir)
        
        # Save CSV file
        csv_path = self.save_csv_results(results, output_dir)
        
        # Add file paths to results
        results["markdown_file"] = markdown_path
        results["csv_file"] = csv_path
        
        # Validate the final CSV
        if results.get("final_csv"):
            validation = self.validate_csv_format(results["final_csv"])
            results["csv_validation"] = validation
        
        return results
