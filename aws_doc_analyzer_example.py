"""
Example usage of AWSDocumentationAnalyzer with MCP client - 5 Agent Workflow
"""
import asyncio
from aws_documentation_analyzer import AWSDocumentationAnalyzer

# Example usage with your MCP client connection
async def analyze_aws_service_example():
    """
    Example of how to use the enhanced AWSDocumentationAnalyzer with 5 agents
    """
    
    # Initialize with your MCP client (replace with your actual MCP client)
    # Assuming you have already established connection to aws-documentation-mcp-server
    mcp_client = None  # Replace with your actual MCP client instance
    
    # Create the analyzer
    analyzer = AWSDocumentationAnalyzer(mcp_client=mcp_client)
    
    # Example 1: Complete S3 analysis with CSV output
    print("Analyzing S3 security controls with 5-agent workflow...")
    s3_results = await analyzer.analyze_and_save_all("S3", output_dir="aws_analysis_output")
    
    print(f"S3 analysis complete!")
    print(f"  - Markdown report: {s3_results.get('markdown_file')}")
    print(f"  - CSV file: {s3_results.get('csv_file')}")
    print(f"  - CSV validation: {'PASSED' if s3_results.get('csv_validation', {}).get('is_valid') else 'FAILED'}")
    
    # Example 2: Lambda with custom search query and manual saves
    print("\nAnalyzing Lambda security controls...")
    lambda_results = await analyzer.analyze_aws_service_security(
        "Lambda", 
        search_query="AWS Lambda security best practices IAM permissions encryption"
    )
    
    # Save both formats manually
    markdown_path = analyzer.save_analysis_results(lambda_results, "aws_analysis_output")
    csv_path = analyzer.save_csv_results(lambda_results, "aws_analysis_output")
    
    print(f"Lambda analysis saved:")
    print(f"  - Markdown: {markdown_path}")
    print(f"  - CSV: {csv_path}")
    
    # Display CSV validation results
    if lambda_results.get("final_csv"):
        validation = analyzer.validate_csv_format(lambda_results["final_csv"])
        print(f"  - CSV validation: {'PASSED' if validation['is_valid'] else 'FAILED'}")
        if not validation['is_valid']:
            print(f"    Issues: {validation['issues']}")
    
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
        Extract security controls for multiple AWS services with CSV output
        
        Args:
            aws_services: List of AWS service names to analyze
            
        Returns:
            Dictionary with service names as keys and comprehensive analysis results
        """
        results = {}
        
        for service in aws_services:
            print(f"Extracting security controls for {service}...")
            
            try:
                # Use the 5-agent workflow to get structured security controls
                analysis = await self.doc_analyzer.analyze_aws_service_security(service)
                
                # Store comprehensive results
                results[service] = {
                    "security_controls": analysis.get("security_controls", ""),
                    "processed_controls": analysis.get("processed_controls", ""),
                    "validation_report": analysis.get("validation_report", ""),
                    "final_csv": analysis.get("final_csv", ""),
                    "source_url": analysis.get("extracted_url", ""),
                    "search_query": analysis.get("search_query", "")
                }
                
                # Validate CSV if available
                if analysis.get("final_csv"):
                    validation = self.doc_analyzer.validate_csv_format(analysis["final_csv"])
                    results[service]["csv_validation"] = validation
                    validation_status = "PASSED" if validation["is_valid"] else "FAILED"
                    print(f"✓ Completed analysis for {service} - CSV validation: {validation_status}")
                else:
                    print(f"✓ Completed analysis for {service} - No CSV generated")
                
            except Exception as e:
                print(f"✗ Error analyzing {service}: {str(e)}")
                results[service] = {"error": str(e)}
        
        return results
    
    async def generate_compliance_report(self, aws_services: list, output_file: str = "compliance_report.md"):
        """
        Generate a comprehensive compliance report for multiple AWS services with CSV outputs
        """
        print("Generating compliance report...")
        
        # Extract security controls for all services
        all_controls = await self.extract_security_controls_for_services(aws_services)
        
        # Generate markdown report
        report_content = "# AWS Services Security Controls Compliance Report\n\n"
        report_content += f"**Services Analyzed:** {', '.join(aws_services)}\n\n"
        
        # Summary statistics
        total_services = len(aws_services)
        successful_analyses = len([s for s, data in all_controls.items() if "error" not in data])
        csv_generated = len([s for s, data in all_controls.items() if data.get("final_csv")])
        
        report_content += f"**Analysis Summary:**\n"
        report_content += f"- Total Services: {total_services}\n"
        report_content += f"- Successful Analyses: {successful_analyses}\n"
        report_content += f"- CSV Files Generated: {csv_generated}\n\n"
        report_content += "---\n\n"
        
        # Create master CSV content
        master_csv_content = "controlId,controlName,severity,policies,awsConfig,implementation,relatedRequirements,awsService\n"
        
        for service, data in all_controls.items():
            report_content += f"## {service} Security Controls\n\n"
            
            if "error" in data:
                report_content += f"**Error:** {data['error']}\n\n"
            else:
                report_content += f"**Source:** {data.get('source_url', 'N/A')}\n\n"
                
                # Add CSV validation status
                if data.get("csv_validation"):
                    validation = data["csv_validation"]
                    status = "✅ PASSED" if validation["is_valid"] else "❌ FAILED"
                    report_content += f"**CSV Validation:** {status}\n"
                    if not validation["is_valid"]:
                        report_content += f"**Issues:** {', '.join(validation['issues'])}\n"
                    report_content += f"**CSV Records:** {validation.get('row_count', 0)}\n\n"
                
                # Add structured controls
                if data.get("processed_controls"):
                    report_content += "### Structured Controls\n"
                    report_content += data.get('processed_controls', 'No processed controls') + "\n\n"
                
                # Add to master CSV
                if data.get("final_csv"):
                    csv_lines = data["final_csv"].strip().split('\n')
                    if len(csv_lines) > 1:  # Skip header
                        for line in csv_lines[1:]:
                            if line.strip():
                                master_csv_content += f"{line},{service}\n"
                
                # Add raw security controls
                report_content += "### Raw Security Controls\n"
                report_content += data.get('security_controls', 'No controls extracted') + "\n\n"
            
            report_content += "---\n\n"
        
        # Add master CSV section to report
        report_content += "## Master CSV Data\n\n"
        report_content += "Combined CSV data from all services:\n\n"
        report_content += "```csv\n"
        report_content += master_csv_content
        report_content += "```\n\n"
        
        # Save markdown report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Save master CSV file
        csv_output_file = output_file.replace('.md', '_master.csv')
        with open(csv_output_file, 'w', encoding='utf-8', newline='') as f:
            f.write(master_csv_content)
        
        print(f"Compliance report saved to: {output_file}")
        print(f"Master CSV saved to: {csv_output_file}")
        return output_file, csv_output_file

# Enhanced Usage Examples
async def main():
    """
    Main example showing different ways to use the enhanced 5-agent analyzer
    """
    
    # Replace with your actual MCP client setup
    # mcp_client = your_mcp_client_instance
    
    # Example 1: Single service analysis with CSV output
    # analyzer = AWSDocumentationAnalyzer(mcp_client=mcp_client)
    # results = await analyzer.analyze_and_save_all("RDS", output_dir="security_analysis")
    # print(f"Analysis complete! CSV: {results['csv_file']}, Report: {results['markdown_file']}")
    
    # Example 2: Multiple services with compliance report and master CSV
    # extractor = SecurityControlsExtractor(mcp_client=mcp_client)
    # services = ["S3", "EC2", "RDS", "Lambda", "IAM"]
    # md_file, csv_file = await extractor.generate_compliance_report(services)
    # print(f"Master compliance report: {md_file}")
    # print(f"Master CSV file: {csv_file}")
    
    # Example 3: Validate existing CSV
    # csv_content = "controlId,controlName,severity,policies,awsConfig,implementation,relatedRequirements\nAWS-S3-001,Bucket Encryption,High,Data Protection Policy,Enable S3 bucket encryption,Configure default encryption,GDPR compliance"
    # validation = analyzer.validate_csv_format(csv_content)
    # print(f"CSV validation: {'PASSED' if validation['is_valid'] else 'FAILED'}")
    
    print("Enhanced example usage complete. Replace mcp_client with your actual MCP client instance.")
    print("\nNew Features in 5-Agent Workflow:")
    print("✅ Structured CSV output with required columns")
    print("✅ Automatic CSV validation")
    print("✅ Multi-service master CSV generation")
    print("✅ Enhanced compliance reporting")
    print("✅ Programmatic CSV format validation")

if __name__ == "__main__":
    asyncio.run(main())
