# AWS Documentation Analyzer - FastAPI Server

## 🚀 Overview

This FastAPI application provides HTTP endpoints to analyze AWS services documentation and generate structured security controls CSV using the enhanced 5-agent workflow.

## 🎯 Features

- **Single Service Analysis** - Analyze individual AWS services
- **Multiple Services Analysis** - Batch analyze multiple services with master CSV
- **File Downloads** - Download CSV and markdown reports  
- **CSV Validation** - Validate CSV format and data quality
- **Real-time Processing** - Async processing with status tracking
- **Comprehensive Logging** - Detailed logging and error handling

## 🏗️ Architecture

```
FastAPI Server
├── DocumentSearchAgent (search_documentation MCP tool)
├── URLSelectorAgent (select best documentation URL)
├── DocumentReaderAgent (read_documentation MCP tool)  
├── SecurityControlsProcessor (structure into CSV)
└── CSVValidator (validate format and data)
```

## 📋 API Endpoints

### Core Analysis Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze/{service_name}` | Analyze single AWS service |
| `POST` | `/analyze-multiple` | Analyze multiple AWS services |
| `POST` | `/validate-csv` | Validate CSV content format |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check and status |
| `GET` | `/services` | List available AWS services |

### File Download Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/download/csv/{service_name}` | Download service CSV file |
| `GET` | `/download/report/{service_name}` | Download service markdown report |
| `GET` | `/download/master-csv/{analysis_id}` | Download master CSV from multi-service analysis |

## 🛠️ Setup & Installation

### 1. Install Dependencies

```bash
# Install FastAPI dependencies
pip install -r requirements_api.txt

# Install your existing project dependencies
pip install autogen-agentchat autogen-ext openai
```

### 2. Configure MCP Client

**Important**: You need to configure your MCP client in `start_api.py`:

```python
# In start_api.py, replace the TODO section:
async def initialize_mcp_client():
    # Add your actual MCP client initialization
    from your_mcp_module import create_mcp_client
    
    mcp_client = await create_mcp_client(
        server_path="path/to/aws-documentation-mcp-server",
        config=your_config
    )
    
    return mcp_client
```

### 3. Start the Server

```bash
# Method 1: Using startup script (recommended)
python start_api.py

# Method 2: Development mode (without MCP client)
python start_api.py --dev

# Method 3: Direct uvicorn
uvicorn aws_documentation_api:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the API

- **API Server**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📖 Usage Examples

### Using Python Requests

```python
import requests

# Single service analysis
response = requests.post(
    "http://localhost:8000/analyze/S3",
    params={"search_query": "S3 security encryption best practices"}
)

result = response.json()
print(f"CSV Records: {result['csv_records_count']}")
print(f"Validation: {result['validation_status']}")

# Download CSV file
csv_response = requests.get("http://localhost:8000/download/csv/S3")
with open("s3_security_controls.csv", "wb") as f:
    f.write(csv_response.content)
```

### Using the Test Client

```python
from test_api_client import AWSDocumentationAPIClient

client = AWSDocumentationAPIClient()

# Analyze single service
result = client.analyze_service("Lambda")
csv_path = client.download_csv("Lambda")

# Analyze multiple services  
multi_result = client.analyze_multiple_services(["S3", "EC2", "RDS"])
master_csv = client.download_master_csv(multi_result['analysis_id'])
```

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Analyze S3
curl -X POST "http://localhost:8000/analyze/S3" \
  -H "Content-Type: application/json"

# Analyze multiple services
curl -X POST "http://localhost:8000/analyze-multiple" \
  -H "Content-Type: application/json" \
  -d '{"service_names": ["S3", "EC2", "RDS"]}'

# Download CSV
curl -O "http://localhost:8000/download/csv/S3"
```

## 📊 API Response Format

### Single Service Analysis Response

```json
{
  "status": "success",
  "service_name": "S3",
  "analysis_id": "uuid-here",
  "csv_records_count": 15,
  "validation_status": "PASSED",
  "search_query": "S3 security controls best practices",
  "source_url": "https://docs.aws.amazon.com/s3/...",
  "file_paths": {
    "csv_file": "api_output/aws_s3_security_controls.csv",
    "markdown_file": "api_output/aws_s3_security_analysis.md"
  },
  "csv_data": "controlId,controlName,severity,...",
  "validation_issues": [],
  "timestamp": "2024-01-01T12:00:00"
}
```

