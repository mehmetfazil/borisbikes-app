import os
from dotenv import load_dotenv
import sqlitecloud

class DB:
    def __init__(self):
        load_dotenv()
        sqlite_conn_str = os.environ.get("SQLITECLOUD_CONN_STR")
        self.conn = sqlitecloud.connect(sqlite_conn_str)

    def get_station_data(self, terminal_name):
        query = f"""
        SELECT
            last_update,
            nb_ebikes,
            nb_standard_bikes,
            nb_empty_docks
        FROM
            livecyclehireupdates
        WHERE
            terminal_name = '{terminal_name}';"""
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
    def get_latest_station_data(self, terminal_name):
        query = f"""
        SELECT
            last_update,
            nb_ebikes,
            nb_standard_bikes,
            nb_empty_docks
        FROM
            livecyclehireupdates
        WHERE
            terminal_name = '{terminal_name}'
        ORDER BY last_update DESC
        LIMIT 1;"""
        cursor = self.conn.execute(query)
        return cursor.fetchone()

    def get_all_stations(self):
        query = """
        SELECT DISTINCT
            terminal_name
        FROM
            livecyclehireupdates;"""
        cursor = self.conn.execute(query)
        return [row[0] for row in cursor.fetchall()]

    def close(self):
        self.conn.close()
