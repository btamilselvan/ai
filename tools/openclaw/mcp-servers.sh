#!/bin/bash
# setup-mcp.sh
openclaw mcp set my-local-server '{
  "command": "python",
  "args": ["'$(pwd)'/mcp-server/main.py"],
  "env": {
    "DEBUG": "true"
  }
}'