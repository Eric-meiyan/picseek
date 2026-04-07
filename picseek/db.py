import os
import sqlite3
import struct
import time


def serialize_f32(vector: list[float]) -> bytes:
    return struct.pack("%sf" % len(vector), *vector)


class Database:
    def __init__(self, db_path: str):
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._load_sqlite_vec()
        self._init_tables()

    def _load_sqlite_vec(self) -> None:
        import sqlite_vec
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)

    def _init_tables(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_size INTEGER,
                modified_at REAL,
                indexed_at REAL
            )
        """)
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_images USING vec0(
                id INTEGER PRIMARY KEY,
                embedding float[512]
            )
        """)
        self.conn.commit()

    def insert_image(self, file_path: str, file_size: int, modified_at: float, embedding: list[float]) -> int:
        cursor = self.conn.execute(
            "INSERT INTO images (file_path, file_size, modified_at, indexed_at) VALUES (?, ?, ?, ?)",
            [file_path, file_size, modified_at, time.time()],
        )
        row_id = cursor.lastrowid
        self.conn.execute(
            "INSERT INTO vec_images (id, embedding) VALUES (?, ?)",
            [row_id, serialize_f32(embedding)],
        )
        self.conn.commit()
        return row_id

    def update_image(self, file_path: str, file_size: int, modified_at: float, embedding: list[float]) -> None:
        record = self.get_image(file_path)
        if record is None:
            return
        row_id = record["id"]
        self.conn.execute(
            "UPDATE images SET file_size=?, modified_at=?, indexed_at=? WHERE id=?",
            [file_size, modified_at, time.time(), row_id],
        )
        self.conn.execute("DELETE FROM vec_images WHERE id=?", [row_id])
        self.conn.execute(
            "INSERT INTO vec_images (id, embedding) VALUES (?, ?)",
            [row_id, serialize_f32(embedding)],
        )
        self.conn.commit()

    def delete_image(self, file_path: str) -> None:
        record = self.get_image(file_path)
        if record is None:
            return
        row_id = record["id"]
        self.conn.execute("DELETE FROM vec_images WHERE id=?", [row_id])
        self.conn.execute("DELETE FROM images WHERE id=?", [row_id])
        self.conn.commit()

    def get_image(self, file_path: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM images WHERE file_path=?", [file_path]
        ).fetchone()
        return dict(row) if row else None

    def get_all_records(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM images").fetchall()
        return [dict(r) for r in rows]

    def search(self, query_vector: list[float], limit: int = 10) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT v.id, v.distance, i.file_path, i.file_size
            FROM vec_images v
            JOIN images i ON i.id = v.id
            WHERE v.embedding MATCH ?
              AND k = ?
            ORDER BY v.distance
            """,
            [serialize_f32(query_vector), limit],
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()
