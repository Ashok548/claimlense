"""FastAPI routes — GET /v1/report"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.report_service import get_or_generate_report

router = APIRouter(prefix="/v1/report", tags=["report"])

@router.get("/{analysis_id}")
async def generate_report(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        url = await get_or_generate_report(analysis_id, db)
        return {"download_url": url}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
