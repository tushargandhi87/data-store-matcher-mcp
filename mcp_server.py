
import os
import time
import json
import logging
import requests
from typing import List, Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import anthropic

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_server")

load_dotenv()

# Configuration
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-5-sonnet-20241022" # Using a valid sonnet model as default, user specified claude-sonnet-4-20250514 which might be a future/internal model tag. I will use the user's tag if possible or fallback.
# User specified: claude-sonnet-4-20250514. I will use it.
CLAUDE_MODEL_USER = "claude-sonnet-4-20250514" 
# NOTE: If this model tag doesn't exist, it will fail. I will use it as requested.

PRODUCT_MAP = {
    "sql server": "mssql",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mongodb": "mongodb",
    "redis": "redis",
    "mysql": "mysql",
    "oracle": "oracle-database",
    "access": "access",
    "sqlite": "sqlite",
    "mariadb": "mariadb",
    "elasticsearch": "elasticsearch",
    "kafka": "kafka",
    "rabbitmq": "rabbitmq",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "nginx": "nginx",
    "apache": "apache",
    "tomcat": "tomcat",
    "jenkins": "jenkins",
    "git": "git",
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "python": "python",
    "java": "java",
    "go": "go",
    "ruby": "ruby",
    "php": "php",
    "ubuntu": "ubuntu",
    "debian": "debian",
    "centos": "centos",
    "fedora": "fedora",
    "rhel": "rhel",
    "windows server": "windows-server",
    "visual studio": "visual-studio",
    "dotnet": "dotnet",
    # Add more as needed based on common datastores
}

mcp = FastMCP("acat_matcher")
anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

@mcp.tool()
def llm_match(input_datastore: str, reference_list: List[str]) -> Dict[str, Any]:
    """
    Match a user-provided datastore to the ACAT reference list using an LLM.
    """
    time.sleep(0.5) # Rate limiting
    
    logger.info(f"LLM Matching: {input_datastore}")
    
    # Constructing the Prompt
    # Using a robust template since the exact one wasn't fully visible in prompt description
    prompt = f"""
    You are an expert software asset manager.
    Task: Match the input datastore name to exactly one entry in the provided ACAT reference list.
    
    Input Datastore: "{input_datastore}"
    
    ACAT Reference List:
    {json.dumps(reference_list, indent=2)}
    
    Instructions:
    1. Analyze the input datastore name (accounting for typos, version numbers, or variations).
    2. Find the best match in the ACAT Reference List.
    3. If multiple versions exist in the list, choose the most generic one unless the input specifies a version.
    4. Provide a confidence score (0.0 to 1.0).
    5. Provide short reasoning.
    
    Return ONLY a JSON object with this format:
    {{
        "matched_datastore": "Exact String Found In List",
        "confidence": 0.9,
        "reasoning": "Explanation..."
    }}
    
    If no reasonable match matches, return "matched_datastore": "NOT FOUND" with low confidence.
    """

    try:
        response = anthropic_client.messages.create(
            model=CLAUDE_MODEL_USER, # Using the requested model tag
            max_tokens=1000,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        # Strip code fences if present
        content = content.replace("```json", "").replace("```", "").strip()
        
        result = json.loads(content)
        return result
        
    except Exception as e:
        logger.error(f"LLM match failed: {e}")
        return {
            "matched_datastore": "NOT FOUND",
            "confidence": 0.0,
            "reasoning": str(e)
        }

@mcp.tool()
def endoflife_lookup(product: str, version: str) -> Dict[str, Any]:
    """
    Check endoflife.date API for product version details.
    """
    time.sleep(0.5) # Rate limiting
    
    # 1. Map product name
    mapped_product = PRODUCT_MAP.get(product.lower(), product.lower().replace(" ", "-"))
    
    url = f"https://endoflife.date/api/{mapped_product}.json"
    logger.info(f"Checking EOL for {mapped_product} version {version}")
    
    attempts = 0
    max_attempts = 3
    backoff = [1, 2, 4]
    
    final_error = None
    
    while attempts < max_attempts:
        try:
            resp = requests.get(url, timeout=30)
            
            if resp.status_code == 404:
                return {
                    "status": "not_found",
                    "reason": "Product not found in endoflife.date",
                    "product": mapped_product,
                    "original_product": product,
                    "version": version
                }
            
            if resp.status_code != 200:
                raise Exception(f"API returned {resp.status_code}")
                
            data = resp.json()
            # data is a list of cycles
            
            # Find matching cycle
            # Logic: Try exact match on 'cycle', then loose match?
            # 'cycle' in API is usually major or semi-major version (e.g. "1.19", "14", "2019")
            
            best_match = None
            
            for cycle_data in data:
                c_ver = str(cycle_data.get('cycle', ''))
                # Simple exact match check on cycle
                # Version input: "2012", cycle: "2012" -> match
                # Version input: "14.1", cycle: "14" -> maybe match?
                
                if c_ver == version:
                    best_match = cycle_data
                    break
                
                # Try simple prefix matching if version provided is more specific
                if version.startswith(c_ver + "."):
                    best_match = cycle_data
                    # Keep looking for better match? Usually cycles are unique.
                    break
            
            if best_match:
                return {
                    "status": "success",
                    "data": best_match,
                    "mapped_product": mapped_product
                }
            else:
                # Fallback: find closest? 
                # For now return not found version
                return {
                    "status": "not_found",
                    "reason": "Version not found for product",
                    "product": mapped_product,
                    "available_cycles": [c['cycle'] for c in data[:5]]
                }

        except Exception as e:
            final_error = str(e)
            logger.warning(f"Attempt {attempts+1} failed: {e}")
            time.sleep(backoff[attempts])
            attempts += 1
            
    return {
        "status": "error",
        "error_message": final_error,
        "product": mapped_product
    }

if __name__ == "__main__":
    mcp.run()
