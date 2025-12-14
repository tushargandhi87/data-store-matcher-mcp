
# ACAT Datastore Matcher (MCP)

This tool matches user-provided datastore names against the ACAT reference list using exact matching logic and an LLM (Claude) via the Model Context Protocol (MCP). It also performs end-of-life (EOL) checks for items that cannot be confidently matched.

## Architecture

- **MCP Architecture**: Utilizes a central MCP server (`mcp_server.py`) that exposes `llm_match` and `endoflife_lookup` tools.
- **Client**: `main_mcp.py` acts as the orchestrator, connecting to the MCP server via stdio.
- **No Normalization**: Raw inputs are processed directly.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**:
   - Rename `.env` (it may already be set) and add your `CLAUDE_API_KEY`.
   - Ensure `input/ACAT_Data_Stores_Master.xlsx` and `input/user_input.xlsx` exist.

## Usage

Run the main orchestrator:
```bash
python main_mcp.py
```

## Output

Results are saved in the `output/` directory:
- `matched_datastores.csv`: Phase 1 matching results.
- `api_success.csv`: Successful EOL lookups.
- `api_not_found.csv`: Products not found in EOL database.
- `api_errors.csv`: API connection or processing errors.

## Troubleshooting

- **MCP Connection Error**: Ensure `mcp_server.py` is executable and `mcp` library is installed.
- **LLM Rate Limit**: The tool waits 0.5s between calls. Increase if needed in `mcp_server.py`.
