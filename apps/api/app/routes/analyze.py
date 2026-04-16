"""FastAPI routes — POST /v1/analyze"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.rules.engine import analyze_claim
from app.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/v1/analyze", tags=["analyze"])


@router.post("/", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> AnalyzeResponse:
    try:
        return await analyze_claim(request, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
