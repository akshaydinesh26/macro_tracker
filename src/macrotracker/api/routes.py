import asyncio
from fastapi import APIRouter, status, Request, Response
from fastapi.responses import HTTPException

from macrotracker.models.models import (
    AvailableResponse, 
    DataResponse, 
    HealthResponse, 
    IndicatorsResponse,
    DataRequest,
     DataPoint )
from macrotracker.database.storage import SeriesNotFound
from macrotracker.services.process_request import retrive_data
router = APIRouter()

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check():
    return HealthResponse()

@router.get("/available", response_model=AvailableResponse)
async def readiness(response: Response, request: Request):
    sync_done = getattr(request.app.state, "sync_done", False)
    sync_error = getattr(request.app.state, "sync_error", None)
    if not sync_done:
        reason = sync_error or "Sync not completed"
        response.status_code = (
            status.HTTP_500_INTERNAL_SERVER_ERROR if sync_error
            else status.HTTP_503_SERVICE_UNAVAILABLE)
        return AvailableResponse.model_validate(
            {"status": "not ready", "sync_status": sync_done, "sync_error": reason}
        )
    response.status_code = status.HTTP_200_OK
    return AvailableResponse.model_validate(
        {"status": "ready", "sync_status": sync_done, "sync_error": sync_error}
    )

@router.get("/")
async def root_path():
    return {"root": "you are at the root. you should use the endpoint /macrotracker"}

@router.post("/macrotracker")
async def run_macrotracker(body:DataRequest, request: Request):
    state = request.app.state
    indicators = state.indicators.get("indicator", [])
    indicator_ids = [item['fred_code'] for item in indicators]
    if body.indicator not in indicator_ids:
        raise HTTPException(404, f"Unknown indicator: {body.indicator}")
    # retrive data from the database
    try:
        rows = await asyncio.to_thread(
            retrive_data, body.indicator, body.start_date, body.end_date
        )
    except SeriesNotFound:
        raise HTTPException(
            503, f'No data found for indicator {body.indicator} in {body.start_date}–{body.end_date}'
        )
    return DataRequest(
        indicators=body.indicator,
        start_date=body.start_date,
        end_date=body.end_date,
        count=len(rows),
        data=[DataPoint(date=d,value=v) for d,v in rows]
    )


@router.get("/indicators", response_model=IndicatorsResponse)
async def list_indicators(request: Request):
    return IndicatorsResponse(indicators=request.app.state.indicators.get("indicator",[]))
