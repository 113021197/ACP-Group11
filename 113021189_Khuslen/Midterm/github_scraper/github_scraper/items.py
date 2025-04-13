from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RepositoryItem:
    url: str                    
    about: str                  
    last_updated: str          
    languages: Optional[List[str]] = None  
    commits: Optional[int] = None 