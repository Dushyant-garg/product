"""
Example usage of AWSDocumentationAnalyzer with MCP client
"""
import asyncio
from aws_documentation_analyzer import AWSDocumentationAnalyzer

# Example usage with your MCP client connection
async def analyze_aws_service_example():
    """
    Example of how to use the AWSDocumentationAnalyzer
    """
    
    # Initialize with your MCP client (replace with your actual MCP client)
    # Assuming you have already established connection to aws-documentation-mcp-server
    mcp_client = None  # Replace with your actual MCP client instance
    
    # Create the analyzer
    analyzer = AWSDocumentationAnalyzer(mcp_client=mcp_client)
    
    # Example 1: Analyze S3 security controls
    print("Analyzing S3 security controls...")
    s3_results = await analyzer.analyze_aws_service_security("S3")
    
    # Save results
    s3_file = analyzer.save_analysis_results(s3_results, "aws_analysis_output")
    print(f"S3 analysis saved to: {s3_file}")
    
    # Example 2: Analyze Lambda with custom search query
    print("\nAnalyzing Lambda security controls...")
    lambda_results = await analyzer.analyze_aws_service_security(
        "Lambda", 
        search_query="AWS Lambda security best practices IAM permissions"
    )
    
    # Save results
    lambda_file = analyzer.save_analysis_results(lambda_results, "aws_analysis_output")
    print(f"Lambda analysis saved to: {lambda_file}")
    
    # Example 3: Get quick summary
    print("\nGetting EC2 security summary...")
    ec2_summary = await analyzer.get_service_security_summary("EC2")
    print(f"EC2 Security Summary: {ec2_summary}")
    
    return s3_results, lambda_results

# Alternative example showing how to integrate with your existing workflow
class SecurityControlsExtractor:
    """
    Integration example showing how to use AWSDocumentationAnalyzer
    in your existing security controls workflow
    """
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.doc_analyzer = AWSDocumentationAnalyzer(mcp_client=mcp_client)
    
    async def extract_security_controls_for_services(self, aws_services: list) -> dict:
        """
        Extract security controls for multiple AWS services
        
        Args:
            aws_services: List of AWS service names to analyze
            
        Returns:
            Dictionary with service names as keys and security controls as values
        """
        results = {}
        
        for service in aws_services:
            print(f"Extracting security controls for {service}...")
            
            try:
                # Use the 3-agent workflow to get security controls
                analysis = await self.doc_analyzer.analyze_aws_service_security(service)
                
                # Extract just the security controls section
                security_controls = analysis.get("security_controls", "")
                
                # Store results
                results[service] = {
                    "security_controls": security_controls,
                    "source_url": analysis.get("extracted_url", ""),
                    "search_query": analysis.get("search_query", "")
                }
                
                print(f"✓ Completed analysis for {service}")
                
            except Exception as e:
                print(f"✗ Error analyzing {service}: {str(e)}")
                results[service] = {"error": str(e)}
        
        return results
    
    async def generate_compliance_report(self, aws_services: list, output_file: str = "compliance_report.md"):
        """
        Generate a comprehensive compliance report for multiple AWS services
        """
        print("Generating compliance report...")
        
        # Extract security controls for all services
        all_controls = await self.extract_security_controls_for_services(aws_services)
        
        # Generate report
        report_content = "# AWS Services Security Controls Compliance Report\n\n"
        report_content += f"**Services Analyzed:** {', '.join(aws_services)}\n\n"
        report_content += "---\n\n"
        
        for service, data in all_controls.items():
            report_content += f"## {service} Security Controls\n\n"
            
            if "error" in data:
                report_content += f"**Error:** {data['error']}\n\n"
            else:
                report_content += f"**Source:** {data.get('source_url', 'N/A')}\n\n"
                report_content += data.get('security_controls', 'No controls extracted') + "\n\n"
            
            report_content += "---\n\n"
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"Compliance report saved to: {output_file}")
        return output_file

# Usage example
async def main():
    """
    Main example showing different ways to use the analyzer
    """
    
    # Replace with your actual MCP client setup
    # mcp_client = your_mcp_client_instance
    
    # Example 1: Single service analysis
    # analyzer = AWSDocumentationAnalyzer(mcp_client=mcp_client)
    # results = await analyzer.analyze_aws_service_security("RDS")
    # print("Analysis complete!")
    
    # Example 2: Multiple services with compliance report
    # extractor = SecurityControlsExtractor(mcp_client=mcp_client)
    # services = ["S3", "EC2", "RDS", "Lambda", "IAM"]
    # await extractor.generate_compliance_report(services)
    
    print("Example usage complete. Replace mcp_client with your actual MCP client instance.")

if __name__ == "__main__":
    asyncio.run(main())
