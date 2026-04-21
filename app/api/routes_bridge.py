from fastapi import APIRouter, Depends

from app.core.security import verify_api_key


router = APIRouter(prefix="/bridge", tags=["bridge"], dependencies=[Depends(verify_api_key)])


@router.post("/runtime-call")
def runtime_call(payload: dict) -> dict:
    func_name = str(payload.get("function", "") or "")
    args = payload.get("args", []) or []
    return {
        "ok": True,
        "value": {
            "function": func_name,
            "args": args,
            "mode": "python_java_script_runtime_bridge",
        },
    }
