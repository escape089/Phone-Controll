from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [],  # hier kannst du deine benötigten Pakete auflisten
    "include_files": [
        ("", "."),  # kopiert die Datei ins Hauptverzeichnis
        ("dein_ordner", "dein_ordner")  # kopiert den Ordner ins Hauptverzeichnis
    ],
}

setup(
    name="MeinProgramm",
    version="1.0",
    description="Beschreibung deines Programms",
    options={"build_exe": build_exe_options},
    executables=[Executable("dein_skriptname.py")]
)
