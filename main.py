"""
Pesten Score Tracker - BeeWare (Toga) app met MariaDB integratie en spelbeheer

Gebruik:
1. Installeer dependencies:
   pip install toga mysql-connector-python
2. Start je MariaDB-container:
   docker run --name mariadb -e MARIADB_ROOT_PASSWORD=rootpass -e MARIADB_DATABASE=pesten -p 3306:3306 -d mariadb:latest
3. Maak de tabellen aan:
   docker exec -it mariadb mariadb -u root -p pesten
   CREATE TABLE scores (
       id INT AUTO_INCREMENT PRIMARY KEY,
       speler VARCHAR(255),
       wins INT DEFAULT 0
   );
   CREATE TABLE games (
       id INT AUTO_INCREMENT PRIMARY KEY,
       starttijd DATETIME DEFAULT CURRENT_TIMESTAMP
   );
   CREATE TABLE game_players (
       game_id INT,
       speler VARCHAR(255)
   );
4. Run: python pesten_app.py
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import mysql.connector

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'rootpass',
    'database': 'pesten'
}

class PestenApp(toga.App):
    def __init__(self):
        super().__init__('Pesten Tracker', 'org.example.pesten')
        self.conn = None
        self.cursor = None
        self.current_game_id = None

    def startup(self):
        self._connect_db()

        self.main_window = toga.MainWindow(title=self.formal_name)

        self.speler_input = toga.TextInput(placeholder='Naam van speler', style=Pack(padding=5))
        show_scores_button = toga.Button('Toon scores', on_press=self.show_scores, style=Pack(padding=5))
        new_game_button = toga.Button('Nieuw spel', on_press=self.start_new_game, style=Pack(padding=5))

        self.scores_label = toga.Label('Scores komen hier...', style=Pack(padding=10))

        button_box = toga.Box(children=[self.speler_input, show_scores_button, new_game_button], style=Pack(direction=ROW, padding=5))
        main_box = toga.Box(children=[button_box, self.scores_label], style=Pack(direction=COLUMN, padding=10))

        self.main_window.content = main_box
        self.main_window.show()

    def _connect_db(self):
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()

    def start_new_game(self, widget):
        self.cursor.execute("INSERT INTO games () VALUES ()")
        self.conn.commit()
        self.current_game_id = self.cursor.lastrowid
        self.main_window.info_dialog('Nieuw spel', f'Nieuw spel gestart met ID {self.current_game_id}. Voeg nu spelers toe.')

        spelers_str = self.main_window.question_dialog('Spelers toevoegen', 'Voer de spelers in, gescheiden door komma')
        if spelers_str:
            spelers = [s.strip() for s in spelers_str.split(',') if s.strip()]
            for speler in spelers:
                self.cursor.execute("INSERT INTO game_players (game_id, speler) VALUES (%s, %s)", (self.current_game_id, speler))
            self.conn.commit()

    def show_scores(self, widget):
        self.cursor.execute("SELECT speler, wins FROM scores ORDER BY wins DESC")
        rows = self.cursor.fetchall()
        if rows:
            score_text = '\n'.join([f"{speler}: {wins}" for speler, wins in rows])
        else:
            score_text = 'Nog geen scores.'
        self.scores_label.text = score_text

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
