#!/usr/bin/env python3
"""Sync StellarMate custom drivers from Ekos to Web Manager."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Iterable, Sequence


SOURCE_DB = Path.home() / ".var/app/org.kde.kstars/data/kstars/userdb.sqlite"
SOURCE_TABLE = "customdrivers"
SOURCE_COLUMNS = ["Name", "Label", "Family", "Exec", "Version"]

DEST_DB = Path.home() / ".indi/profiles.db"
DEST_TABLE = "custom"
DEST_COLUMNS = ["name", "label", "family", "exec", "version"]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Sync StellarMate custom drivers from Ekos to Web Manager."
	)
	parser.add_argument(
		"--dryrun",
		action="store_true",
		help="Show what would happen without writing to the destination database.",
	)
	parser.add_argument(
		"--force",
		action="store_true",
		help="Skip the confirmation prompt before copying.",
	)
	return parser.parse_args(argv)


def fetch_rows(db_path: Path, table: str, columns: Iterable[str], readonly: bool = False) -> list[sqlite3.Row]:
	if readonly:
		conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
	else:
		conn = sqlite3.connect(db_path)

	conn.row_factory = sqlite3.Row
	try:
		column_list = ", ".join(columns)
		query = f"SELECT id, {column_list} FROM {table} ORDER BY id ASC"
		return conn.execute(query).fetchall()
	finally:
		conn.close()


def print_rows(title: str, rows: Sequence[sqlite3.Row], columns: Sequence[str]) -> None:
	print(title)
	if not rows:
		print("  (no rows)")
		return

	headers = ["id", *columns]
	widths = {header: len(header) for header in headers}
	rendered_rows: list[list[str]] = []

	for row in rows:
		rendered_row = [str(row["id"])]
		rendered_row.extend("" if row[column] is None else str(row[column]) for column in columns)
		rendered_rows.append(rendered_row)
		for header, value in zip(headers, rendered_row, strict=True):
			widths[header] = max(widths[header], len(value))

	def render(values: Sequence[str]) -> str:
		return "  " + "  ".join(value.ljust(widths[header]) for header, value in zip(headers, values, strict=True))

	print(render(headers))
	for rendered_row in rendered_rows:
		print(render(rendered_row))


def confirm() -> bool:
	response = input(
		"Continue with the copy? Existing rows in the destination table will be deleted. [y/N]: "
	).strip().lower()
	return response in {"y", "yes"}


def backup_destination(db_path: Path) -> Path:
	backup_path = Path(f"{db_path}.syncbackup")
	shutil.copy2(db_path, backup_path)
	return backup_path


def clear_destination(conn: sqlite3.Connection) -> None:
	conn.execute(f"DELETE FROM {DEST_TABLE}")


def copy_rows(conn: sqlite3.Connection, rows: Sequence[sqlite3.Row]) -> None:
	columns_sql = ", ".join(DEST_COLUMNS)
	placeholders = ", ".join(["?"] * len(DEST_COLUMNS))
	insert_sql = f"INSERT INTO {DEST_TABLE} ({columns_sql}) VALUES ({placeholders})"

	for row in rows:
		values = [row["Name"], row["Label"], row["Family"], row["Exec"], row["Version"]]
		conn.execute(insert_sql, values)
		print(
			"  copied id={id} name={name} label={label} family={family} exec={exec} version={version}".format(
				id=row["id"],
				name="" if row["Name"] is None else row["Name"],
				label="" if row["Label"] is None else row["Label"],
				family="" if row["Family"] is None else row["Family"],
				exec="" if row["Exec"] is None else row["Exec"],
				version="" if row["Version"] is None else row["Version"],
			)
		)


def main(argv: Sequence[str]) -> int:
	args = parse_args(argv)

	if not SOURCE_DB.exists():
		print(f"Source database not found: {SOURCE_DB}", file=sys.stderr)
		return 1
	if not DEST_DB.exists():
		print(f"Destination database not found: {DEST_DB}", file=sys.stderr)
		return 1

	source_rows = fetch_rows(SOURCE_DB, SOURCE_TABLE, SOURCE_COLUMNS, readonly=True)
	destination_rows = fetch_rows(DEST_DB, DEST_TABLE, DEST_COLUMNS)

	if args.dryrun:
		print_rows(f"Source table: {SOURCE_TABLE}", source_rows, SOURCE_COLUMNS)
		print()
		print_rows(f"Destination table: {DEST_TABLE}", destination_rows, DEST_COLUMNS)
		print()
		print("Dry run: no database changes were made.")
		print()
		print_rows(f"Destination table after copy (dry run, unchanged): {DEST_TABLE}", destination_rows, DEST_COLUMNS)
		return 0

	backup_path = backup_destination(DEST_DB)
	print(f"Backup created: {backup_path}")

	print_rows(f"Source table: {SOURCE_TABLE}", source_rows, SOURCE_COLUMNS)
	print()
	print_rows(f"Destination table: {DEST_TABLE}", destination_rows, DEST_COLUMNS)
	print()

	if not args.force and not confirm():
		print("Cancelled.")
		return 0

	with sqlite3.connect(DEST_DB) as conn:
		clear_destination(conn)
		copy_rows(conn, source_rows)
		conn.commit()

	print()
	final_rows = fetch_rows(DEST_DB, DEST_TABLE, DEST_COLUMNS)
	print_rows(f"Destination table after copy: {DEST_TABLE}", final_rows, DEST_COLUMNS)
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))
