
import pandas as pd
from typing import List
from models.datastore import MatchResult, APISuccessResult, APINotFoundResult, APIErrorResult
import dataclasses

def generate_matched_datastores_csv(results: List[MatchResult], filepath: str):
    if not results:
        df = pd.DataFrame(columns=[field.name for field in dataclasses.fields(MatchResult)])
    else:
        df = pd.DataFrame([dataclasses.asdict(r) for r in results])
    
    # Ensure correct column ordering if specified, otherwise default to dataclass order
    # Prompt says "7 columns", MatchResult has 7.
    df.to_csv(filepath, index=False)
    print(f"Generated {filepath} with {len(df)} rows.")

def generate_api_success_csv(results: List[APISuccessResult], filepath: str):
    if not results:
        df = pd.DataFrame(columns=[field.name for field in dataclasses.fields(APISuccessResult)])
    else:
        df = pd.DataFrame([dataclasses.asdict(r) for r in results])
    df.to_csv(filepath, index=False)
    print(f"Generated {filepath} with {len(df)} rows.")

def generate_api_not_found_csv(results: List[APINotFoundResult], filepath: str):
    if not results:
        df = pd.DataFrame(columns=[field.name for field in dataclasses.fields(APINotFoundResult)])
    else:
        df = pd.DataFrame([dataclasses.asdict(r) for r in results])
    df.to_csv(filepath, index=False)
    print(f"Generated {filepath} with {len(df)} rows.")

def generate_api_errors_csv(results: List[APIErrorResult], filepath: str):
    if not results:
        df = pd.DataFrame(columns=[field.name for field in dataclasses.fields(APIErrorResult)])
    else:
        df = pd.DataFrame([dataclasses.asdict(r) for r in results])
    df.to_csv(filepath, index=False)
    print(f"Generated {filepath} with {len(df)} rows.")

def display_statistics(phase1_results, phase2_success, phase2_not_found, phase2_errors):
    total_input = len(phase1_results)
    matches_exact = sum(1 for r in phase1_results if r.match_type == 'exact')
    matches_llm = sum(1 for r in phase1_results if r.match_type == 'llm' and r.confidence >= 0.7) # heuristic for "successful" LLM match
    matches_failed = sum(1 for r in phase1_results if r.confidence < 0.7) # flagged for API
    
    print("\n" + "="*40)
    print("EXECUTION STATISTICS")
    print("="*40)
    print(f"Total Datastores Processed: {total_input}")
    print("-" * 20)
    print("PHASE 1: MATCHING")
    print(f"  Exact Matches:    {matches_exact}")
    print(f"  LLM Matches:      {matches_llm}")
    print(f"  Low Confidence:   {matches_failed} (Flagged for API)")
    print("-" * 20)
    print("PHASE 2: API LOOKUP")
    print(f"  API Success:      {len(phase2_success)}")
    print(f"  API Not Found:    {len(phase2_not_found)}")
    print(f"  API Errors:       {len(phase2_errors)}")
    print("="*40 + "\n")
