"""
Test client for AWS Documentation Analyzer FastAPI
Demonstrates how to use the API endpoints
"""

import requests
import json
import time
from typing import List

class AWSDocumentationAPIClient:
    """Client for interacting with AWS Documentation Analyzer API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def health_check(self) -> dict:
        """Check API health status"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def list_services(self) -> dict:
        """Get list of available AWS services"""
        response = self.session.get(f"{self.base_url}/services")
        response.raise_for_status()
        return response.json()
    
    def analyze_service(self, service_name: str, search_query: str = None, output_dir: str = "api_output") -> dict:
        """
        Analyze a single AWS service
        
        Args:
            service_name: AWS service name (e.g., 'S3', 'EC2')
            search_query: Optional custom search query
            output_dir: Output directory for files
            
        Returns:
            Analysis results dictionary
        """
        params = {"output_dir": output_dir}
        if search_query:
            params["search_query"] = search_query
        
        response = self.session.post(f"{self.base_url}/analyze/{service_name}", params=params)
        response.raise_for_status()
        return response.json()
    
    def analyze_multiple_services(self, service_names: List[str], output_dir: str = "api_output") -> dict:
        """
        Analyze multiple AWS services
        
        Args:
            service_names: List of AWS service names
            output_dir: Output directory for files
            
        Returns:
            Multi-service analysis results
        """
        payload = {
            "service_names": service_names,
            "output_dir": output_dir
        }
        
        response = self.session.post(f"{self.base_url}/analyze-multiple", json=payload)
        response.raise_for_status()
        return response.json()
    
    def download_csv(self, service_name: str, output_dir: str = "api_output", save_path: str = None) -> str:
        """
        Download CSV file for a service
        
        Args:
            service_name: AWS service name
            output_dir: Output directory on server
            save_path: Local path to save file (optional)
            
        Returns:
            Path where file was saved
        """
        params = {"output_dir": output_dir}
        response = self.session.get(f"{self.base_url}/download/csv/{service_name}", params=params)
        response.raise_for_status()
        
        if not save_path:
            save_path = f"aws_{service_name.lower()}_security_controls.csv"
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return save_path
    
    def download_report(self, service_name: str, output_dir: str = "api_output", save_path: str = None) -> str:
        """
        Download markdown report for a service
        
        Args:
            service_name: AWS service name
            output_dir: Output directory on server
            save_path: Local path to save file (optional)
            
        Returns:
            Path where file was saved
        """
        params = {"output_dir": output_dir}
        response = self.session.get(f"{self.base_url}/download/report/{service_name}", params=params)
        response.raise_for_status()
        
        if not save_path:
            save_path = f"aws_{service_name.lower()}_security_analysis.md"
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return save_path
    
    def download_master_csv(self, analysis_id: str, output_dir: str = "api_output", save_path: str = None) -> str:
        """
        Download master CSV file for multiple services analysis
        
        Args:
            analysis_id: Analysis ID from multi-service analysis
            output_dir: Output directory on server
            save_path: Local path to save file (optional)
            
        Returns:
            Path where file was saved
        """
        params = {"output_dir": output_dir}
        response = self.session.get(f"{self.base_url}/download/master-csv/{analysis_id}", params=params)
        response.raise_for_status()
        
        if not save_path:
            save_path = f"compliance_report_{analysis_id}_master.csv"
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return save_path
    
    def validate_csv(self, csv_content: str) -> dict:
        """
        Validate CSV content format
        
        Args:
            csv_content: CSV content as string
            
        Returns:
            Validation results dictionary
        """
        response = self.session.post(f"{self.base_url}/validate-csv", data=csv_content)
        response.raise_for_status()
        return response.json()


