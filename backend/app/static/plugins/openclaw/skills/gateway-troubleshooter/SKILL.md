# Skill: gateway-troubleshooter

## Overview
Helps diagnose connectivity issues between OpenClaw and Gemini Gateway.

## Instructions
- If a 401 error occurs, verify the `Authorization: Bearer <TOKEN>` header in the config.
- If a "Connection Refused" error occurs, check if the gateway is running on the specified URL (default http://0.0.0.0:6400/mcp).
- Use `opencode mcp list` to verify if the server is recognized.
- Check the gateway logs for "mcp.auth_failed" or "mcp.mounted" events.
