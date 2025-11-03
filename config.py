"""
Cấu hình server và domain
"""
import os
from typing import Optional

# Thông tin VPS
VPS_IP = "97.74.83.97"
VPS_HOSTNAME = "97.83.74.97.host.secureserver.net"
VPS_USERNAME = "myadmin"
VPS_OS = "Ubuntu 22.04"
VPS_LOCATION = "Asia (Singapore)"

# Thông tin Domain
DOMAIN = "lukistar.space"
DOMAIN_FULL = f"https://{DOMAIN}"

# Cấu hình Server
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
SERVER_WORKERS = int(os.getenv("SERVER_WORKERS", "4"))

# Cấu hình Database và Storage
DB_PATH = os.getenv("DB_PATH", "logs.db")
SCREENSHOTS_DIR = os.getenv("SCREENSHOTS_DIR", "screenshots")
RESULTS_DIR = os.getenv("RESULTS_DIR", "results")

# URLs cho API
USE_DOMAIN = os.getenv("USE_DOMAIN", "true").lower() == "true"
if USE_DOMAIN:
    API_BASE_URL = os.getenv("API_BASE_URL", f"http://{DOMAIN}")
    ADMIN_URL = f"{API_BASE_URL}/admin"
else:
    API_BASE_URL = os.getenv("API_BASE_URL", f"http://{VPS_IP}:{SERVER_PORT}")
    ADMIN_URL = f"{API_BASE_URL}/admin"

