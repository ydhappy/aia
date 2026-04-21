from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.models.request_models import DecideRequest, ObserveRequest
from app.services.agent_service import agent_service


router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def websocket_gateway(websocket: WebSocket) -> None:
    if not settings.enable_websocket_gateway:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            action = payload.get("type")
            body = payload.get("body", {})

            if action == "observe":
                request = ObserveRequest(**body)
                response = agent_service.observe(request)
                await websocket.send_json({"type": "observe_result", "body": response.model_dump()})
                continue

            if action == "decide":
                request = DecideRequest(**body)
                response = agent_service.decide(request)
                await websocket.send_json({"type": "decide_result", "body": response.model_dump()})
                continue

            await websocket.send_json({"type": "error", "body": {"detail": "unknown_message_type"}})
    except WebSocketDisconnect:
        return
