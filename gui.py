import json
import tkinter as tk
from tkinter import messagebox, ttk

class App:
    CONFIG_FILE = "config.json"  # Datei für die Spracheinstellungen

    def __init__(self, root):
        self.root = root
        self.root.geometry("400x200")
        
        # Sprache aus Konfigurationsdatei laden oder Standard auf Deutsch setzen
        self.language_code = self.load_language_setting()
        
        # Übersetzungen und Texte laden
        self.translations = self.load_translations()
        self.texts = self.get_texts(self.language_code)

        # GUI-Elemente erstellen
        self.create_widgets()
        self.update_texts()  # Texte basierend auf der Sprache anwenden

    def load_language_setting(self):
        # Versuche, die Sprache aus der Konfigurationsdatei zu laden
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("language", "de")  # Standardmäßig Deutsch, wenn nichts gesetzt ist
        except (FileNotFoundError, json.JSONDecodeError):
            return "de"  # Standardmäßig Deutsch

    def save_language_setting(self):
        # Speichere die aktuelle Sprache in der Konfigurationsdatei
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"language": self.language_code}, f)

    def load_translations(self):
        # Lade alle Übersetzungen aus der JSON-Datei
        with open("translations.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def get_texts(self, language_code):
        # Übersetzungen für die ausgewählte Sprache zurückgeben
        return self.translations.get(language_code, self.translations["en"])  # Fallback auf Englisch

    def switch_language(self, event=None):
        # Sprache basierend auf Auswahl im Dropdown wechseln
        self.language_code = self.language_var.get()
        self.texts = self.get_texts(self.language_code)
        self.update_texts()  # Texte aktualisieren
        self.save_language_setting()  # Spracheinstellung speichern

    def update_texts(self):
        # Texte der UI-Elemente basierend auf `self.texts` aktualisieren
        self.root.title(self.texts["title"])
        self.greeting_label.config(text=self.texts["greeting_label_text"])
        self.language_label.config(text=self.texts["language_label_text"])
        self.change_lang_button.config(text=self.texts["change_language_button_text"])
        self.example_button.config(text=self.texts["example_button_text"])
        self.menu.entryconfig(0, label=self.texts["menu_option_1_text"])
        self.menu.entryconfig(1, label=self.texts["menu_option_2_text"])

    def show_message(self):
        # Beispielnachricht anzeigen
        messagebox.showinfo(self.texts["message_title"], self.texts["message_content"])

    def create_widgets(self):
        # Beispiel-Label und Button
        self.greeting_label = tk.Label(self.root, text="")
        self.greeting_label.pack(pady=10)
        
        self.language_label = tk.Label(self.root, text="")
        self.language_label.pack()
        
        # Dropdown-Menü für die Sprachauswahl
        self.language_var = tk.StringVar(value=self.language_code)
        self.language_dropdown = ttk.Combobox(self.root, textvariable=self.language_var, values=list(self.translations.keys()))
        self.language_dropdown.bind("<<ComboboxSelected>>", self.switch_language)
        self.language_dropdown.pack(pady=5)
        
        # Buttons
        self.change_lang_button = tk.Button(self.root, text="", command=self.switch_language)
        self.change_lang_button.pack(pady=5)
        
        self.example_button = tk.Button(self.root, text="", command=self.show_message)
        self.example_button.pack(pady=5)

        # Menü mit Optionen erstellen
        menubar = tk.Menu(self.root)
        self.menu = tk.Menu(menubar, tearoff=0)
        self.menu.add_command(label="", command=lambda: print("Option 1 selected"))
        self.menu.add_command(label="", command=lambda: print("Option 2 selected"))
        menubar.add_cascade(label="Options", menu=self.menu)
        self.root.config(menu=menubar)

# Hauptprogramm starten
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