### Multiple Services Analysis Response

```json
{
  "status": "success", 
  "analysis_id": "uuid-here",
  "total_services": 3,
  "successful_analyses": 3,
  "failed_analyses": 0,
  "master_csv_records": 45,
  "file_paths": {
    "master_csv": "api_output/compliance_report_uuid_master.csv",
    "compliance_report": "api_output/compliance_report_uuid.md"
  },
  "service_results": [...],
  "timestamp": "2024-01-01T12:00:00"
}
```

## 📁 Output Files

### Directory Structure

```
api_output/
├── aws_s3_security_controls.csv
├── aws_s3_security_analysis.md
├── aws_ec2_security_controls.csv
├── aws_ec2_security_analysis.md
├── compliance_report_uuid.md
└── compliance_report_uuid_master.csv
```

### CSV Format

```csv
controlId,controlName,severity,policies,awsConfig,implementation,relatedRequirements
AWS-S3-001,Bucket Encryption,High,Data Protection Policy,Enable default encryption,Configure S3 bucket encryption,GDPR compliance
AWS-S3-002,Access Logging,Medium,Audit Policy,Enable access logging,Configure logging bucket,SOX compliance
AWS-S3-003,Public Access Block,Critical,Security Policy,Block all public access,Enable public access block settings,PCI DSS requirement
```

## 🔧 Configuration

### Environment Variables

```bash
# OpenAI Configuration (from your app.config)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_OUTPUT_DIR=api_output
```

### Customization Options

```python
# In aws_documentation_api.py startup event
analyzer = AWSDocumentationAnalyzer(
    mcp_client=your_mcp_client
)

# Customize output directory per request
await analyzer.analyze_and_save_all(
    aws_service="S3",
    output_dir="custom_output_dir"
)
```

## 🧪 Testing

### Run Test Client

```bash
# Comprehensive API tests
python test_api_client.py

# Individual examples
python -c "from test_api_client import example_single_service; example_single_service()"
```

### API Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "analyzer_ready": true}
```

## 🚨 Error Handling

### Common Issues

1. **MCP Client Not Configured**
   ```json
   {"detail": "Analyzer not initialized"}
   ```
   **Solution**: Configure MCP client in `start_api.py`

2. **File Not Found**
   ```json
   {"detail": "CSV file not found for service: S3"}
   ```
   **Solution**: Ensure analysis completed successfully before downloading

3. **Invalid Service Name**
   ```json
   {"detail": "Analysis failed for InvalidService: Service not found"}
   ```
   **Solution**: Use valid AWS service names (see `/services` endpoint)

### Logging

Logs are written to:
- **Console**: Real-time output
- **File**: `logs/api.log`

## 🔒 Security Considerations

- **CORS**: Configure allowed origins in production
- **Rate Limiting**: Consider adding rate limiting for production use
- **Authentication**: Add authentication for production deployment
- **File Access**: Secure file download endpoints
- **Input Validation**: All inputs are validated via Pydantic models

## 🚀 Production Deployment

### Docker Deployment (example)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements_api.txt
EXPOSE 8000

CMD ["python", "start_api.py"]
```

### Using Gunicorn

```bash
pip install gunicorn
gunicorn aws_documentation_api:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📈 Monitoring

### Health Endpoint

Monitor API health with:
```bash
curl http://localhost:8000/health
```

### Metrics to Track

- Response times per endpoint
- Success/failure rates
- File generation rates
- CSV validation pass rates
- MCP client connection status

## 🤝 Contributing

1. Implement MCP client initialization in `start_api.py`
2. Test with your aws-documentation-mcp-server
3. Add additional AWS services to the analysis list
4. Enhance error handling and logging
5. Add authentication and rate limiting for production

## 📞 Support

For issues:
1. Check the logs in `logs/api.log`
2. Verify MCP client connection
3. Test with the health endpoint
4. Use the test client for debugging

## 🎉 Ready to Use!

Your FastAPI server is ready to analyze AWS documentation and generate structured security controls. Just configure your MCP client and start analyzing!
