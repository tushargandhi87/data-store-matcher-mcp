
import pandas as pd
import re
from typing import List, Dict, Any
from utils.logger import setup_logger
from models.datastore import NormalizedDatastore

logger = setup_logger("input_processor")

def load_acat_reference(filepath: str) -> List[str]:
    """Load ACAT reference from Excel, return list of datastore names."""
    logger.info(f"Loading ACAT reference from {filepath}")
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)
    
    # Assuming the column name is 'Data Store' or similar, we'll try to find the first likely string column
    # Or just take the first column if no headers match.
    # Instruction says "ACAT_Data_Stores_Master.xlsx". 
    # We will assume the column with datastore names is the first one or named 'Name'/'Data Store'
    
    possible_cols = ['Data Store', 'Name', 'Datastore', 'Application']
    col_name = None
    for col in possible_cols:
        if col in df.columns:
            col_name = col
            break
            
    if not col_name:
        col_name = df.columns[0] # Fallback to first column
        
    logger.info(f"Using column '{col_name}' for ACAT reference")
    
    # Drop NAs and convert to string
    datastores = df[col_name].dropna().astype(str).tolist()
    logger.info(f"Loaded {len(datastores)} reference datastores")
    return datastores

def load_user_input(filepath: str) -> pd.DataFrame:
    """Load user input, return DataFrame, filtering out empty rows."""
    logger.info(f"Loading user input from {filepath}")
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)
        
    # Filter out nulls and empty strings from the first column
    if not df.empty:
        col = df.columns[0]
        original_count = len(df)
        
        # Convert to string, strip whitespace, replace empty strings with NaN, then dropna
        df = df[df[col].notna()] # Drop explicit NaNs first
        
        # Check for string whitespace if column is object/string type
        if pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
             df = df[df[col].astype(str).str.strip().astype(bool)]
             
        filtered_count = len(df)
        if filtered_count < original_count:
            logger.info(f"Filtered out {original_count - filtered_count} empty/null rows. Remaining: {filtered_count}")
            
    return df

def split_multi_datastore(datastore_str: str) -> List[str]:
    """Split 'Access 2010, SQL Server 2012' into separate entries."""
    if not isinstance(datastore_str, str):
        return []
        
    # Split by comma or newline, trimming whitespace
    # But be careful about version numbers containing commas (rare but possible?)
    # Generally assume comma separator for distinct products
    items = re.split(r'[,\n]+', datastore_str)
    return [item.strip() for item in items if item.strip()]

def extract_product_version(text: str) -> dict:
    """
    Heuristic to split product from version. 
    e.g. "SQL Server 2012" -> {"product": "SQL Server", "version": "2012"}
    This is a fallback/helper for pre-processing if needed, 
    but mainly we rely on LLM for complex stuff. 
    This is simple logic: strings with numbers at end.
    """
    # Find the last sequence of digits/dots
    match = re.search(r'^(.*?)(\d+(?:\.\d+)*)$', text)
    if match:
        return {"product": match.group(1).strip(), "version": match.group(2).strip(), "original": text}
    return {"product": text, "version": "", "original": text}
