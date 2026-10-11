from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.database import get_db

router = APIRouter(tags=["evaluations"])


@router.post(
    "/campaign-evaluations",
    response_model=schemas.CampaignEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_evaluation(data: schemas.CampaignEvaluationRequest, db: Session = Depends(get_db)):
    batch_size = settings.evaluation_batch_size
    results: list[schemas.PlayerEvaluationResult] = []
    for i in range(0, len(data.player_ids), batch_size):
        chunk = data.player_ids[i : i + batch_size]
        found: dict[str, models.Player] = {
            p.player_id: p for p in crud.get_players_by_ids(db, chunk)
        }
        for pid in chunk:
            player = found.get(pid)
            if player is None:
                results.append(
                    schemas.PlayerEvaluationResult(
                        player_id=pid, matches=False, error="player not found"
                    )
                )
                continue
            record = crud.save_match(
                db,
                campaign_id=data.rules.campaign_id,
                player=player,
                evaluation_id=data.evaluation_id,
                minimum_level=data.rules.minimum_level,
                countries=data.rules.countries,
            )
            results.append(
                schemas.PlayerEvaluationResult(player_id=pid, matches=record.matches)
            )
    return schemas.CampaignEvaluationResponse(
        evaluation_id=data.evaluation_id,
        campaign_id=data.rules.campaign_id,
        rules=schemas.StoredRules(
            minimum_level=data.rules.minimum_level,
            countries=data.rules.countries,
        ),
        results=results,
    )


@router.get(
    "/campaign-evaluations/{evaluation_id}",
    response_model=schemas.CampaignEvaluationResponse,
)
def get_evaluation(
    evaluation_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    rows = crud.list_evaluation_matches(db, evaluation_id, skip=skip, limit=limit)
    if not rows:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return schemas.CampaignEvaluationResponse(
        evaluation_id=evaluation_id,
        campaign_id=rows[0].campaign_id,
        rules=schemas.StoredRules(
            minimum_level=rows[0].minimum_level,
            countries=rows[0].countries,
        ),
        results=[
            schemas.PlayerEvaluationResult(player_id=r.player_id, matches=r.matches)
            for r in rows
        ],
    )
