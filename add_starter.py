# migrate_add_starter.py
import os
import json
import mysql.connector
from mysql.connector import Error

CONFIG_FILENAME = "db_config.json"

def main():
    config_path = os.path.join(os.getcwd(), CONFIG_FILENAME)
    if not os.path.exists(config_path):
        print(f"Configuratiebestand niet gevonden in huidige map: {config_path}")
        return

    # Config laden
    with open(config_path, "r") as f:
        db_config = json.load(f)

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check of kolom bestaat
        cursor.execute("SHOW COLUMNS FROM games LIKE 'starter'")
        result = cursor.fetchone()
        if result:
            print("Kolom 'starter' bestaat al. Geen wijzigingen nodig.")
        else:
            cursor.execute("ALTER TABLE games ADD COLUMN starter VARCHAR(255)")
            conn.commit()
            print("Kolom 'starter' succesvol toegevoegd.")

        cursor.close()
        conn.close()
    except Error as err:
        print(f"Database fout: {err}")

if __name__ == "__main__":
    main()