# Example usage and tests
async def test_api_examples():
    """Example usage of the API client"""
    
    client = AWSDocumentationAPIClient()
    
    print("🔍 Testing AWS Documentation Analyzer API\n")
    
    # 1. Health check
    print("1. Health Check")
    try:
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Analyzer Ready: {health['analyzer_ready']}")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # 2. List available services
    print("\n2. Available Services")
    try:
        services = client.list_services()
        print(f"   Available: {', '.join(services['aws_services'][:10])}... (showing first 10)")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Analyze single service
    print("\n3. Single Service Analysis (S3)")
    try:
        s3_result = client.analyze_service("S3", search_query="S3 security best practices encryption")
        print(f"   Status: {s3_result['status']}")
        print(f"   CSV Records: {s3_result['csv_records_count']}")
        print(f"   Validation: {s3_result['validation_status']}")
        print(f"   Source URL: {s3_result['source_url'][:100]}...")
        
        # Download files
        if s3_result['status'] == 'success':
            csv_path = client.download_csv("S3")
            report_path = client.download_report("S3")
            print(f"   Downloaded: {csv_path}, {report_path}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Analyze multiple services
    print("\n4. Multiple Services Analysis")
    try:
        multi_result = client.analyze_multiple_services(["EC2", "RDS", "Lambda"])
        print(f"   Status: {multi_result['status']}")
        print(f"   Total Services: {multi_result['total_services']}")
        print(f"   Successful: {multi_result['successful_analyses']}")
        print(f"   Master CSV Records: {multi_result['master_csv_records']}")
        
        # Download master CSV
        if multi_result['status'] == 'success':
            master_csv = client.download_master_csv(multi_result['analysis_id'])
            print(f"   Downloaded: {master_csv}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. CSV validation
    print("\n5. CSV Validation Test")
    try:
        sample_csv = """controlId,controlName,severity,policies,awsConfig,implementation,relatedRequirements
AWS-S3-001,Bucket Encryption,High,Data Protection Policy,Enable default encryption,Configure S3 default encryption,GDPR compliance
AWS-S3-002,Access Logging,Medium,Audit Policy,Enable access logging,Configure logging bucket,SOX compliance"""
        
        validation = client.validate_csv(sample_csv)
        print(f"   Validation Status: {validation['validation_status']}")
        print(f"   Row Count: {validation['row_count']}")
        print(f"   Issues: {len(validation['issues'])}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ API testing complete!")


# Direct execution examples
def example_single_service():
    """Example: Analyze single AWS service"""
    client = AWSDocumentationAPIClient()
    
    print("Analyzing Lambda security controls...")
    
    try:
        result = client.analyze_service(
            service_name="Lambda",
            search_query="AWS Lambda security IAM permissions encryption"
        )
        
        print(f"Analysis completed!")
        print(f"  - CSV Records: {result['csv_records_count']}")
        print(f"  - Validation: {result['validation_status']}")
        print(f"  - Files: {result['file_paths']}")
        
        # Display CSV data preview
        if result.get('csv_data'):
            lines = result['csv_data'].split('\n')
            print(f"\nCSV Preview (first 3 lines):")
            for i, line in enumerate(lines[:3]):
                print(f"  {i+1}: {line}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")


def example_multiple_services():
    """Example: Analyze multiple AWS services"""
    client = AWSDocumentationAPIClient()
    
    services = ["S3", "EC2", "RDS"]
    print(f"Analyzing multiple services: {', '.join(services)}")
    
    try:
        result = client.analyze_multiple_services(services)
        
        print(f"Multi-service analysis completed!")
        print(f"  - Total Services: {result['total_services']}")
        print(f"  - Successful: {result['successful_analyses']}")
        print(f"  - Failed: {result['failed_analyses']}")
        print(f"  - Master CSV Records: {result['master_csv_records']}")
        print(f"  - Files: {result['file_paths']}")
        
        # Show individual service results
        print(f"\nIndividual Service Results:")
        for service_result in result['service_results']:
            status_emoji = "✅" if service_result['status'] == 'success' else "❌"
            print(f"  {status_emoji} {service_result['service_name']}: {service_result['csv_records_count']} records")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import asyncio
    
    print("🚀 AWS Documentation Analyzer API Test Client\n")
    print("Make sure the FastAPI server is running on http://localhost:8000\n")
    print("Start server with: python aws_documentation_api.py\n")
    
    # Run comprehensive tests
    # asyncio.run(test_api_examples())
    
    # Or run individual examples:
    print("Example 1: Single Service Analysis")
    example_single_service()
    
    print("\n" + "="*50 + "\n")
    
    print("Example 2: Multiple Services Analysis")  
    example_multiple_services()
