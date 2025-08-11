import json
import pymysql
from pymysql import MySQLError

CONFIG_FILENAME = 'db_config.json'

def load_db_config():
    try:
        with open(CONFIG_FILENAME, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Kon config bestand '{CONFIG_FILENAME}' niet laden: {e}")
        return None

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            speler VARCHAR(255) PRIMARY KEY,
            wins INT DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INT AUTO_INCREMENT PRIMARY KEY
        )
    """)
    conn.commit()
    cursor.close()
    print("Tabellen aangemaakt of bestaan al.")

def add_players(conn):
    cursor = conn.cursor()
    while True:
        speler = input("Voeg een speler toe (of leeg laten om te stoppen): ").strip()
        if not speler:
            break

        # Check of speler al bestaat
        cursor.execute("SELECT COUNT(*) FROM scores WHERE speler = %s", (speler,))
        exists = cursor.fetchone()[0]
        if exists:
            print(f"Speler '{speler}' bestaat al.")
            continue

        cursor.execute("INSERT INTO scores (speler, wins) VALUES (%s, 0)", (speler,))
        conn.commit()
        print(f"Speler '{speler}' toegevoegd.")

    cursor.close()

def main():
    config = load_db_config()
    if not config:
        print("Stoppen omdat geen config beschikbaar is.")
        return

    try:
        conn = pymysql.connect(**config)
    except MySQLError as e:
        print(f"Kon niet verbinden met database: {e}")
        return

    create_tables(conn)
    add_players(conn)
    conn.close()
    print("Klaar.")

if __name__ == "__main__":
    main()
