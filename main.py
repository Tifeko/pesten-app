"""
Pesten Score Tracker - een BeeWare (Toga) app met MariaDB integratie

Gebruik:
1. Installeer dependencies:
   pip install toga mysql-connector-python
2. Zorg dat MariaDB draait en dat je database en tabel bestaan:
   CREATE DATABASE pesten;
   USE pesten;
   CREATE TABLE scores (
       id INT AUTO_INCREMENT PRIMARY KEY,
       speler VARCHAR(255),
       wins INT DEFAULT 0
   );
3. Run: python pesten_app.py
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'rootpass',
    'database': 'pesten'
}

class PestenApp(toga.App):
    def __init__(self):
        super().__init__('Pesten Tracker', 'org.example.pesten')
        self.conn = None
        self.cursor = None

    def startup(self):
        self._connect_db()

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.speler_input = toga.TextInput(placeholder='Naam van speler', style=Pack(padding=5))
        add_win_button = toga.Button('Voeg winst toe', on_press=self.add_win, style=Pack(padding=5))
        show_scores_button = toga.Button('Toon scores', on_press=self.show_scores, style=Pack(padding=5))

        self.scores_label = toga.Label('Scores komen hier...', style=Pack(padding=10))

        button_box = toga.Box(children=[self.speler_input, add_win_button, show_scores_button], style=Pack(direction=ROW, padding=5))
        main_box = toga.Box(children=[button_box, self.scores_label], style=Pack(direction=COLUMN, padding=10))

        self.main_window.content = main_box
        self.main_window.show()

    def _connect_db(self):
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()

    def add_win(self, widget):
        speler = self.speler_input.value.strip()
        if not speler:
            self.main_window.info_dialog('Fout', 'Voer een spelersnaam in.')
            return

        self.cursor.execute("SELECT wins FROM scores WHERE speler = %s", (speler,))
        result = self.cursor.fetchone()
        if result:
            self.cursor.execute("UPDATE scores SET wins = wins + 1 WHERE speler = %s", (speler,))
        else:
            self.cursor.execute("INSERT INTO scores (speler, wins) VALUES (%s, %s)", (speler, 1))
        self.conn.commit()
        self.main_window.info_dialog('Winst toegevoegd', f'{speler} heeft nu een extra winst!')
        self.speler_input.value = ''

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
