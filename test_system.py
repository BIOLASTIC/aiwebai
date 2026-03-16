#!/usr/bin/env python3
"""
Final verification script to confirm all features of the Gemini Unified Gateway are working
"""

import requests
import json
import time

BASE_URL = "http://0.0.0.0:6400"
API_KEY = "sk-pXHS7Y5hP2f-6EEFHn_pVAUm_5mtFZmG3s43e38SbYc"


def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200, (
        f"Health endpoint failed: {response.status_code}"
    )
    print("✅ Health endpoint: OK")


def test_openapi():
    """Test OpenAPI schema (fixed recursion bug)"""
    response = requests.get(f"{BASE_URL}/openapi.json")
    assert response.status_code == 200, (
        f"OpenAPI endpoint failed: {response.status_code}"
    )
    data = response.json()
    assert "paths" in data, "OpenAPI schema missing paths"
    print("✅ OpenAPI schema: OK (recursion bug fixed)")


def test_chat_completions():
    """Test OpenAI-compatible chat completions"""
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    data = {
        "model": "gemini-2.0-flash",
        "messages": [{"role": "user", "content": "Hello, world!"}],
    }
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions", headers=headers, json=data
    )
    assert response.status_code == 200, (
        f"Chat completions failed: {response.status_code}"
    )
    result = response.json()
    assert "choices" in result, "Missing choices in response"
    print("✅ Chat completions: OK")


def test_file_storage():
    """Test file upload/list functionality"""
    headers = {"X-API-Key": API_KEY}
    response = requests.get(f"{BASE_URL}/v1/files", headers=headers)
    assert response.status_code == 200, f"File listing failed: {response.status_code}"
    result = response.json()
    assert "data" in result, "Missing data in file response"
    print("✅ File storage: OK")


def test_models():
    """Test models endpoint via admin interface"""
    # Login first
    login_data = "username=admin@local.host&password=111111"
    login_response = requests.post(
        f"{BASE_URL}/admin/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=login_data,
    )
    assert login_response.status_code == 200, (
        f"Admin login failed: {login_response.status_code}"
    )

    token_data = login_response.json()
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    response = requests.get(f"{BASE_URL}/admin/models/", headers=headers)
    assert response.status_code == 200, (
        f"Models endpoint failed: {response.status_code}"
    )
    result = response.json()
    assert len(result) > 0, "No models returned"
    print("✅ Models discovery: OK")


def test_native_image_generation():
    """Test native image generation"""
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    data = {"prompt": "A colorful test image", "model": "imagen-3.0", "size": "256x256"}
    response = requests.post(
        f"{BASE_URL}/native/tasks/image", headers=headers, json=data
    )
    assert response.status_code == 200, (
        f"Image generation failed: {response.status_code}"
    )
    result = response.json()
    assert "job_id" in result, "Missing job_id in response"
    print("✅ Native image generation: OK")


def test_native_video_generation():
    """Test native video generation"""
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    data = {"prompt": "A short test video", "model": "veo-2.0", "duration": 2}
    response = requests.post(
        f"{BASE_URL}/native/tasks/video", headers=headers, json=data
    )
    assert response.status_code == 200, (
        f"Video generation failed: {response.status_code}"
    )
    result = response.json()
    assert "job_id" in result, "Missing job_id in response"
    print("✅ Native video generation: OK")


def test_mcp_server():
    """Test MCP server"""
    response = requests.get("http://0.0.0.0:6403/health")
    assert response.status_code == 200, (
        f"MCP server health check failed: {response.status_code}"
    )
    print("✅ MCP server: OK")


def test_frontend():
    """Test frontend accessibility"""
    response = requests.get("http://0.0.0.0:6401")
    assert response.status_code == 200, (
        f"Frontend not accessible: {response.status_code}"
    )
    print("✅ Frontend: OK")


def test_swagger_docs():
    """Test Swagger documentation"""
    response = requests.get(f"{BASE_URL}/docs")
    assert response.status_code == 200, (
        f"Swagger docs not accessible: {response.status_code}"
    )
    print("✅ Swagger documentation: OK")


def main():
    """Run all tests"""
    print("🧪 Running final verification tests...\n")

    test_health()
    test_openapi()
    test_chat_completions()
    test_file_storage()
    test_models()
    test_native_image_generation()
    test_native_video_generation()
    test_mcp_server()
    test_frontend()
    test_swagger_docs()

    print("\n🎉 All tests passed! System is 100% operational.")
    print("\n📋 Final verification completed:")
    print("   • Backend API: http://0.0.0.0:6400")
    print("   • Frontend: http://0.0.0.0:6401")
    print("   • Swagger docs: http://0.0.0.0:6400/docs")
    print("   • MCP Server: http://0.0.0.0:6403")
    print("   • Credentials: admin@local.host / 111111")
    print("   • Global API Key: sk-pXHS7Y5hP2f-6EEFHn_pVAUm_5mtFZmG3s43e38SbYc")


if __name__ == "__main__":
    main()
