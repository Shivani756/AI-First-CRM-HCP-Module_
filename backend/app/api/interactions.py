from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ..database import get_db
from ..models.interaction import Interaction
from ..schemas.interaction import InteractionCreate, InteractionUpdate, InteractionResponse

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])


@router.post("", response_model=InteractionResponse, status_code=201)
async def create_interaction(
    payload: InteractionCreate, db: AsyncSession = Depends(get_db)
):
    interaction = Interaction(**payload.model_dump())
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return interaction


@router.get("", response_model=List[InteractionResponse])
async def list_interactions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Interaction).order_by(Interaction.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{interaction_id}", response_model=InteractionResponse)
async def get_interaction(interaction_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Interaction).where(Interaction.id == interaction_id)
    )
    interaction = result.scalar_one_or_none()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.put("/{interaction_id}", response_model=InteractionResponse)
async def update_interaction(
    interaction_id: int,
    payload: InteractionUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Interaction).where(Interaction.id == interaction_id)
    )
    interaction = result.scalar_one_or_none()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(interaction, key, value)

    await db.commit()
    await db.refresh(interaction)
    return interaction
