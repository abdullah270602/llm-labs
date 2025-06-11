import logging
import os
import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection as PGConnection
from typing import Optional

logger = logging.getLogger(__name__)

class PostgresConnection:
    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[str] = None,
        database: Optional[str] = None
    ) -> None:
        self._user = user or os.getenv("DB_USER")
        self._password = password or os.getenv("DB_PASSWORD")
        self._host = host or os.getenv("BRANCH_DB_HOST")
        self._port = port or os.getenv("DB_PORT")
        self._database = database or os.getenv("DB_NAME")
        self._connection: Optional[PGConnection] = None

    def __enter__(self) -> PGConnection:
        self.connect()
        return self._connection

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close_connection()

    def connect(self) -> None:
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(
                    user=self._user,
                    password=self._password,
                    host=self._host,
                    port=self._port,
                    database=self._database,
                    sslmode="require",
                )
                logger.info("Connection established successfully.")
            except psycopg2.Error as e:
                logger.error(f"Error connecting to PostgreSQL: {e}")
                raise

    def close_connection(self) -> None:
        if self._connection and not self._connection.closed:
            try:
                self._connection.close()
                logger.info("Connection closed successfully.")
            except psycopg2.Error as e:
                logger.error(f"Error while closing the connection: {e}")
                raise
