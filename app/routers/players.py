from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=list[schemas.PlayerRead])
def list_players(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    country: str | None = Query(default=None, min_length=2, max_length=2),
    db: Session = Depends(get_db),
):
    return crud.list_players(db, skip=skip, limit=limit, country=country)


@router.get("/{player_id}", response_model=schemas.PlayerRead)
def get_player(player_id: str, db: Session = Depends(get_db)):
    player = crud.get_player(db, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
