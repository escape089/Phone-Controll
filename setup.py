from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [
        "json", "shutil", "socket", "subprocess", "sys", "threading", "os", "re", "tkinter", "time",
        "plyer", "psutil", "requests", "pygame", "zipfile", "ctypes", "PIL", "cv2"
    ],
    
    "include_files": [
        # Einzelne Dateien
        ("apktool.jar", "apktool.jar"),
        ("bundletool.jar", "bundletool.jar"),
        ("config.json", "config.json"),
        ("translations.json", "translations.json"),
        ("img", "img"),
        ("platform-tools", "platform-tools"),
        ("tools", "tools"),
        ("app.manifest", "app.manifest")
    ]
}

setup(
    name="ADB_GUI",
    version="1.0",
    description="ADB APP",
    options={"build_exe": build_exe_options},
    executables=[
        Executable("ADB.py", target_name="Phone Controll.exe", icon="img/adb_icon2.ico", manifest="app.manifest"),  # Erste .exe
        Executable("data.py", target_name="Data.exe", icon=r"img\explorer.ico", manifest="app.manifest")  # Zweite .exe
    ]
)
