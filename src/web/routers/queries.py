"""
Queries management routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from typing import List
from pydantic import BaseModel

from ..services.auth_service import verify_token_dependency

router = APIRouter(prefix="/api/queries", tags=["queries"])


class QueriesResponse(BaseModel):
    """Queries response model."""
    queries: List[str]
    total: int
    file: str


@router.get("", response_model=QueriesResponse)
async def get_queries(
    mode: str = "default",
    payload: dict = Depends(verify_token_dependency)
):
    """
    Get search queries for the specified mode.
    
    - **mode**: Query file mode (default, gemini, openrouter, modelscope, siliconflow)
    """
    try:
        query_file = f"config/queries/{mode}.txt"
        query_path = Path(query_file)
        
        if not query_path.exists():
            raise HTTPException(status_code=404, detail=f"Query file not found: {mode}")
        
        queries = []
        with open(query_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    queries.append(line)
        
        return QueriesResponse(
            queries=queries,
            total=len(queries),
            file=query_file
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Query file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

