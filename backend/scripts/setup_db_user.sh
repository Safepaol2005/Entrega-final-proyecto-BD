#!/usr/bin/env bash
# Creates a dedicated MySQL user for UNTrade and writes credentials to backend/.env
# Run this on your machine (where MySQL is reachable), then start uvicorn on 8001.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
APP_USER="untrade"
APP_PASS="$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)"
DB_NAME="UnTrade"

echo "Connecting as MySQL root (you will be prompted for the root password if needed)..."
mysql -u root -p <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${APP_USER}'@'localhost' IDENTIFIED BY '${APP_PASS}';
CREATE USER IF NOT EXISTS '${APP_USER}'@'127.0.0.1' IDENTIFIED BY '${APP_PASS}';
ALTER USER '${APP_USER}'@'localhost' IDENTIFIED BY '${APP_PASS}';
ALTER USER '${APP_USER}'@'127.0.0.1' IDENTIFIED BY '${APP_PASS}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${APP_USER}'@'localhost';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${APP_USER}'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL

python3 - <<PY
from pathlib import Path
env = Path(${ENV_FILE@Q})
kv = {
    "DB_HOST": "127.0.0.1",
    "DB_PORT": "3306",
    "DB_USER": ${APP_USER@Q},
    "DB_PASSWORD": ${APP_PASS@Q},
    "DB_NAME": ${DB_NAME@Q},
    "API_HOST": "127.0.0.1",
    "API_PORT": "8001",
}
text = env.read_text(encoding="utf-8") if env.exists() else ""
lines, seen = [], set()
for line in text.splitlines():
    if not line or line.strip().startswith("#") or "=" not in line:
        lines.append(line); continue
    key = line.split("=", 1)[0].strip()
    if key in kv:
        lines.append(f"{key}={kv[key]}"); seen.add(key)
    else:
        lines.append(line)
for k, v in kv.items():
    if k not in seen:
        lines.append(f"{k}={v}")
env.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("Updated", env)
print("DB_USER=${APP_USER}")
print("API_PORT=8001")
print("Restart: uvicorn main:app --reload --host 127.0.0.1 --port 8001")
PY
