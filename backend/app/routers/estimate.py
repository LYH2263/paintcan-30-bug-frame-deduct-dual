from fastapi import APIRouter, HTTPException
from app.engines.wall_area import InvalidOpening
from app.schemas.estimate import EstimateRequest
from app.services.paint_service import PaintService
router = APIRouter()


@router.post("/estimate")
def post_estimate(body: EstimateRequest):
    with PaintService() as s:
        try:
            r = s.estimate(body.room_id, body.persist, body.coats, body.coverage)
        except InvalidOpening as e:
            # 内口宽或高 <= 0：整单拒绝，且在落库前抛出 → 不写记录
            raise HTTPException(status_code=422, detail=str(e))
        if not r: raise HTTPException(404)
        return r
