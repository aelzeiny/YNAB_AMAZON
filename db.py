import datetime as dt
from typing import Optional
from datetime import datetime
import sqlite3
from dataclasses import dataclass


@dataclass
class Run:
    id: Optional[int]
    dttm: datetime
    completion_token_usage: int
    prompt_token_usage: int
    server_knowledge: str

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row[0],
            dttm=datetime.fromisoformat(row[1]),
            prompt_token_usage=row[2],
            completion_token_usage=row[3],
            server_knowledge=row[4],
        )


class RunStore:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS amazon_orders (
                ynab_id TEXT,
                order_id TEXT,
                dttm TIMESTAMP,
                subtotal REAL,
                total REAL,
                created_dttm TIMESTAMP
            )
        """
        )
        self.conn.commit()


    def add_amazon_order(self, ynab_id: str, order_id: str, dttm: datetime, subtotal: float, total: float):
        cursor = self.conn.cursor()
        cursor.execute(
            """\
            INSERT INTO amazon_orders (ynab_id, order_id, dttm, subtotal, total, created_dttm)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (ynab_id, order_id, dttm.isoformat(), subtotal, total, dt.datetime.now().isoformat()),
        )
        self.conn.commit()

    def has_amazon_order(self, order_id: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM amazon_orders WHERE order_id = ?)", (order_id,)
        )
        exists = cursor.fetchone()[0]
        return exists

    def close(self):
        self.conn.close()
