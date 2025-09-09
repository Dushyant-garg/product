# AWS Documentation Analyzer - AutoGen Agents

This module provides a 3-agent AutoGen system that interacts with your AWS Documentation MCP Server to extract security controls and best practices.

## Overview

The system consists of 3 specialized agents that work sequentially:

1. **DocumentSearchAgent** - Uses `search_documentation` tool to find relevant AWS documentation URLs
2. **URLSelectorAgent** - Analyzes search results and selects the most relevant URL  
3. **DocumentReaderAgent** - Uses `read_documentation` tool to extract security controls from the selected documentation

## Architecture

```
User Request → DocumentSearchAgent → URLSelectorAgent → DocumentReaderAgent → Security Controls
                      ↓                    ↓                     ↓
              search_documentation    Select Best URL    read_documentation
```

## Key Features

- **Sequential Workflow**: Agents work in a coordinated sequence, each building on the previous agent's output
- **Documentation-Only**: Agents only use actual AWS documentation content - no assumptions or hallucinations
- **Structured Output**: Organized security controls categorized by type (Access, Data Protection, etc.)
- **Flexible Queries**: Support for both auto-generated and custom search queries
- **Results Persistence**: Save analysis results to markdown files

## Setup

### Prerequisites

1. Your existing MCP client connection to `aws-documentation-mcp-server`
2. AutoGen agents installed
3. OpenAI API key configured in your settings

### Installation

```python
from aws_documentation_analyzer import AWSDocumentationAnalyzer

# Initialize with your MCP client
analyzer = AWSDocumentationAnalyzer(mcp_client=your_mcp_client)
```

## Usage Examples

### Basic Service Analysis

```python
import asyncio
from aws_documentation_analyzer import AWSDocumentationAnalyzer

async def analyze_s3_security():
    # Initialize with your MCP client
    analyzer = AWSDocumentationAnalyzer(mcp_client=mcp_client)
    
    # Analyze S3 security controls
    results = await analyzer.analyze_aws_service_security("S3")
    
    # Save results to file
    filepath = analyzer.save_analysis_results(results, "output")
    print(f"Analysis saved to: {filepath}")

asyncio.run(analyze_s3_security())
```

### Custom Search Query

```python
# Use custom search terms for more specific results
results = await analyzer.analyze_aws_service_security(
    "Lambda", 
    search_query="AWS Lambda security best practices IAM permissions encryption"
)
```

### Multiple Services Analysis

```python
from aws_doc_analyzer_example import SecurityControlsExtractor

async def analyze_multiple_services():
    extractor = SecurityControlsExtractor(mcp_client=mcp_client)
    
    services = ["S3", "EC2", "RDS", "Lambda", "IAM"]
    controls = await extractor.extract_security_controls_for_services(services)
    
    # Generate compliance report
    await extractor.generate_compliance_report(services)

asyncio.run(analyze_multiple_services())
```

## Agent Responsibilities

### DocumentSearchAgent
- **Input**: AWS service name and search query
- **Action**: Calls `search_documentation` tool via MCP server
- **Output**: List of relevant documentation URLs with descriptions
- **Focus**: Security-related documentation, best practices, compliance guides

### URLSelectorAgent  
- **Input**: Search results from DocumentSearchAgent
- **Action**: Analyzes URLs and selects the most relevant one
- **Output**: Selected URL with reasoning
- **Criteria**: Prioritizes official security docs, best practices, compliance guides

### DocumentReaderAgent
- **Input**: Selected URL from URLSelectorAgent
- **Action**: Calls `read_documentation` tool via MCP server
- **Output**: Structured security controls and requirements
- **Categories**: Access Controls, Data Protection, Network Security, Monitoring, Compliance

## Output Structure

The final output includes:

```markdown
# AWS [Service] Security Controls Analysis

## Access Controls
- Authentication requirements
- Authorization mechanisms
- IAM policies and roles

## Data Protection  
- Encryption requirements
- Data classification
- Backup and recovery

## Network Security
- VPC configurations
- Security groups
- Network ACLs

## Monitoring & Logging
- CloudTrail requirements
- Monitoring best practices
- Alerting configurations

## Compliance Controls
- Regulatory requirements
- Audit considerations
- Documentation needs

## Implementation Requirements
- Step-by-step setup
- Configuration parameters
- Validation procedures
```

## Integration with Your Existing Code

### Adding to RequirementAnalyzer

You can integrate this with your existing `RequirementAnalyzer` class:

```python
class EnhancedRequirementAnalyzer(RequirementAnalyzer):
    def __init__(self, mcp_client=None):
        super().__init__()
        self.aws_analyzer = AWSDocumentationAnalyzer(mcp_client=mcp_client)
    
    async def analyze_with_aws_security(self, document_text: str, aws_services: list):
        # Run your existing analysis
        srd_results = await self.analyze_requirements(document_text)
        
        # Add AWS security controls
        aws_controls = {}
        for service in aws_services:
            controls = await self.aws_analyzer.analyze_aws_service_security(service)
            aws_controls[service] = controls
        
        return {
            **srd_results,
            "aws_security_controls": aws_controls
        }
```

## Error Handling

The system includes comprehensive error handling:

- **MCP Connection Issues**: Graceful failure with error messages
- **Documentation Not Found**: Clear indication when documentation is unavailable  
- **Agent Communication**: Fallback mechanisms for agent coordination
- **Tool Call Failures**: Detailed error reporting for debugging

## Configuration

### System Messages

Each agent has carefully crafted system messages that:
- Define their specific role in the workflow
- Provide clear instructions for tool usage
- Ensure consistent output formatting
- Prevent assumptions and hallucinations

### Termination Conditions

- **MaxMessageTermination(6)**: Allows 2 messages per agent
- **Sequential Processing**: Each agent waits for the previous agent to complete
- **Error Recovery**: Graceful handling of failed tool calls

## Best Practices

1. **Specific Service Names**: Use exact AWS service names (e.g., "S3", "EC2", "Lambda")
2. **Targeted Queries**: Include security-focused terms in custom queries
3. **Result Validation**: Review agent outputs for completeness
4. **Regular Updates**: Re-run analysis when AWS documentation is updated
5. **Documentation Links**: Always verify the source URLs in the results

## Troubleshooting

### Common Issues

1. **MCP Client Not Connected**
   ```
   ValueError: MCP client not configured
   ```
   Solution: Ensure your MCP client is properly initialized and connected

2. **No Search Results**
   - Try broader search terms
   - Verify the AWS service name is correct
   - Check MCP server connectivity

3. **Empty Security Controls**
   - The selected documentation may not contain security information
   - Try a different search query
   - Review the selected URL for relevance

### Debug Mode

Enable debug logging to see the full agent conversation:

```python
results = await analyzer.analyze_aws_service_security("S3")
print("Full conversation:", results["full_conversation"])
```

## Contributing

When extending this system:
1. Maintain the sequential agent workflow
2. Ensure agents only use actual documentation content
3. Follow the established output formatting
4. Add comprehensive error handling
5. Update system messages for clarity

## License

This module follows the same license as your main project.
