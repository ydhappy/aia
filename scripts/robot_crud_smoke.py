import json
import os
import time
import urllib.error
import urllib.request


BASE_URL = os.environ.get("AIA_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_KEY = os.environ.get("API_KEY", "")


def request_json(method: str, path: str, payload: dict | None = None, expected_status: int = 200) -> dict:
    body = None
    headers = {"Accept": "application/json", "Content-Type": "application/json; charset=utf-8"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(BASE_URL + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            status = response.getcode()
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        status = exc.code
        data = json.loads(exc.read().decode("utf-8"))
    if status != expected_status:
        raise RuntimeError("%s %s expected %s got %s: %s" % (method, path, expected_status, status, data))
    return data


def main() -> None:
    agent_id = "robot_crud_smoke_%s" % int(time.time())
    profile = {
        "agent_id": agent_id,
        "name": "스모크로봇",
        "role": "custom",
        "style": "balanced",
        "metadata": {"source": "robot_crud_smoke", "memo": "UTF-8 확인"},
    }

    created = request_json("POST", "/robot/profile", profile)
    listed = request_json("GET", "/robot")
    if agent_id not in listed.get("agent_ids", []):
        raise RuntimeError("created agent_id not found in /robot list: %s" % listed)

    patched = request_json(
        "PATCH",
        "/robot/%s/profile" % urllib.parse.quote(agent_id, safe=""),
        {"style": "defensive", "metadata": {"source": "robot_crud_smoke", "memo": "수정 완료"}},
    )
    loaded = request_json("GET", "/robot/%s" % urllib.parse.quote(agent_id, safe=""))
    deleted = request_json("DELETE", "/robot/%s" % urllib.parse.quote(agent_id, safe=""))
    missing = request_json("GET", "/robot/%s" % urllib.parse.quote(agent_id, safe=""), expected_status=404)

    print("ROBOT_CRUD_SMOKE_OK=1")
    print("CREATE=%s" % created.get("accepted"))
    print("PATCH=%s" % patched.get("accepted"))
    print("STYLE=%s" % loaded.get("profile", {}).get("style"))
    print("DELETE=%s" % deleted.get("deleted"))
    print("MISSING_CODE=%s" % missing.get("detail", {}).get("code"))


if __name__ == "__main__":
    main()
