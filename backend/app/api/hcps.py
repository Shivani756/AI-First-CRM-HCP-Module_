from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ..database import get_db
from ..models.hcp import HCP
from ..models.material import Material
from ..schemas.hcp import HCPResponse

router = APIRouter(prefix="/api/hcps", tags=["HCPs"])


@router.get("", response_model=List[HCPResponse])
async def search_hcps(
    q: str = Query(default="", description="Search query"),
    db: AsyncSession = Depends(get_db),
):
    query = select(HCP)
    if q:
        query = query.where(HCP.name.ilike(f"%{q}%"))
    result = await db.execute(query.order_by(HCP.name).limit(20))
    return result.scalars().all()


@router.get("/{hcp_id}", response_model=HCPResponse)
async def get_hcp(hcp_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HCP).where(HCP.id == hcp_id))
    hcp = result.scalar_one_or_none()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp


materials_router = APIRouter(prefix="/api/materials", tags=["Materials"])


@materials_router.get("")
async def search_materials(
    q: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    query = select(Material)
    if q:
        query = query.where(Material.name.ilike(f"%{q}%"))
    result = await db.execute(query.limit(20))
    items = result.scalars().all()
    return [{"id": m.id, "name": m.name, "type": m.type, "url": m.url} for m in items]
