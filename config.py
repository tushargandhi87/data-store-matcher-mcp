import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(rel_path):
    # If it's already absolute, return it
    if os.path.isabs(rel_path):
        return rel_path
    # Otherwise join with BASE_DIR
    return os.path.join(BASE_DIR, rel_path)

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
ACAT_REF_PATH = get_path(os.getenv("ACAT_REF_PATH", "input/ACAT_Data_Stores_Master.xlsx"))
USER_INPUT_PATH = get_path(os.getenv("USER_INPUT_PATH", "input/user_input.xlsx"))
OUTPUT_DIR = get_path(os.getenv("OUTPUT_DIR", "output"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
MCP_SERVER_SCRIPT = os.getenv("MCP_SERVER_SCRIPT", "mcp_server.py")

if not CLAUDE_API_KEY:
    # We warn but don't crash yet, allowing setup to continue
    import sys
    sys.stderr.write("WARNING: CLAUDE_API_KEY not found in environment.\n")
