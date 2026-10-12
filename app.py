import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, jsonify, request


app = Flask(__name__)


def database_path(data_dir=None):
	directory = Path(data_dir or os.environ.get("DATA_DIR", "/data"))
	directory.mkdir(parents=True, exist_ok=True)
	return directory / "habits.sqlite3"


def connect_database(data_dir=None):
	connection = sqlite3.connect(database_path(data_dir))
	connection.row_factory = sqlite3.Row
	connection.execute("PRAGMA foreign_keys = ON")
	return connection


def initialize_database(data_dir=None):
	connection = connect_database(data_dir)
	try:
		connection.executescript(
			"""
			CREATE TABLE IF NOT EXISTS habits (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL COLLATE NOCASE UNIQUE,
				created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
			);
			CREATE TABLE IF NOT EXISTS completions (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				habit_id INTEGER NOT NULL,
				completion_date TEXT NOT NULL,
				created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
				UNIQUE (habit_id, completion_date),
				FOREIGN KEY (habit_id) REFERENCES habits (id) ON DELETE CASCADE
			);
			"""
		)
		connection.commit()
	finally:
		connection.close()


def calculate_streak(completion_dates, reference_date=None):
	reference = reference_date or date.today()
	completed = {date.fromisoformat(value) for value in completion_dates}
	streak = 0
	current = reference
	while current in completed:
		streak += 1
		current -= timedelta(days=1)
	return streak


def row_data(row):
	return dict(row)


def error(message, status):
	return jsonify({"error": message}), status


def parse_completion_date(value):
	if not isinstance(value, str):
		raise ValueError("completion_date must use YYYY-MM-DD format")
	try:
		return date.fromisoformat(value)
	except ValueError as exc:
		raise ValueError("completion_date must use YYYY-MM-DD format") from exc


@app.get("/")
def index():
	return jsonify({"name": "habit-tracker", "status": "ok"})


@app.get("/habits")
def list_habits():
	connection = connect_database()
	try:
		rows = connection.execute(
			"SELECT id, name, created_at FROM habits ORDER BY id"
		).fetchall()
		return jsonify([row_data(row) for row in rows])
	finally:
		connection.close()


@app.post("/habits")
def create_habit():
	payload = request.get_json(silent=True) or {}
	name = payload.get("name")
	if not isinstance(name, str) or not name.strip():
		return error("name must be a non-empty string", 400)
	connection = connect_database()
	try:
		cursor = connection.execute(
			"INSERT INTO habits (name) VALUES (?)", (name.strip(),)
		)
		connection.commit()
		row = connection.execute(
			"SELECT id, name, created_at FROM habits WHERE id = ?",
			(cursor.lastrowid,),
		).fetchone()
		return jsonify(row_data(row)), 201
	except sqlite3.IntegrityError:
		connection.rollback()
		return error("a habit with that name already exists", 409)
	finally:
		connection.close()


@app.delete("/habits/<int:habit_id>")
def delete_habit(habit_id):
	connection = connect_database()
	try:
		cursor = connection.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
		connection.commit()
		if cursor.rowcount == 0:
			return error("habit not found", 404)
		return "", 204
	finally:
		connection.close()


@app.post("/habits/<int:habit_id>/completions")
def complete_habit(habit_id):
	payload = request.get_json(silent=True) or {}
	value = payload.get("completion_date", date.today().isoformat())
	try:
		completion_date = parse_completion_date(value)
	except ValueError as exc:
		return error(str(exc), 400)
	if completion_date > date.today():
		return error("future completion dates are not allowed", 400)

	connection = connect_database()
	try:
		if connection.execute(
			"SELECT id FROM habits WHERE id = ?", (habit_id,)
		).fetchone() is None:
			return error("habit not found", 404)
		connection.execute(
			"INSERT OR IGNORE INTO completions (habit_id, completion_date) "
			"VALUES (?, ?)",
			(habit_id, completion_date.isoformat()),
		)
		connection.commit()
		row = connection.execute(
			"SELECT id, habit_id, completion_date, created_at FROM completions "
			"WHERE habit_id = ? AND completion_date = ?",
			(habit_id, completion_date.isoformat()),
		).fetchone()
		return jsonify(row_data(row))
	finally:
		connection.close()


@app.get("/habits/<int:habit_id>/completions")
def list_completions(habit_id):
	connection = connect_database()
	try:
		if connection.execute(
			"SELECT id FROM habits WHERE id = ?", (habit_id,)
		).fetchone() is None:
			return error("habit not found", 404)
		rows = connection.execute(
			"SELECT id, habit_id, completion_date, created_at FROM completions "
			"WHERE habit_id = ? ORDER BY completion_date DESC",
			(habit_id,),
		).fetchall()
		return jsonify([row_data(row) for row in rows])
	finally:
		connection.close()


@app.get("/habits/<int:habit_id>/streak")
def habit_streak(habit_id):
	connection = connect_database()
	try:
		if connection.execute(
			"SELECT id FROM habits WHERE id = ?", (habit_id,)
		).fetchone() is None:
			return error("habit not found", 404)
		rows = connection.execute(
			"SELECT completion_date FROM completions WHERE habit_id = ?",
			(habit_id,),
		).fetchall()
		streak = calculate_streak((row["completion_date"] for row in rows))
		return jsonify({"habit_id": habit_id, "streak": streak})
	finally:
		connection.close()


if __name__ == "__main__":
	initialize_database()
	app.run(
		host="0.0.0.0",
		port=int(os.environ.get("PORT", "8000")),
	)
