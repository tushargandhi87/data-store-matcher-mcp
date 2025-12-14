import os
from dotenv import load_dotenv

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
ACAT_REF_PATH = os.getenv("ACAT_REF_PATH", "input/ACAT_Data_Stores_Master.xlsx")
USER_INPUT_PATH = os.getenv("USER_INPUT_PATH", "input/user_input.xlsx")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
MCP_SERVER_SCRIPT = os.getenv("MCP_SERVER_SCRIPT", "mcp_server.py")

if not CLAUDE_API_KEY:
    # We warn but don't crash yet, allowing setup to continue
    print("WARNING: CLAUDE_API_KEY not found in environment.")
