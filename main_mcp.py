
import asyncio
import sys
import pandas as pd
from typing import List, Dict, Any
from mcp import ClientSession

from config import (
    ACAT_REF_PATH, USER_INPUT_PATH, OUTPUT_DIR, 
    CONFIDENCE_THRESHOLD, MCP_SERVER_SCRIPT
)
from utils.logger import setup_logger
from utils.mcp_client import MCPClientWrapper
from processors.input_processor import (
    load_acat_reference, load_user_input, 
    split_multi_datastore, extract_product_version
)
from matchers.exact_matcher import exact_match
from models.datastore import (
    NormalizedDatastore, MatchResult, 
    APISuccessResult, APINotFoundResult, APIErrorResult
)
from output_generator import (
    generate_matched_datastores_csv,
    generate_api_success_csv,
    generate_api_not_found_csv,
    generate_api_errors_csv,
    display_statistics
)

logger = setup_logger("main_mcp")

async def process_datastores():
    # 1. Load Data
    try:
        acat_refs = load_acat_reference(ACAT_REF_PATH)
        input_df = load_user_input(USER_INPUT_PATH)
    except Exception as e:
        logger.critical(f"Failed to load input data: {e}")
        return

    # 2. Process Input (Split multi-values)
    # Assuming input_df has a column 'Datastore' or uses the first column
    col_name = input_df.columns[0]
    processed_inputs = [] # List of strings
    
    for idx, row in input_df.iterrows():
        raw_val = str(row[col_name])
        split_items = split_multi_datastore(raw_val)
        processed_inputs.extend(split_items)
        
    logger.info(f"Expanded {len(input_df)} rows into {len(processed_inputs)} datastore entries.")

    # 3. Setup Results Containers
    phase1_results: List[MatchResult] = []
    api_lookup_queue: List[str] = [] # List of original strings to lookup
    
    phase2_success: List[APISuccessResult] = []
    phase2_not_found: List[APINotFoundResult] = []
    phase2_errors: List[APIErrorResult] = []

    # 4. Connect to MCP Server
    client = MCPClientWrapper(MCP_SERVER_SCRIPT)
    try:
        await client.connect()
        
        # 5. Phase 1 Matching
        logger.info("Starting Phase 1: Matching...")
        
        for ds in processed_inputs:
            try:
                # A. Exact Match
                exact = exact_match(ds, acat_refs)
                if exact:
                    logger.info(f"Exact match found: {ds} -> {exact}")
                    phase1_results.append(MatchResult(
                        original=ds,
                        matched_name=exact,
                        confidence=1.0,
                        reasoning="Exact string match",
                        match_type="exact"
                    ))
                    continue # Skip LLM/API for exact matches (per implied logic, or do we?)
                    # Instructions say: "If no exact match -> Call MCP llm_match"
                
                # B. LLM Match
                logger.info(f"Calling LLM for: {ds}")
                llm_res = await client.call_tool("llm_match", {
                    "input_datastore": ds,
                    "reference_list": acat_refs 
                })
                
                # Parse LLM Result
                matched_name = llm_res.get("matched_datastore", "NOT FOUND")
                confidence = float(llm_res.get("confidence", 0.0))
                reasoning = llm_res.get("reasoning", "")
                
                phase1_results.append(MatchResult(
                    original=ds,
                    matched_name=matched_name,
                    confidence=confidence,
                    reasoning=reasoning,
                    match_type="llm"
                ))
                
                # C. Check for API Flag
                if confidence < CONFIDENCE_THRESHOLD:
                    logger.info(f"Low confidence ({confidence}) for '{ds}'. Flagging for API lookup.")
                    api_lookup_queue.append(ds)
                    
            except Exception as e:
                logger.error(f"Error processing {ds}: {e}")
                phase1_results.append(MatchResult(
                    original=ds,
                    matched_name="ERROR",
                    confidence=0.0,
                    reasoning=str(e),
                    match_type="error"
                ))

        # Generate Phase 1 CSV
        generate_matched_datastores_csv(phase1_results, f"{OUTPUT_DIR}/matched_datastores.csv")
        
        # 6. Phase 2 API Lookup
        logger.info(f"Starting Phase 2: API Lookup for {len(api_lookup_queue)} items...")
        
        for ds in api_lookup_queue:
            try:
                # Extract product/version
                # We use the helper, but maybe the LLM tool could have done this? 
                # The instructions say "Extract product/version... Call MCP endoflife_lookup"
                
                parsed = extract_product_version(ds)
                product = parsed['product']
                version = parsed['version']
                
                if not version:
                    # heuristic: if no version, we can't really do EOL check effectively
                    # check if product has simple mapping?
                    pass

                api_res = await client.call_tool("endoflife_lookup", {
                    "product": product,
                    "version": version
                })
                
                status = api_res.get("status")
                
                if status == "success":
                    data = api_res.get("data", {})
                    phase2_success.append(APISuccessResult(
                        original=ds,
                        product=api_res.get("mapped_product", product),
                        version=version,
                        eol_cycle=data.get("cycle", ""),
                        release_date=data.get("releaseDate", ""),
                        eol_date=data.get("eol", ""),
                        lts=data.get("lts", False),
                        support=data.get("support", ""), # parsing support status needed?
                        latest_version=data.get("latest", ""),
                        link=data.get("link", ""),
                        api_response=data
                    ))
                elif status == "not_found":
                    phase2_not_found.append(APINotFoundResult(
                        original=ds,
                        product=product,
                        version=version,
                        status="not_found",
                        reason=api_res.get("reason", ""),
                        api_response=api_res,
                        attempts=3
                    ))
                else: # error
                    phase2_errors.append(APIErrorResult(
                        original=ds,
                        product=product,
                        version=version,
                        status="error",
                        error_message=api_res.get("error_message", ""),
                        api_response=api_res,
                        attempts=3
                    ))
                    
            except Exception as e:
                logger.error(f"API Lookup failed for {ds}: {e}")
                phase2_errors.append(APIErrorResult(
                    original=ds,
                    product="unknown",
                    version="unknown",
                    status="error",
                    error_message=str(e),
                    api_response=None,
                    attempts=1
                ))

        # Generate Phase 2 CSVs
        generate_api_success_csv(phase2_success, f"{OUTPUT_DIR}/api_success.csv")
        generate_api_not_found_csv(phase2_not_found, f"{OUTPUT_DIR}/api_not_found.csv")
        generate_api_errors_csv(phase2_errors, f"{OUTPUT_DIR}/api_errors.csv")
        
        # Statistics
        display_statistics(phase1_results, phase2_success, phase2_not_found, phase2_errors)

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(process_datastores())
