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
        self.selected_players = []

    def startup(self):
        self._connect_db()

        self.main_window = toga.MainWindow(title=self.formal_name)

        show_scores_button = toga.Button('Toon scores', on_press=self.show_scores, style=Pack(padding=5))
        new_game_button = toga.Button('Nieuw spel', on_press=self.start_new_game, style=Pack(padding=5))

        self.scores_label = toga.Label('Scores komen hier...', style=Pack(padding=10))

        button_box = toga.Box(children=[show_scores_button, new_game_button], style=Pack(direction=ROW, padding=5))
        main_box = toga.Box(children=[button_box, self.scores_label], style=Pack(direction=COLUMN, padding=10))

        self.main_window.content = main_box
        self.main_window.show()

    def _connect_db(self):
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()

    def on_window_close(self, window):
        print(f"Window '{window.title}' wordt gesloten via kruisje!")
        if window in self.windows:
            self.windows.remove(window)
        window.close()
        return True  # Sta toe dat window sluit

    def start_new_game(self, widget):
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
        select_window.on_close = self.on_window_close  # Directe verwijzing, geen lambda!

        self.windows.add(select_window)
        select_window.show()
        self.select_window = select_window

    def close_window(self, window):
        if window in self.windows:
            self.windows.remove(window)
        window.close()

    def confirm_players(self, widget):
        self.selected_players = [cb.text for cb in self.checkboxes if cb.value]
        if not self.selected_players:
            self.main_window.info_dialog('Geen selectie', 'Selecteer minstens één speler.')
            return

        self.close_window(self.select_window)

        self.cursor.execute("INSERT INTO games () VALUES ()")
        self.conn.commit()
        self.current_game_id = self.cursor.lastrowid

        knop_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        for speler in self.selected_players:
            knop_box.add(toga.Button(speler, on_press=lambda w, s=speler: self.set_winner(s), style=Pack(padding=5)))

        win_window = toga.Window(title='Kies winnaar')
        win_window.content = knop_box
        win_window.on_close = self.on_window_close  # Ook hier

        self.windows.add(win_window)
        win_window.show()

    def set_winner(self, speler):
        self.cursor.execute("UPDATE scores SET wins = wins + 1 WHERE speler = %s", (speler,))
        self.conn.commit()
        self.show_scores(None)

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
