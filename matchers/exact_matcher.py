
from typing import List, Optional

def exact_match(input_ds: str, reference_list: List[str]) -> Optional[str]:
    """
    Case-insensitive exact match.
    Returns the original reference name if matched, else None.
    """
    input_lower = input_ds.lower().strip()
    
    # Optimization: Create a map for O(1) lookup if reference list is large, 
    # but for ~450 entries, iteration is fine.
    # To return the exact reference casing, we iterate.
    
    for ref in reference_list:
        if ref.lower().strip() == input_lower:
            return ref
            
    return None
