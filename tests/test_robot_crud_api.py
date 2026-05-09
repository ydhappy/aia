from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_robot_crud_lifecycle_with_korean_payload() -> None:
    agent_id = "crud_robot_한글"

    create_response = client.post(
        "/robot/profile",
        json={
            "agent_id": agent_id,
            "name": "테스트로봇",
            "role": "custom",
            "style": "balanced",
            "metadata": {"memo": "한글 UTF-8 유지"},
        },
    )
    assert create_response.status_code == 200

    list_response = client.get("/robot")
    assert list_response.status_code == 200
    assert agent_id in list_response.json()["agent_ids"]

    patch_response = client.patch(
        f"/robot/{agent_id}/profile",
        json={"style": "defensive", "metadata": {"memo": "수정 완료"}},
    )
    assert patch_response.status_code == 200

    read_response = client.get(f"/robot/{agent_id}")
    assert read_response.status_code == 200
    profile = read_response.json()["profile"]
    assert profile["agent_id"] == agent_id
    assert profile["name"] == "테스트로봇"
    assert profile["style"] == "defensive"
    assert profile["metadata"]["memo"] == "수정 완료"

    delete_response = client.delete(f"/robot/{agent_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    missing_response = client.get(f"/robot/{agent_id}")
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"]["code"] == "robot_not_found"
