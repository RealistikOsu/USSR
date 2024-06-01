#!/bin/bash
set -euo pipefail

echo "Starting server..."

cd /app/ussr/

python3.12 main.py
