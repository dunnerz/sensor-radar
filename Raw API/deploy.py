#!/usr/bin/env python3
"""
Deployment script for the Sensor Coverage API.
This script helps deploy and test the application.
"""

import subprocess
import sys
import time
import requests
import os
from pathlib import Path

def run_command(command, description=""):
    """Run a command and handle errors."""
    print(f"🔄 {description}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_docker():
    """Check if Docker is available."""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is available")
            return True
        else:
            print("❌ Docker is not available")
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed")
        return False

def check_docker_compose():
    """Check if Docker Compose is available."""
    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose is available")
            return True
        else:
            print("❌ Docker Compose is not available")
            return False
    except FileNotFoundError:
        print("❌ Docker Compose is not installed")
        return False

def check_terrain_file():
    """Check if terrain file exists."""
    terrain_file = Path("london-terrain-test.tif")
    if terrain_file.exists():
        print(f"✅ Terrain file found: {terrain_file}")
        return True
    else:
        print(f"❌ Terrain file not found: {terrain_file}")
        print("   Please ensure the terrain file is in the project directory")
        return False

def deploy_with_docker():
    """Deploy using Docker Compose."""
    print("\n🐳 Deploying with Docker Compose...")
    
    # Build and start the containers
    if not run_command("docker-compose up --build -d", "Building and starting containers"):
        return False
    
    # Wait for the service to be ready
    print("⏳ Waiting for service to be ready...")
    time.sleep(10)
    
    # Check if the service is running
    try:
        response = requests.get("http://localhost:8000/", timeout=10)
        if response.status_code == 200:
            print("✅ Service is running and responding")
            return True
        else:
            print(f"❌ Service responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Service is not responding: {e}")
        return False

def deploy_with_python():
    """Deploy using Python directly."""
    print("\n🐍 Deploying with Python...")
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install dependencies
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Start the server
    print("🚀 Starting the server...")
    print("   The server will be available at: http://localhost:8000")
    print("   Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([f"{pip_cmd}", "install", "uvicorn"], check=True)
        subprocess.run([f"{pip_cmd}", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

def run_tests():
    """Run the comprehensive test suite."""
    print("\n🧪 Running comprehensive tests...")
    
    # Wait a bit for the service to be fully ready
    time.sleep(5)
    
    # Run the test script
    if not run_command("python test_comprehensive_api.py", "Running API tests"):
        return False
    
    return True

def show_status():
    """Show the current status of the deployment."""
    print("\n📊 Deployment Status")
    print("=" * 40)
    
    # Check if service is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
            data = response.json()
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Version: {data.get('version', 'N/A')}")
        else:
            print(f"❌ API responded with status: {response.status_code}")
    except requests.exceptions.RequestException:
        print("❌ API is not responding")
    
    # Check Docker containers
    try:
        result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n🐳 Docker containers:")
            print(result.stdout)
    except:
        print("❌ Could not check Docker containers")

def main():
    """Main deployment function."""
    print("🚀 Sensor Coverage API - Deployment Script")
    print("=" * 50)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    
    if not check_terrain_file():
        print("❌ Cannot proceed without terrain file")
        sys.exit(1)
    
    docker_available = check_docker() and check_docker_compose()
    
    # Choose deployment method
    if docker_available:
        print("\n🐳 Docker deployment available")
        choice = input("Deploy with Docker? (y/n): ").lower().strip()
        
        if choice in ['y', 'yes']:
            if deploy_with_docker():
                show_status()
                if input("\nRun tests? (y/n): ").lower().strip() in ['y', 'yes']:
                    run_tests()
            else:
                print("❌ Docker deployment failed")
                sys.exit(1)
        else:
            print("🐍 Using Python deployment instead...")
            deploy_with_python()
    else:
        print("🐍 Using Python deployment...")
        deploy_with_python()

if __name__ == "__main__":
    main() 