from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.config import settings
from app.database import SessionLocal, get_db

router = APIRouter(tags=["evaluations"])


def _evaluation_response(
    run, results: list[schemas.PlayerEvaluationResult]
) -> schemas.CampaignEvaluationResponse:
    return schemas.CampaignEvaluationResponse(
        evaluation_id=run.evaluation_id,
        campaign_id=run.campaign_id,
        rules=schemas.StoredRules(
            minimum_level=run.minimum_level,
            countries=run.countries,
        ),
        status=run.status,
        progress=schemas.EvaluationProgress(processed=run.processed, total=run.total),
        error=run.error,
        results=results,
    )


@router.post(
    "/campaign-evaluations",
    response_model=schemas.CampaignEvaluationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_evaluation(
    data: schemas.CampaignEvaluationRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if crud.evaluation_exists(db, data.evaluation_id):
        raise HTTPException(status_code=409, detail="Evaluation already exists")
    run = crud.create_evaluation(
        db,
        evaluation_id=data.evaluation_id,
        campaign_id=data.rules.campaign_id,
        minimum_level=data.rules.minimum_level,
        countries=data.rules.countries,
        total=len(data.player_ids),
    )
    background.add_task(
        crud.execute_evaluation,
        SessionLocal,
        evaluation_id=data.evaluation_id,
        campaign_id=data.rules.campaign_id,
        minimum_level=data.rules.minimum_level,
        countries=data.rules.countries,
        player_ids=data.player_ids,
        batch_size=settings.evaluation_batch_size,
    )
    return _evaluation_response(run, [])


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
    run = crud.get_evaluation(db, evaluation_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    rows = crud.list_evaluation_matches(db, evaluation_id, skip=skip, limit=limit)
    return _evaluation_response(
        run,
        [
            schemas.PlayerEvaluationResult(
                player_id=r.player_id, matches=r.matches, error=r.error
            )
            for r in rows
        ],
    )
