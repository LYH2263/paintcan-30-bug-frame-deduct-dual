from fastapi import APIRouter, HTTPException
from app.engines.wall_area import InvalidOpening
from app.schemas.opening import OpeningMarginRequest
from app.services.paint_service import PaintService
router = APIRouter()


@router.get("/rooms")
def list_rooms():
    with PaintService() as s: return {"items": s.list_rooms()}


@router.get("/rooms/{room_id}")
def room_detail(room_id: int):
    with PaintService() as s:
        d = s.room_detail(room_id)
        if not d: raise HTTPException(404)
        return d


@router.patch("/openings/{opening_id}/margin")
def patch_opening_margin(opening_id: int, body: OpeningMarginRequest):
    with PaintService() as s:
        try:
            o = s.update_opening_margin(opening_id, body.margin)
        except InvalidOpening as e:
            raise HTTPException(status_code=422, detail=str(e))
        if not o: raise HTTPException(404)
        return o
