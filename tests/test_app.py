from datetime import date, timedelta

import app
import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app.initialize_database()
    return app.app.test_client()


def create_habit(client, name="Read"):
    response = client.post("/habits", json={"name": name})
    assert response.status_code == 201
    return response.json["id"]


def test_index_and_empty_habit_list(client):
    assert client.get("/").json == {"name": "habit-tracker", "status": "ok"}
    assert client.get("/habits").json == []


def test_create_habit_trims_name_and_rejects_invalid_names(client):
    response = client.post("/habits", json={"name": "  Read  "})
    assert response.status_code == 201
    assert response.json["name"] == "Read"

    assert client.post("/habits", json={"name": "read"}).status_code == 409
    assert client.post("/habits", json={"name": "   "}).status_code == 400
    assert client.post("/habits", json={"name": 12}).status_code == 400
    assert client.post("/habits", data="not json").status_code == 400


def test_delete_habit_and_missing_habit(client):
    habit_id = create_habit(client)
    assert client.get("/habits").json[0]["id"] == habit_id

    assert client.delete(f"/habits/{habit_id}").status_code == 204
    assert client.get("/habits").json == []
    assert client.delete(f"/habits/{habit_id}").status_code == 404


def test_completion_is_idempotent_and_history_is_sorted(client):
    habit_id = create_habit(client)
    today = date.today()
    yesterday = today - timedelta(days=1)

    first = client.post(
        f"/habits/{habit_id}/completions",
        json={"completion_date": today.isoformat()},
    )
    duplicate = client.post(
        f"/habits/{habit_id}/completions",
        json={"completion_date": today.isoformat()},
    )
    older = client.post(
        f"/habits/{habit_id}/completions",
        json={"completion_date": yesterday.isoformat()},
    )

    assert first.status_code == duplicate.status_code == older.status_code == 200
    assert duplicate.json["id"] == first.json["id"]
    assert [row["completion_date"] for row in client.get(
        f"/habits/{habit_id}/completions"
    ).json] == [today.isoformat(), yesterday.isoformat()]


def test_completion_rejects_invalid_or_future_dates(client):
    habit_id = create_habit(client)
    future = date.today() + timedelta(days=1)

    assert client.post(
        f"/habits/{habit_id}/completions", json={"completion_date": "bad"}
    ).status_code == 400
    assert client.post(
        f"/habits/{habit_id}/completions", json={"completion_date": future.isoformat()}
    ).status_code == 400
    assert client.post(
        "/habits/999/completions", json={"completion_date": date.today().isoformat()}
    ).status_code == 404
    assert client.get("/habits/999/completions").status_code == 404
    assert client.get("/habits/999/streak").status_code == 404


def test_streak_counts_only_consecutive_dates(client):
    reference = date.today()
    habit_id = create_habit(client)
    for offset in (2, 1, 0):
        response = client.post(
            f"/habits/{habit_id}/completions",
            json={"completion_date": (reference - timedelta(days=offset)).isoformat()},
        )
        assert response.status_code == 200

    assert client.get(f"/habits/{habit_id}/streak").json == {
        "habit_id": habit_id,
        "streak": 3,
    }
    assert app.calculate_streak(
        [reference.isoformat(), (reference - timedelta(days=2)).isoformat()],
        reference,
    ) == 1
    assert app.calculate_streak([], reference) == 0


def test_deleting_habit_deletes_completions(client):
    habit_id = create_habit(client)
    client.post(
        f"/habits/{habit_id}/completions",
        json={"completion_date": date.today().isoformat()},
    )

    assert client.delete(f"/habits/{habit_id}").status_code == 204

    connection = app.connect_database()
    try:
        assert connection.execute("SELECT COUNT(*) FROM completions").fetchone()[0] == 0
    finally:
        connection.close()


def test_parse_completion_date_rejects_non_string():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        app.parse_completion_date(None)
