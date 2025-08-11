import os
import json
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import mysql.connector
from mysql.connector import Error
import csv

CONFIG_FILENAME = "db_config.json"

class PestenApp(toga.App):
    def __init__(self):
        super().__init__('Pesten Tracker', 'org.example.pesten')
        self.conn = None
        self.cursor = None
        self.current_game_id = None
        self.selected_players = []
        self.checkboxes = []
        self.open_windows = set()
        self.db_config = {}
        self.config_path = None
        self.app_dir = None  # Wordt ingesteld in startup

    def startup(self):
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        # Stel app_dir in via toga's paths
        self.app_dir = self.paths.app
        os.makedirs(self.app_dir, exist_ok=True)

        self.config_path = os.path.join(self.app_dir, CONFIG_FILENAME)

        if self.load_db_config():
            try:
                self.conn = mysql.connector.connect(**self.db_config)
                self.cursor = self.conn.cursor()
                self.load_main_menu()
                return
            except Error as err:
                self.main_window.info_dialog('Database Fout', f'Kon niet verbinden met opgeslagen database-config:\n{err}')

        self.show_db_config_dialog()

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
            os.makedirs(self.app_dir, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.db_config, f)
        except Exception as e:
            self.main_window.info_dialog('Fout bij opslaan', f'Kon databaseconfig niet opslaan:\n{e}')

    def show_db_config_dialog(self):
        self.host_input = toga.TextInput(placeholder='Host (bijv. 127.0.0.1)', style=Pack(flex=1))
        self.port_input = toga.TextInput(placeholder='Port (bijv. 3306)', style=Pack(flex=1))
        self.user_input = toga.TextInput(placeholder='Gebruiker', style=Pack(flex=1))
        self.password_input = toga.PasswordInput(placeholder='Wachtwoord', style=Pack(flex=1))
        self.database_input = toga.TextInput(placeholder='Database naam', style=Pack(flex=1))

        if self.db_config:
            self.host_input.value = self.db_config.get('host', '')
            self.port_input.value = str(self.db_config.get('port', '3306'))
            self.user_input.value = self.db_config.get('user', '')
            self.password_input.value = self.db_config.get('password', '')
            self.database_input.value = self.db_config.get('database', '')

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

        submit_button = toga.Button('Verbind met database', on_press=self.on_db_config_submit, style=Pack(padding=10))

        main_box = toga.Box(children=[inputs_box, submit_button], style=Pack(direction=COLUMN, padding=10))

        self.main_window.content = main_box
        self.main_window.show()

    def on_db_config_submit(self, widget):
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

        try:
            self.conn = mysql.connector.connect(**self.db_config)
            self.cursor = self.conn.cursor()
        except Error as err:
            self.main_window.info_dialog('Database Fout', f'Kon niet verbinden:\n{err}')
            return

        self.save_db_config()
        self.load_main_menu()

    def load_main_menu(self):
        show_scores_button = toga.Button('Toon scores', on_press=self.show_scores, style=Pack(padding=5))
        new_game_button = toga.Button('Nieuw spel', on_press=self.start_new_game, style=Pack(padding=5))
        export_csv_button = toga.Button('Exporteer spellen (CSV)', on_press=self.export_games_csv, style=Pack(padding=5))

        self.scores_label = toga.Label('Scores komen hier...', style=Pack(padding=10))

        button_box = toga.Box(children=[show_scores_button, new_game_button, export_csv_button], style=Pack(direction=ROW, padding=5))
        main_box = toga.Box(children=[button_box, self.scores_label], style=Pack(direction=COLUMN, padding=10))

        self.main_window.content = main_box
        self.main_window.show()

    def start_new_game(self, widget):
        if not self.cursor:
            self.main_window.info_dialog('Database Fout', 'Geen verbinding met database.')
            return

        self.cursor.execute("SELECT speler FROM scores")
        spelers = [row[0] for row in self.cursor.fetchall()]

        if not spelers:
            self.main_window.info_dialog('Geen spelers', 'Er zijn nog geen spelers in de database.')
            return

        select_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.checkboxes = []
        for speler in spelers:
            cb = toga.Switch(text=speler)
            cb.value = False
            self.checkboxes.append(cb)
            select_box.add(cb)

        button_row = toga.Box(style=Pack(direction=ROW, padding=5))
        start_button = toga.Button('Bevestig spelers', on_press=self.confirm_players, style=Pack(padding=5))
        close_button = toga.Button('Annuleer', on_press=lambda w: self.close_window(select_window), style=Pack(padding=5))
        button_row.add(start_button)
        button_row.add(close_button)

        select_box.add(button_row)

        select_window = toga.Window(title='Selecteer spelers')
        select_window.content = select_box
        select_window.on_close = self.on_window_close

        self.open_windows.add(select_window)
        select_window.show()
        self.select_window = select_window

    def close_window(self, window):
        if window in self.open_windows:
            self.open_windows.remove(window)
        window.close()

    def confirm_players(self, widget):
        self.selected_players = [cb.text for cb in self.checkboxes if cb.value]
        if not self.selected_players:
            self.main_window.info_dialog('Geen selectie', 'Selecteer minstens één speler.')
            return

        self.close_window(self.select_window)

        if not self.cursor:
            self.main_window.info_dialog('Database Fout', 'Geen verbinding met database.')
            return

        # Spelers opslaan als tekst
        spelers_str = ",".join(self.selected_players)
        self.cursor.execute(
            "INSERT INTO games (spelers) VALUES (%s)",
            (spelers_str,)
        )
        self.conn.commit()
        self.current_game_id = self.cursor.lastrowid

        # Venster om winnaar te kiezen
        knop_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        for speler in self.selected_players:
            knop_box.add(toga.Button(speler, on_press=lambda w, s=speler: self.set_winner(s), style=Pack(padding=5)))

        win_window = toga.Window(title='Kies winnaar')
        win_window.content = knop_box
        win_window.on_close = self.on_window_close

        self.open_windows.add(win_window)
        win_window.show()

    def set_winner(self, speler):
        if not self.cursor:
            self.main_window.info_dialog('Database Fout', 'Geen verbinding met database.')
            return

        # Winnaar in scores verhogen
        self.cursor.execute("UPDATE scores SET wins = wins + 1 WHERE speler = %s", (speler,))

        # Winnaar in games-tabel zetten
        self.cursor.execute(
            "UPDATE games SET winnaar = %s WHERE id = %s",
            (speler, self.current_game_id)
        )

        self.conn.commit()
        self.show_scores(None)

    def show_scores(self, widget):
        if not self.cursor:
            self.scores_label.text = 'Geen database verbinding.'
            return

        self.cursor.execute("SELECT speler, wins FROM scores ORDER BY wins DESC")
        rows = self.cursor.fetchall()
        if rows:
            score_text = '\n'.join([f"{speler}: {wins}" for speler, wins in rows])
        else:
            score_text = 'Nog geen scores.'
        self.scores_label.text = score_text

    async def export_games_csv(self, widget):
        if not self.cursor:
            self.main_window.info_dialog('Fout', 'Geen databaseverbinding.')
            return

        self.cursor.execute("SELECT id, spelers, winnaar FROM games ORDER BY id")
        rows = self.cursor.fetchall()

        if not rows:
            self.main_window.info_dialog('Info', 'Er zijn geen gespeelde spellen om te exporteren.')
            return

        file_path = await self.main_window.save_file_dialog(
            title='Sla spellen op als CSV',
            suggested_filename='spellen.csv',
            file_types=['csv']
        )

        if not file_path:
            return  # gebruiker annuleerde

        # Zorg dat we absoluut pad gebruiken
        file_path = os.path.abspath(file_path)

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Spel ID', 'Spelers', 'Winnaar'])
                for spel_id, spelers, winnaar in rows:
                    writer.writerow([spel_id, spelers, winnaar if winnaar else ''])
            self.main_window.info_dialog('Succes', f'Spellen succesvol opgeslagen in {file_path}')
        except Exception as e:
            self.main_window.info_dialog('Fout', f'Kon CSV niet opslaan:\n{e}')

    def on_window_close(self, window):
        if window in self.open_windows:
            self.open_windows.remove(window)
        window.close()
        return True

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
