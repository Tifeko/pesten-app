import os
import json
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import pymysql
import sqlite3
from pymysql import MySQLError

CONFIG_FILENAME = "db_config.json"

class PestenApp(toga.App):
    def __init__(self):
        super().__init__('Pesten Tracker', 'org.example.pesten')
        self.conn = None
        self.cursor = None
        self.current_game_id = None
        self.selected_players = []
        self.checkboxes = []
        self.db_type = None  # "mysql" of "sqlite"
        self.app_dir = None
        self.config_path = None
        self.db_config = {}

    def startup(self):
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.app_dir = self.paths.app
        os.makedirs(self.app_dir, exist_ok=True)
        self.config_path = os.path.join(self.app_dir, CONFIG_FILENAME)

        # Probeer opgeslagen MySQL config te laden en verbinden
        if self.load_db_config():
            if self.try_connect_mysql():
                self.db_type = "mysql"
                self.show_main_screen()
                self.main_window.show()
                return
            else:
                self.main_window.info_dialog('Database Fout', 'Kon niet verbinden met opgeslagen MySQL-config.')

        # Toon keuze scherm (MySQL/SQLite) of MySQL config scherm
        self.show_db_choice_screen()
        self.main_window.show()

    def load_db_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.db_config = json.load(f)
                return True
            except Exception:
                return False
        return False

    def save_db_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.db_config, f)
        except Exception as e:
            self.main_window.info_dialog('Fout bij opslaan', f'Kon databaseconfig niet opslaan:\n{e}')

    def try_connect_mysql(self):
        try:
            self.conn = pymysql.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            # Zorg dat de games tabel kolommen heeft voor spelers en winnaar
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    spelers TEXT NOT NULL,
                    winnaar VARCHAR(255)
                )
            """)
            self.conn.commit()
            return True
        except MySQLError:
            self.conn = None
            self.cursor = None
            return False

    def show_db_choice_screen(self, widget=None):
        label = toga.Label("Kies database:", style=Pack(padding=10))
        mysql_button = toga.Button('MySQL / MariaDB', on_press=self.show_mysql_config_screen, style=Pack(padding=5))
        sqlite_button = toga.Button('SQLite', on_press=self.select_sqlite, style=Pack(padding=5))

        box = toga.Box(children=[label, mysql_button, sqlite_button], style=Pack(direction=COLUMN, padding=20))
        self.main_window.content = box

    def show_mysql_config_screen(self, widget=None):
        # Vul standaardvelden uit config indien beschikbaar
        host = self.db_config.get('host', '127.0.0.1')
        port = str(self.db_config.get('port', 3306))
        user = self.db_config.get('user', '')
        password = self.db_config.get('password', '')
        database = self.db_config.get('database', '')

        self.host_input = toga.TextInput(value=host, placeholder='Host (bijv. 127.0.0.1)', style=Pack(flex=1))
        self.port_input = toga.TextInput(value=port, placeholder='Port (bijv. 3306)', style=Pack(flex=1))
        self.user_input = toga.TextInput(value=user, placeholder='Gebruiker', style=Pack(flex=1))
        self.password_input = toga.PasswordInput(value=password, placeholder='Wachtwoord', style=Pack(flex=1))
        self.database_input = toga.TextInput(value=database, placeholder='Database naam', style=Pack(flex=1))

        inputs_box = toga.Box(
            children=[
                toga.Label('Host:'), self.host_input,
                toga.Label('Port:'), self.port_input,
                toga.Label('Gebruiker:'), self.user_input,
                toga.Label('Wachtwoord:'), self.password_input,
                toga.Label('Database:'), self.database_input,
            ],
            style=Pack(direction=COLUMN, padding=10, flex=1)
        )

        submit_button = toga.Button('Verbind met database', on_press=self.on_mysql_config_submit, style=Pack(padding=10))
        back_button = toga.Button('Terug', on_press=self.show_db_choice_screen, style=Pack(padding=10))

        buttons = toga.Box(children=[submit_button, back_button], style=Pack(direction=ROW, padding=10))

        main_box = toga.Box(children=[inputs_box, buttons], style=Pack(direction=COLUMN, padding=10))
        self.main_window.content = main_box

    def on_mysql_config_submit(self, widget):
        host = self.host_input.value.strip()
        port_str = self.port_input.value.strip()
        user = self.user_input.value.strip()
        password = self.password_input.value.strip()
        database = self.database_input.value.strip()

        if not (host and port_str and user and database):
            self.main_window.info_dialog('Fout', 'Vul alle velden in behalve wachtwoord.')
            return

        try:
            port = int(port_str)
        except ValueError:
            self.main_window.info_dialog('Fout', 'Poort moet een getal zijn.')
            return

        self.db_config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }

        if not self.try_connect_mysql():
            self.main_window.info_dialog('Database Fout', 'Kon niet verbinden met MySQL met opgegeven gegevens.')
            return

        self.save_db_config()
        self.db_type = "mysql"
        self.show_main_screen()

    def select_sqlite(self, widget=None):
        self.db_type = "sqlite"
        try:
            self.conn = sqlite3.connect(os.path.join(self.app_dir, 'pesten.sqlite3'))
            self.cursor = self.conn.cursor()
            self._setup_sqlite()
        except sqlite3.Error as err:
            self.conn = None
            self.cursor = None
            self.main_window.info_dialog('Database Fout', f'Kon niet verbinden met SQLite:\n{err}')
            return
        self.show_main_screen()

    def _setup_sqlite(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            speler TEXT PRIMARY KEY,
            wins INTEGER DEFAULT 0
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            spelers TEXT NOT NULL,
            winnaar TEXT
        )
        """)
        self.conn.commit()

    def show_main_screen(self, widget=None):
        show_scores_button = toga.Button('Toon scores', on_press=self.show_scores, style=Pack(padding=5))
        new_game_button = toga.Button('Nieuw spel', on_press=self.show_new_game_screen, style=Pack(padding=5))

        self.scores_label = toga.Label('Scores komen hier...', style=Pack(padding=10))

        button_box = toga.Box(children=[show_scores_button, new_game_button], style=Pack(direction=ROW, padding=5))
        main_box = toga.Box(children=[button_box, self.scores_label], style=Pack(direction=COLUMN, padding=10))

        self.main_window.content = main_box
        self.show_scores(None)

    def show_new_game_screen(self, widget=None):
        if not self.cursor:
            self.main_window.info_dialog('Database Fout', 'Geen verbinding met database.')
            return

        self.cursor.execute("SELECT speler FROM scores")
        spelers = [row[0] for row in self.cursor.fetchall()]

        if not spelers:
            self.main_window.info_dialog('Geen spelers', 'Voeg eerst spelers toe in de database.')
            return

        select_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.checkboxes = []
        for speler in spelers:
            cb = toga.Switch(text=speler, value=False)
            self.checkboxes.append(cb)
            select_box.add(cb)

        button_row = toga.Box(style=Pack(direction=ROW, padding=5))
        confirm_button = toga.Button('Bevestig spelers', on_press=self.confirm_players, style=Pack(padding=5))
        cancel_button = toga.Button('Annuleer', on_press=self.show_main_screen, style=Pack(padding=5))
        button_row.add(confirm_button)
        button_row.add(cancel_button)

        select_box.add(button_row)
        self.main_window.content = select_box

    def confirm_players(self, widget):
        self.selected_players = [cb.text for cb in self.checkboxes if cb.value]
        if not self.selected_players:
            self.main_window.info_dialog('Geen selectie', 'Selecteer minstens één speler.')
            return

        if not self.cursor:
            self.main_window.info_dialog('Database Fout', 'Geen verbinding met database.')
            return

        spelers_str = ",".join(self.selected_players)
        if self.db_type == "sqlite":
            self.cursor.execute("INSERT INTO games (spelers) VALUES (?)", (spelers_str,))
        else:
            self.cursor.execute("INSERT INTO games (spelers) VALUES (%s)", (spelers_str,))
        self.conn.commit()
        self.current_game_id = self.cursor.lastrowid

        knop_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        for speler in self.selected_players:
            knop_box.add(toga.Button(speler, on_press=lambda w, s=speler: self.set_winner(s), style=Pack(padding=5)))

        back_button = toga.Button('Terug naar scores', on_press=self.show_main_screen, style=Pack(padding=5))
        knop_box.add(back_button)

        self.main_window.content = knop_box

    def set_winner(self, speler):
        if not self.cursor:
            self.main_window.info_dialog('Database Fout', 'Geen verbinding met database.')
            return

        if self.db_type == "sqlite":
            self.cursor.execute("UPDATE scores SET wins = wins + 1 WHERE speler = ?", (speler,))
            self.cursor.execute("UPDATE games SET winnaar = ? WHERE id = ?", (speler, self.current_game_id))
        else:
            self.cursor.execute("UPDATE scores SET wins = wins + 1 WHERE speler = %s", (speler,))
            self.cursor.execute("UPDATE games SET winnaar = %s WHERE id = %s", (speler, self.current_game_id))

        self.conn.commit()
        self.show_scores(None)

    def show_scores(self, widget=None):
        if not self.cursor:
            self.scores_label.text = 'Geen database verbinding.'
            return

        # Haal spelers en wins op
        self.cursor.execute("SELECT speler, wins FROM scores ORDER BY wins DESC")
        rows = self.cursor.fetchall()

        if not rows:
            self.scores_label.text = 'Nog geen scores.'
            return

        score_texts = []
        for speler, wins in rows:
            # Tel hoeveel potjes de speler heeft gespeeld
            if self.db_type == "sqlite":
                self.cursor.execute(
                    "SELECT COUNT(*) FROM games WHERE instr(spelers, ?) > 0",
                    (speler,)
                )
            else:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM games WHERE FIND_IN_SET(%s, spelers)",
                    (speler,)
                )
            games_played = self.cursor.fetchone()[0]


            if not wins == 0 or not games_played == 0:
                percentage = (wins / games_played) * 100
            else:
                percentage = 0.00000
            score_texts.append(f"{speler}: {wins} / {games_played} - {percentage:.1f}%")

        self.scores_label.text = "\n".join(score_texts)

    def on_exit(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

def main():
    return PestenApp()

if __name__ == '__main__':
    app = main()
    app.main_loop()
