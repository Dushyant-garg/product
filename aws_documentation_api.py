"""
FastAPI application for AWS Documentation Analyzer
Provides HTTP API endpoints to analyze AWS services and generate security controls CSV
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Path
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import uuid
import asyncio
from datetime import datetime
import logging

from aws_documentation_analyzer import AWSDocumentationAnalyzer
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AWS Documentation Security Controls Analyzer",
    description="Analyze AWS services documentation and generate structured security controls CSV using 5-agent workflow",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for your environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global analyzer instance (will be initialized with MCP client)
analyzer: Optional[AWSDocumentationAnalyzer] = None

# Request/Response Models
class AnalysisRequest(BaseModel):
    """Request model for AWS service analysis"""
    service_name: str = Field(..., description="AWS service name (e.g., S3, EC2, Lambda)")
    search_query: Optional[str] = Field(None, description="Custom search query, auto-generated if not provided")
    output_dir: Optional[str] = Field("api_output", description="Directory to save output files")

class MultiServiceRequest(BaseModel):
    """Request model for multiple AWS services analysis"""
    service_names: List[str] = Field(..., description="List of AWS service names to analyze")
    output_dir: Optional[str] = Field("api_output", description="Directory to save output files")

class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    status: str = Field(..., description="Analysis status (success/error)")
    service_name: str = Field(..., description="AWS service analyzed")
    analysis_id: str = Field(..., description="Unique analysis identifier")
    csv_records_count: int = Field(..., description="Number of CSV records generated")
    validation_status: str = Field(..., description="CSV validation status (PASSED/FAILED)")
    search_query: str = Field(..., description="Search query used")
    source_url: str = Field(..., description="Documentation URL analyzed")
    file_paths: Dict[str, str] = Field(..., description="Paths to generated files")
    csv_data: Optional[str] = Field(None, description="CSV content")
    validation_issues: List[str] = Field(default_factory=list, description="Validation issues if any")
    timestamp: str = Field(..., description="Analysis timestamp")

class MultiServiceResponse(BaseModel):
    """Response model for multiple services analysis"""
    status: str = Field(..., description="Overall analysis status")
    analysis_id: str = Field(..., description="Unique analysis identifier")
    total_services: int = Field(..., description="Total services requested")
    successful_analyses: int = Field(..., description="Number of successful analyses")
    failed_analyses: int = Field(..., description="Number of failed analyses")
    master_csv_records: int = Field(..., description="Total records in master CSV")
    file_paths: Dict[str, str] = Field(..., description="Paths to generated files")
    service_results: List[AnalysisResponse] = Field(..., description="Individual service results")
    timestamp: str = Field(..., description="Analysis timestamp")

# Startup event to initialize MCP client
@app.on_event("startup")
async def startup_event():
    """Initialize the AWS Documentation Analyzer with MCP client"""
    global analyzer
    
    try:
        # TODO: Initialize your MCP client here
        # For now, we'll initialize without MCP client - you need to replace this
        # with your actual MCP client initialization
        mcp_client = None  # Replace with: await initialize_your_mcp_client()
        
        analyzer = AWSDocumentationAnalyzer(mcp_client=mcp_client)
        logger.info("AWS Documentation Analyzer initialized successfully")
        
        # Create output directory
        os.makedirs("api_output", exist_ok=True)
        
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {str(e)}")
        # You may want to exit the application or handle this differently
        raise

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "analyzer_ready": analyzer is not None
    }

# Single service analysis endpoint
@app.post("/analyze/{service_name}", response_model=AnalysisResponse)
async def analyze_service(
    service_name: str = Path(..., description="AWS service name"),
    search_query: Optional[str] = Query(None, description="Custom search query"),
    output_dir: Optional[str] = Query("api_output", description="Output directory")
) -> AnalysisResponse:
    """
    Analyze a single AWS service and generate security controls CSV
    
    This endpoint runs the complete 5-agent workflow:
    1. DocumentSearchAgent - Search AWS documentation
    2. URLSelectorAgent - Select best URL
    3. DocumentReaderAgent - Read documentation
    4. SecurityControlsProcessor - Structure into CSV
    5. CSVValidator - Validate CSV format
    """
    
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")
    
    analysis_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    try:
        logger.info(f"Starting analysis for service: {service_name} (ID: {analysis_id})")
        
        # Run the complete 5-agent analysis
        results = await analyzer.analyze_and_save_all(
            aws_service=service_name,
            search_query=search_query,
            output_dir=output_dir
        )
        
        # Extract validation info
        csv_validation = results.get("csv_validation", {})
        validation_status = "PASSED" if csv_validation.get("is_valid", False) else "FAILED"
        validation_issues = csv_validation.get("issues", [])
        
        # Count CSV records
        csv_records_count = 0
        if results.get("final_csv"):
            csv_lines = results["final_csv"].strip().split('\n')
            csv_records_count = max(0, len(csv_lines) - 1)  # Exclude header
        
        response = AnalysisResponse(
            status="success",
            service_name=service_name,
            analysis_id=analysis_id,
            csv_records_count=csv_records_count,
            validation_status=validation_status,
            search_query=results.get("search_query", ""),
            source_url=results.get("extracted_url", ""),
            file_paths={
                "csv_file": results.get("csv_file", ""),
                "markdown_file": results.get("markdown_file", "")
            },
            csv_data=results.get("final_csv", ""),
            validation_issues=validation_issues,
            timestamp=timestamp
        )
        
        logger.info(f"Analysis completed for {service_name}: {csv_records_count} records, validation {validation_status}")
        return response
        
    except Exception as e:
        logger.error(f"Analysis failed for {service_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed for {service_name}: {str(e)}"
        )

# Multiple services analysis endpoint
@app.post("/analyze-multiple", response_model=MultiServiceResponse)
async def analyze_multiple_services(request: MultiServiceRequest) -> MultiServiceResponse:
    """
    Analyze multiple AWS services and generate a master compliance report
    
    This endpoint analyzes each service individually and then combines results
    into a master CSV file and comprehensive compliance report.
    """
    
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")
    
    analysis_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    try:
        logger.info(f"Starting multi-service analysis for {len(request.service_names)} services (ID: {analysis_id})")
        
        # Import the SecurityControlsExtractor from example
        from aws_doc_analyzer_example import SecurityControlsExtractor
        
        # Initialize extractor
        extractor = SecurityControlsExtractor(analyzer.mcp_client)
        
        # Generate compliance report
        md_file, csv_file = await extractor.generate_compliance_report(
            request.service_names,
            output_file=os.path.join(request.output_dir, f"compliance_report_{analysis_id}.md")
        )
        
        # Get individual service results
        all_controls = await extractor.extract_security_controls_for_services(request.service_names)
        
        # Build individual service responses
        service_results = []
        successful_analyses = 0
        total_csv_records = 0
        
        for service_name in request.service_names:
            service_data = all_controls.get(service_name, {})
            
            if "error" in service_data:
                service_result = AnalysisResponse(
                    status="error",
                    service_name=service_name,
                    analysis_id=f"{analysis_id}-{service_name}",
                    csv_records_count=0,
                    validation_status="FAILED",
                    search_query="",
                    source_url="",
                    file_paths={},
                    validation_issues=[service_data["error"]],
                    timestamp=timestamp
                )
            else:
                csv_validation = service_data.get("csv_validation", {})
                validation_status = "PASSED" if csv_validation.get("is_valid", False) else "FAILED"
                record_count = csv_validation.get("row_count", 0)
                
                if validation_status == "PASSED":
                    successful_analyses += 1
                    total_csv_records += record_count
                
                service_result = AnalysisResponse(
                    status="success" if validation_status == "PASSED" else "warning",
                    service_name=service_name,
                    analysis_id=f"{analysis_id}-{service_name}",
                    csv_records_count=record_count,
                    validation_status=validation_status,
                    search_query=service_data.get("search_query", ""),
                    source_url=service_data.get("source_url", ""),
                    file_paths={},
                    csv_data=service_data.get("final_csv", ""),
                    validation_issues=csv_validation.get("issues", []),
                    timestamp=timestamp
                )
            
            service_results.append(service_result)
        
        response = MultiServiceResponse(
            status="success",
            analysis_id=analysis_id,
            total_services=len(request.service_names),
            successful_analyses=successful_analyses,
            failed_analyses=len(request.service_names) - successful_analyses,
            master_csv_records=total_csv_records,
            file_paths={
                "master_csv": csv_file,
                "compliance_report": md_file
            },
            service_results=service_results,
            timestamp=timestamp
        )
        
        logger.info(f"Multi-service analysis completed: {successful_analyses}/{len(request.service_names)} successful")
        return response
        
    except Exception as e:
        logger.error(f"Multi-service analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Multi-service analysis failed: {str(e)}"
        )

# File download endpoints
@app.get("/download/csv/{service_name}")
async def download_csv(
    service_name: str = Path(..., description="AWS service name"),
    output_dir: str = Query("api_output", description="Output directory")
):
    """Download the CSV file for a specific service"""
    
    csv_filename = f"aws_{service_name.lower()}_security_controls.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail=f"CSV file not found for service: {service_name}")
    
    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=csv_filename
    )

@app.get("/download/report/{service_name}")
async def download_report(
    service_name: str = Path(..., description="AWS service name"),
    output_dir: str = Query("api_output", description="Output directory")
):
    """Download the markdown report for a specific service"""
    
    report_filename = f"aws_{service_name.lower()}_security_analysis.md"
    report_path = os.path.join(output_dir, report_filename)
    
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail=f"Report file not found for service: {service_name}")
    
    return FileResponse(
        report_path,
        media_type="text/markdown",
        filename=report_filename
    )

@app.get("/download/master-csv/{analysis_id}")
async def download_master_csv(
    analysis_id: str = Path(..., description="Analysis ID"),
    output_dir: str = Query("api_output", description="Output directory")
):
    """Download the master CSV file for multiple services analysis"""
    
    csv_filename = f"compliance_report_{analysis_id}_master.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail=f"Master CSV file not found for analysis: {analysis_id}")
    
    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=csv_filename
    )

# Validation endpoint
@app.post("/validate-csv")
async def validate_csv_data(csv_content: str):
    """Validate CSV content format and data quality"""
    
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")
    
    try:
        validation = analyzer.validate_csv_format(csv_content)
        
        return {
            "validation_status": "PASSED" if validation["is_valid"] else "FAILED",
            "is_valid": validation["is_valid"],
            "row_count": validation["row_count"],
            "column_count": validation["column_count"],
            "issues": validation["issues"],
            "required_columns": validation["required_columns"]
        }
        
    except Exception as e:
        logger.error(f"CSV validation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"CSV validation failed: {str(e)}"
        )

# List available services endpoint
@app.get("/services")
async def list_aws_services():
    """Get list of commonly analyzed AWS services"""
    return {
        "aws_services": [
            "S3", "EC2", "RDS", "Lambda", "IAM", "VPC", "CloudFormation",
            "CloudTrail", "CloudWatch", "ELB", "ALB", "NLB", "API Gateway",
            "DynamoDB", "ECS", "EKS", "ECR", "SNS", "SQS", "KMS", "Secrets Manager",
            "Systems Manager", "Config", "GuardDuty", "Security Hub", "Inspector",
            "WAF", "Shield", "Route53", "CloudFront", "ElastiCache", "Redshift"
        ],
        "description": "Common AWS services that can be analyzed for security controls"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "aws_documentation_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
