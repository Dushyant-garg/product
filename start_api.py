#!/usr/bin/env python3
"""
Startup script for AWS Documentation Analyzer FastAPI
Handles MCP client initialization and server startup
"""

import uvicorn
import asyncio
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup required directories and environment"""
    
    # Create output directories
    directories = ["api_output", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    # Check if required files exist
    required_files = [
        "aws_documentation_analyzer.py",
        "aws_documentation_api.py", 
        "app/config.py"  # Assuming your config file is here
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        logger.error("Please ensure all required files are in the current directory")
        return False
    
    return True

async def initialize_mcp_client():
    """
    Initialize your MCP client here
    
    TODO: Replace this with your actual MCP client initialization
    """
    logger.info("Initializing MCP client...")
    
    try:
        # TODO: Add your actual MCP client initialization here
        # For example:
        # from your_mcp_module import create_mcp_client
        # mcp_client = await create_mcp_client(
        #     server_path="path/to/aws-documentation-mcp-server",
        #     config=your_config
        # )
        
        # For now, return None - you need to replace this
        mcp_client = None
        
        if mcp_client is None:
            logger.warning("⚠️  MCP client is None - you need to implement MCP client initialization in start_api.py")
            logger.warning("⚠️  The API will start but analyses will fail until MCP client is properly configured")
        else:
            logger.info("✅ MCP client initialized successfully")
        
        return mcp_client
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize MCP client: {str(e)}")
        logger.error("The API will start but analyses will fail")
        return None

def update_api_with_mcp_client(mcp_client):
    """Update the FastAPI app with the initialized MCP client"""
    
    try:
        # Import the FastAPI app and update the analyzer
        from aws_documentation_api import app, analyzer
        from aws_documentation_analyzer import AWSDocumentationAnalyzer
        
        # Create new analyzer instance with MCP client
        global_analyzer = AWSDocumentationAnalyzer(mcp_client=mcp_client)
        
        # Update the global analyzer in the API module
        import aws_documentation_api
        aws_documentation_api.analyzer = global_analyzer
        
        logger.info("✅ FastAPI app updated with MCP client")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to update FastAPI app with MCP client: {str(e)}")
        return False

async def main():
    """Main startup function"""
    
    logger.info("🚀 Starting AWS Documentation Analyzer API Server")
    
    # Setup environment
    if not setup_environment():
        logger.error("❌ Environment setup failed")
        sys.exit(1)
    
    # Initialize MCP client
    mcp_client = await initialize_mcp_client()
    
    # Update API with MCP client
    if not update_api_with_mcp_client(mcp_client):
        logger.error("❌ Failed to configure API with MCP client")
        sys.exit(1)
    
    # Server configuration
    config = {
        "app": "aws_documentation_api:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,
        "log_level": "info",
        "access_log": True,
        "log_config": {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "formatter": "default",
                    "class": "logging.FileHandler",
                    "filename": "logs/api.log",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default", "file"],
            },
        },
    }
    
    logger.info("🌐 Starting FastAPI server...")
    logger.info(f"📍 Server will be available at: http://localhost:{config['port']}")
    logger.info(f"📖 API Documentation: http://localhost:{config['port']}/docs")
    logger.info(f"📚 ReDoc Documentation: http://localhost:{config['port']}/redoc")
    
    if mcp_client is None:
        logger.warning("⚠️  Server starting without MCP client - analyses will fail!")
        logger.warning("⚠️  Please implement MCP client initialization in start_api.py")
    
    # Start the server
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {str(e)}")
        sys.exit(1)

def run_dev_server():
    """Quick development server start (without MCP client setup)"""
    
    logger.info("🚀 Starting Development Server (without MCP client)")
    logger.warning("⚠️  This is for development only - analyses will fail without MCP client")
    
    setup_environment()
    
    uvicorn.run(
        "aws_documentation_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AWS Documentation Analyzer API Server")
    parser.add_argument(
        "--dev", 
        action="store_true", 
        help="Start development server without MCP client setup"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to run the server on (default: 8000)"
    )
    
    args = parser.parse_args()
    
    if args.dev:
        run_dev_server()
    else:
        asyncio.run(main())
