from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [],  # Liste der benötigten Pakete
    "include_files": [
        # Einzelne Dateien
        ("apktool.jar", "apktool.jar"),
        ("bundletool.jar", "bundletool.jar"),
        ("config.json", "config.json"),
        ("translations.json", "translations.json"),
        ("img", "img"),
        ("platform-tools", "platform-tools"),
        ("tools", "tools")
    ]
}

setup(
    name="ADB_GUI",
    version="1.0",
    description="This is an ADB program with a GUI",
    options={"build_exe": build_exe_options},
    executables=[
        Executable("ADB.pyw", target_name="ADB_GUI.exe", icon="img/adb_icon2.ico"),  # Erste .exe
        Executable("data.pyw", target_name="Data.exe")  # Zweite .exe
    ]
)
