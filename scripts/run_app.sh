#!/bin/bash
set -euo pipefail

echo "Starting server..."

cd /app/ussr/

python3.9 main.py
