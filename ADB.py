import json
import shutil
import socket
import subprocess
import sys
from threading import Thread
import os
import re
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext, filedialog
import threading
import time
from plyer import notification 
import psutil
import requests
import pygame
import zipfile
import ctypes
from PIL import Image, ImageTk
from tkinter import PhotoImage
import cv2

ADB_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
ADB_FOLDER = "platform-tools"
adb_path = r"platform-tools\adb.exe"

class ProgramRestarter:
    def __init__(self, program_path):
        self.program_path = program_path
        self.program_name = os.path.basename(program_path)

    def is_program_running(self):
        """Überprüfen, ob das Programm läuft."""
        for process in psutil.process_iter(['name']):
            if process.info['name'] == self.program_name:
                return True
        return False

    def restart_program(self):
        """Starte das Programm neu, wenn es bereits läuft."""
        if self.is_program_running():
            for process in psutil.process_iter(['name']):
                if process.info['name'] == self.program_name:
                    print(f"{self.program_name} läuft bereits und wird beendet.")
                    process.terminate()  # Beenden des laufenden Prozesses
                    process.wait()  # Warten, bis der Prozess beendet ist
            
            print(f"Starte {self.program_name} neu...")
            subprocess.Popen([self.program_path])  # Starte das Programm neu
        else:
            print(f"{self.program_name} läuft nicht. Kein Neustart erforderlich.")
            return False  # Programm ist nicht gestartet


def load_main_program():
    pass

# Funktion zum Abspielen des Willkommensvideos
def play_welcome_screen():
    # Videoquelle und Pfad
    video_path = r"img\Willkommen_Screen.mp4"
    cap = cv2.VideoCapture(video_path)

    # Überprüfen, ob das Video erfolgreich geladen wurde
    if not cap.isOpened():
        
        exit()

    # Videogröße bestimmen
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Erstelle ein rahmenloses Fenster in Pygame
    screen = pygame.display.set_mode((video_width, video_height), pygame.NOFRAME)
    pygame.display.set_caption("Willkommen")

    # Frame-Rate des Videos
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_duration = 1 / fps  # Dauer eines Frames

    # Schleife zum Abspielen des Videos
    running = True
    while running:
        ret, frame = cap.read()  # Nächsten Frame lesen
        if not ret:
            break  # Beende die Schleife, wenn das Video zu Ende ist

        # Konvertiere den Frame von OpenCV (BGR) in Pygame (RGB)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))  # Konvertiere in Pygame-Oberfläche

        # Zeige den Frame in Pygame an
        screen.blit(frame, (0, 0))
        pygame.display.update()

        # Überprüfen, ob Escape gedrückt wurde oder das Fenster geschlossen wird
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Schließen, wenn ESC gedrückt wird
                    running = False

        # Warte die entsprechende Zeit basierend auf der Frame-Rate
        time.sleep(frame_duration)

    # Videoquelle freigeben und Pygame beenden
    cap.release()
    pygame.quit()



# Initialisiere Pygame
pygame.init()

# Starte das Hauptprogramm im Hintergrund
main_program_thread = threading.Thread(target=load_main_program)
main_program_thread.start()

# Spiele den Willkommensbildschirm ab (dieser blockiert den Hauptthread)
play_welcome_screen()

# Warten, bis das Hauptprogramm geladen wurde, bevor es startet
main_program_thread.join()

# Hier kannst du dein Hauptprogramm nach dem Willkommensbildschirm starten

load_main_program()

class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="", validate_func=None, **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.validate_func = validate_func  # Die Validierungsfunktion übergeben
        self.placeholder_active = False
        self.bind("<FocusIn>", self.clear_placeholder)
        self.bind("<FocusOut>", self.set_placeholder)
        self.set_placeholder()  # Setze den Platzhalter beim Start

        self.validate_command = master.register(self.validate_input)

        # Aktivierung der Validierung
        self.config(validate="key", validatecommand=(self.validate_command, '%P'))

    def clear_placeholder(self, event=None):
        if self.placeholder_active:
            self.delete(0, tk.END)
            self.config(fg='black')  # Setze die Schriftfarbe auf schwarz
            self.placeholder_active = False

    def set_placeholder(self, event=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(fg='gray')  # Setze die Schriftfarbe auf grau
            self.placeholder_active = True


    def validate_input(self, new_value):
        if self.placeholder_active:
            return True  # Wenn der Placeholder aktiv ist, keine Validierung durchführen
        if self.validate_func:
            return self.validate_func(new_value)  # Validierung auf Zahlen durchführen
        return True



class TWRPBackupRestoreApp:
    CONFIG_FILE = "config.json" 

    def __init__(self, master):
        self.master = master
        self.master.title("Phone Controll - Home")
        self.master.geometry("1000x740")
        self.search_var = tk.StringVar()
        self.apktool_path = r"apktool.jar"
        
        self.icon = PhotoImage(file="img/android.png")  # Pfad zu deinem Icon-Bild
        self.master.iconphoto(False, self.icon)
        
        self.adb_path = r"platform-tools\adb.exe"

        self.bundletool_path = r"bundletool.jar"
       
        self.apps = []
        self.device_label = None

        #Images

        self.magisk_folder_path = r"tools/Magisk"  # Pfad zum Magisk-Ordner
        
        # Initialisiere Boot-Image-Pfad
        self.boot_image_path = ""

        self.refrash_img = Image.open(r"img\refresh.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.refresh_ico = ImageTk.PhotoImage(self.refrash_img)

        self.yes_img = Image.open(r"img\yes.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.yes_ico = ImageTk.PhotoImage(self.yes_img)

        self.screen_img = Image.open(r"img\screen.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.screen_ico = ImageTk.PhotoImage(self.screen_img)


        self.müll_img = Image.open(r"img\müll.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.müll_ico = ImageTk.PhotoImage(self.müll_img)

        self.home_img = Image.open(r"img\home.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.home_ico = ImageTk.PhotoImage(self.home_img)

        self.Power_img = Image.open(r"img\Power.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.Power_ico = ImageTk.PhotoImage(self.Power_img)

        self.bluetooth_img = Image.open(r"img\bluetooth.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.bluetooth_ico = ImageTk.PhotoImage(self.bluetooth_img)

        self.explorer_img = Image.open(r"img\explorer.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.explorer_ico = ImageTk.PhotoImage(self.explorer_img)

        self.wifi_img = Image.open(r"img\wifi.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.wifi_ico = ImageTk.PhotoImage(self.wifi_img)

        self.gps_img = Image.open(r"img\gps.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.gps_ico = ImageTk.PhotoImage(self.gps_img)

        self.data_img = Image.open(r"img\data.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.data_ico = ImageTk.PhotoImage(self.data_img)

        self.hotspot_img = Image.open(r"img\hotspot.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.hotspot_ico = ImageTk.PhotoImage(self.hotspot_img)


        self.info_img = Image.open(r"img\info.png")  # Ersetze mit dem Pfad zu deinem Bild
        self.info_ico = ImageTk.PhotoImage(self.info_img)



        # Dunkelmodus
        self.set_dark_mode()

        self.backup_folder_path = None
        self.countdown_timer = 0
        self.is_countdown_running = False
        self.previous_device_info = ""

        # Checkbuttons für Partitionen
        self.partition_vars = {}
        self.partitions = ['boot', 'system', 'vendor', 'super', 'system', 'recovery', 'up_param', 'vbmeta']
        
        # Dictionary, um den Status der Checkboxen zu speichern
        self.partitions_vars = {partition: tk.BooleanVar() for partition in self.partitions}
        
        # Frame für die Checkbox-Liste
        
        
       
        

        self.buttons = tk.Frame(master, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.buttons.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.45)


        self.backup_frame = tk.Frame(master, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.backup_frame.place_forget()

        


        self.backup_sel_frame = tk.Frame(self.backup_frame, bg="black",relief=tk.SUNKEN,  borderwidth=2, height=30)
        self.backup_sel_frame.pack(side="top", fill="x")

        self.backup_twrp_frame = tk.Frame(self.backup_frame, bg="#221C22", relief=tk.SUNKEN, borderwidth=2)
        self.backup_twrp_frame.place(relx=0.1, rely=0.15, relwidth=0.8, relheight=0.8)

        self.backup_dd_frame = tk.Frame(self.backup_frame, bg="#221C22", relief=tk.SUNKEN, borderwidth=2)
        self.backup_dd_frame.place_forget()

        #self.backup_adb_frame = tk.Frame(self.backup_frame, bg="#221C22", relief=tk.SUNKEN, borderwidth=2)
        #self.backup_adb_frame.place(relx=0.1, rely=0.1, relwidth=0.8, relheight=0.8)
        
        #self.backup_adb_root_frame = tk.Frame(self.backup_frame, bg="#221C22", relief=tk.SUNKEN, borderwidth=2)
        #self.backup_adb_root_frame.place(relx=0.1, rely=0.1, relwidth=0.8, relheight=0.8)

        self.open_twrp_frame = tk.Button(self.backup_sel_frame, bg="#2C2C2C", text="", command=self.open_twrp)
        self.open_twrp_frame.pack(side="left", fill="both")

        self.open_dd_frame = tk.Button(self.backup_sel_frame, bg="#2C2C2C", text="", command=self.open_dd)
        self.open_dd_frame.pack(side="left", fill="both", padx=10)

        ## Busybox Backup ##################################################################################################

        self.program_path = 'Data.exe'  # Pfad zu deinem externen Programm
        self.restarter = ProgramRestarter(self.program_path)
        

        self.ddbackupbox = tk.Listbox(self.backup_dd_frame, selectmode=tk.MULTIPLE, height=10, bg="black", fg="White")
        self.ddbackupbox.place(relx=0.05, rely=0.05, relwidth=0.9)

        self.save_dd_button = tk.Button(self.backup_dd_frame, text="", command=self.save_selected_partitions)
        self.save_dd_button.place(relx=0.5, rely=0.75, anchor='center')

        self.restore_dd_button = tk.Button(self.backup_dd_frame, text="", command=self.restore_selected_partitions)
        self.restore_dd_button.place(relx=0.5, rely=0.85, anchor='center')

        self.progress_bar = ttk.Progressbar(self.backup_dd_frame, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.place(relx=0.5, rely=0.95, anchor='center')
        
        self.is_busybox_installed 
        self.load_partitions()

        ########### Batterie #################################################################

        # Canvas für das Batteriesymbol
        self.canvas = tk.Canvas(master, width=60, height=30, background="#2C2C2C", highlightthickness=0, cursor="hand2")
        self.canvas.place(relx=0.92, rely=0.45)


        self.canvas.bind("<Button-1>", self.on_canvas_click)
        

        # Platzhalter für den Frame mit Text-Widget und Scrollbar
        
        self.text_widget = None
        self.text_frame = None

        # Ereignisbindung für das Klicken im gesamten Fenster
        


        

        # Zeichne das statische Batteriesymbol
        self.draw_static_battery()

        # Initiale Batterieanzeige und Statuswerte
        self.is_glowing = True  # Setze auf True, um den Schimmer zu aktivieren
        self.battery_level = 0
        self.is_charging = False
        self.charge_type = None


        # Halte die IDs der Teile, die sich ändern
        self.battery_fill_id = None
        self.battery_text_id = None
        self.charging_symbol_id = None

        # Update-Funktion aufrufen
        self.update_battery_status()

        self.delete_apps_frame = tk.Frame(master, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.delete_apps_frame.place_forget()
        

        self.delete_all_frame = tk.Frame(self.delete_apps_frame, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.delete_all_frame.place_forget()

        self.scrollbar = tk.Scrollbar(self.delete_all_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)





        # Treeview erstellen und an Scrollbar binden
        self.listbox_apks = ttk.Treeview(self.delete_all_frame, columns=('Package Name',), show='headings', yscrollcommand=self.scrollbar.set)
        self.listbox_apks.place(rely=0.15, relx=0.05, relheight=0.65, relwidth=0.9)

        # Überschrift und Breite der einzigen Spalte konfigurieren
        self.listbox_apks.heading('Package Name', text='Package Name')
        self.listbox_apks.column('Package Name', width=20)  # Setzt die Breite der Spalte

        self.scrollbar.config(command=self.listbox_apks.yview)

        ################# richtige
        self.search_app_var = tk.StringVar()  # Definiere eine StringVar, um den Suchbegriff zu speichern
        self.search_app_entry = tk.Entry(self.delete_all_frame, textvariable=self.search_app_var, width=50)  # Verbinde die Entry mit der StringVar
        self.search_app_entry.place(relx=0.4, rely=0.05, relwidth=0.4, height=25)
        self.search_app_entry.bind("<KeyRelease>", self.search_apks)

        self.info_app_btn = ttk.Button(self.delete_all_frame, image=self.info_ico, command=self.Prop_toplevel)
        self.info_app_btn.place(relx=0.85, rely=0.01)






        
        self.listbox_apks.bind("<Button-1>", self.start_selection)  # Linksklick zum Starten der Auswahl
        self.listbox_apks.bind("<B1-Motion>", self.select_with_drag)  # Bewege die Maus mit gedrückter Taste
        self.listbox_apks.bind("<ButtonRelease-1>", self.end_selection)  # Linksklick loslassen, um die Auswahl zu beenden
        self.listbox_apks.bind("<Button-3>", self.clear_selection)  # Rechtsklick, um die Auswahl aufzuheben
        self.listbox_apks.bind("<Motion>", self.toggle_selection)  # Bewege die Maus mit gedrückter Taste
        

        #self.backup_button = tk.Button(self.delete_apks_frame, text="Sichere ausgewählte Apps", command=self.backup_selected_appss)
        #self.backup_button.place(relx=0.7, rely=0.9, relwidth=0.25, height=25)

        #self.backup_all_button = tk.Button(self.delete_all_frame, text="Alle Apps sichern", command=self.backup_all_apkss)
        #self.backup_all_button.place(relx=0.5, rely=0.8, relwidth=0.17, height=25)



        #self.load_button = tk.Button(self.delete_apks_frame, text="Cleare Cache", command=self.clear_cache)
        #self.load_button.place(relx=0.3, rely=0.8, relwidth=0.15, height=30)


        
        #self.apk_count_label = tk.Label(self.delete_apks_frame, text="0")
        #self.apk_count_label.place(relx=0.1, rely=0.9, relwidth=0.2, height=25)


        ######### richtige

                
        self.settings_frame = tk.Frame(master, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.settings_frame.place_forget()

        self.settings_prop_frame = tk.Frame(master, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.settings_prop_frame.place_forget()
        
        self.settings_opti_frame = tk.Frame(master, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.settings_opti_frame.place_forget()

        self.odin_frame = tk.Frame(master, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.odin_frame.place_forget()
        
        self.fastboot_frame = tk.Frame(master, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.fastboot_frame.place_forget()

        self.install_frame = tk.Frame(master, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.install_frame.place_forget()

        self.select_frame = tk.Frame(master, bg="black", relief=tk.SUNKEN, borderwidth=2)
        self.select_frame.place_forget()

        self.select_s_frame = tk.Frame(master, bg="black", relief=tk.SUNKEN, borderwidth=2)
        self.select_s_frame.place_forget()
        
        self.reboot_options_frame = tk.Frame(master, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.reboot_options_frame.place_forget()

        self.open_install = tk.Button(self.select_frame, text="", command=self.install_frame_open)
        self.open_install.pack(side="left", padx=5)

        
        self.open_lockscreen_frame = tk.Button(self.select_s_frame, text="", command=self.open_settings_framed)
        self.open_lockscreen_frame.pack(side="left", padx=5)

        self.open_propp_frame = tk.Button(self.select_s_frame, text="", command=self.open_prop_frame)
        self.open_propp_frame.pack(side="left", padx=5)

        self.open_opti_frame = tk.Button(self.select_s_frame, text="", command=self.open_opti_framed)
        self.open_opti_frame.pack(side="left", padx=5)


        ########### Phone-Settings-GUI #########################################################

        self.current_volume = self.get_current_volume()
        self.current_brightness = self.get_current_brightness()

        # Erstelle den Lautstärke-Slider
        self.volume_slider = tk.Scale(self.settings_opti_frame, from_=0, to=15, orient="horizontal", label="Lautstärke", command=self.set_volume)
        self.volume_slider.place(relx=0.01, rely=0.1)



        self.brightness_slider = tk.Scale(self.settings_opti_frame, from_=0, to=255, orient="horizontal", label="Helligkeit", command=self.on_brightness_change)
        self.brightness_slider.set(self.current_brightness)  # Setzt den Slider auf den aktuellen Wert
        self.brightness_slider.place(relx=0.2, rely=0.1)
        
        self.bluetooth_button = tk.Button(self.settings_opti_frame, image="", command=self.toggle_bluetooth)
        self.bluetooth_button.place(relx=0.01, rely=0.3)

        self.wifi_button = tk.Button(self.settings_opti_frame, image="", command=self.toggle_wifi)
        self.wifi_button.place(relx=0.07, rely=0.3)

        self.gps_button = tk.Button(self.settings_opti_frame, image=self.gps_ico, command=self.update_gps_text)
        self.gps_button.place(relx=0.13, rely=0.3)

        self.data_button = tk.Button(self.settings_opti_frame, image=self.data_ico, command=self.toggle_mobile_data)
        self.data_button.place(relx=0.19, rely=0.3)


        self.hotspot_button = tk.Button(self.settings_opti_frame, image="", command=self.toggle_hotspot)
        self.hotspot_button.place(relx=0.25, rely=0.3)
        

        self.volume_slider.set(self.current_volume)
        self.check_wifi_periodically()


        ########################################################################################

        self.open_delete_apps_frame = tk.Button(self.select_frame, text="", command=self.delete_frame_open)
        self.open_delete_apps_frame.pack(side="left", padx=5)

        #self.open_odin_frame = tk.Button(self.select_frame, text="Odin", command=self.odin_frame_open)
        #self.open_odin_frame.place(relx=0.33, rely=0.1, relwidth=0.15, height=25)

        self.download_odin_button = tk.Button(self.odin_frame, text="Download Odinn", command=None) #------------
        self.download_odin_button.place(relx=0.01, rely=0.15, relwidth=0.15, height=30)

        
        self.open_fastboot_frame = tk.Button(self.select_frame, text="Fastboot", command=self.fastboot_frame_open)
        self.open_fastboot_frame.pack(side="left", padx=5)

        self.open_backup_frame = tk.Button(self.buttons, text="", command=self.toggle_frame_visibility)
        self.open_backup_frame.place(relx=0.2, rely=0.1)

        self.open_settings_frame = tk.Button(self.buttons, text="", command=self.open_settings_framed)
        self.open_settings_frame.place(relx=0.2, rely=0.55)

        self.open_install_frame = tk.Button(self.buttons, text="", command=self.install_frame_open)
        self.open_install_frame.place(relx=0.2, rely=0.25)
        
        # Widgets erstellen und mit relativer Positionierung platzieren
        self.install_button = tk.Button(self.buttons, text="", command=self.start_installation)
        self.install_button.place(relx=0.2, rely=0.4)

        self.apk_install_frame = tk.Button(self.install_frame, text="", command=self.start_flashing_process)
        self.apk_install_frame.place(relx=0.2, rely=0.25)

        self.patch_boot_button = tk.Button(self.install_frame, text="Patch Boot (Magisk)", command=self.select_boot_image)
        self.patch_boot_button.place_forget()


        self.select_flash_file_button = tk.Button(self.fastboot_frame, text="", command=self.select_flash_file)
        self.select_flash_file_button.place(relx=0.2, rely=0.7)

        self.start_flash_button = tk.Button(self.fastboot_frame, text="", command=self.execute_flash)
        self.start_flash_button.place(relx=0.4, rely=0.7)

        # delete frame widgets -----------------------------------

        self.apps = []  # Liste der installierten Apps
        self.displayed_apps = []  # Liste der Checkbutton-Variablen

        #ADB INSTALL---------------------------------------------------

        #Lockscreen#############################

        frame = tk.Frame(self.settings_prop_frame, bg="red")
        frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=1)

                # Scrollbare Canvas erstellen
        self.canvas = tk.Canvas(frame, background="black")
        
        # Scrollbar hinzufügen

        # Scrollable Frame im Canvas erstellen
        self.scrollable_frame = tk.Frame(self.canvas, background="black")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    
        self.scrollable_frame.bind("<Configure>", self.update_scrollregion)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
          

        self.canvas.pack(side="left", fill="both", expand=True)
        # Label in das scrollbare Frame setzen


        self.info_label = tk.Text(self.scrollable_frame, wrap="word", bg="black", highlightbackground="black", borderwidth=0, highlightcolor="black", highlightthickness=0, fg="white", font=("Courier New", 10))
        self.info_label.pack(fill="both", expand=True)

        self.save_info_button = tk.Button(self.settings_prop_frame, text="", command=self.save_prop_text)
        self.save_info_button.place(relx=0.9, rely=0.9, anchor="center")

        self.get_info_button = tk.Button(self.settings_prop_frame, text="", command=self.get_device_info)
        self.get_info_button.place(relx=0.9, rely=0.8, anchor="center")
        self.get_device_info()

        ############# PASSWORT ########################

        self.Passwort_frame = tk.Frame(self.settings_frame, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.Passwort_frame.place(relx=0.1, rely=0.15, relwidth=0.3, relheight=0.5)

        ############# REMOVE LOCKSCREEN ################

        self.Remove_passwort_frame = tk.Frame(self.settings_frame, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.Remove_passwort_frame.place(relx=0.1, rely=0.7, relwidth=0.3, relheight=0.3)

        self.remove_password_label = tk.Label(self.Remove_passwort_frame, bg="#2C2C2C", text="")
        self.remove_password_label.place(relx=0, rely=0.1, relwidth=1)

        self.remove_password_button = tk.Button(self.Remove_passwort_frame, text="", command=self.start_delete_threads)
        self.remove_password_button.place(relx=0, rely=0.7)

        ############ cange passwort ########################

        self.old_password_var = tk.StringVar()
        self.old_password_entry = PlaceholderEntry(self.Passwort_frame, textvariable=self.old_password_var, placeholder="OLD PASSWORD")
        self.old_password_entry.place(relx=0.1, rely=0.12, relwidth=0.8, height=20)

        self.new_password_var = tk.StringVar()
        self.new_password_entry = PlaceholderEntry(self.Passwort_frame, textvariable=self.new_password_var, placeholder="NEW PASSWORD")
        self.new_password_entry.place(relx=0.1, rely=0.4, relwidth=0.8, height=20)

        self.set_password_button = tk.Button(self.Passwort_frame, image=self.yes_ico, command=self.set_password)
        self.set_password_button.place(relx=0.25, rely=0.6, relwidth=0.2, height=30)

        self.clear_password_button = tk.Button(self.Passwort_frame, image=self.müll_ico, command=self.clear_password)
        self.clear_password_button.place(relx=0.55, rely=0.6, relwidth=0.2, height=30)

        ################ PIN #######################  

        self.PIN_frame = tk.Frame(self.settings_frame, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        self.PIN_frame.place(relx=0.6, rely=0.15, relwidth=0.3, relheight=0.5)

        self.only_numbers = self.master.register(self.only_numbers)

        self.old_PIN_var = tk.StringVar()
        self.old_PIN_entry = PlaceholderEntry(self.PIN_frame, textvariable=self.old_PIN_var, placeholder="OLD PIN", validate_func=self.only_numbers)
        self.old_PIN_entry.place(relx=0.1, rely=0.12, relwidth=0.8, height=20)

########################################        # Neues PIN Entry
        self.new_PIN_var = tk.StringVar()
        self.new_PIN_entry = PlaceholderEntry(self.PIN_frame, textvariable=self.new_PIN_var, placeholder="NEW PIN", validate_func=self.only_numbers)
        self.new_PIN_entry.place(relx=0.09, rely=0.4, relwidth=0.8, height=20)

        # Button zum Setzen des neuen Passworts
        self.set_PIN_button = tk.Button(self.PIN_frame, image=self.yes_ico, command=self.set_pin)
        self.set_PIN_button.place(relx=0.25, rely=0.6, relwidth=0.2, height=30)

        # Button zum Löschen des Entsperr-Passworts
        self.clear_PIN_button = tk.Button(self.PIN_frame, image=self.müll_ico, command=self.clear_pin)
        self.clear_PIN_button.place(relx=0.55, rely=0.6, relwidth=0.2, height=30)


        ############################################################################################################
        ############################################################################################################

        #self.sel_frame = tk.Frame(root, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        #self.sel_frame.place(relx=0, rely=0, relwidth=1, relheight=0.07)

        #save_button = tk.Button(self.sel_frame, text="Phone to PC", command=None)
        #save_button.place(relx=0.5, rely=0.5, anchor='center')

        #self.ptl_frame = tk.Frame(root, bg="#2C2C2C", relief=tk.SUNKEN, borderwidth=2)
        #self.ptl_frame.place(relx=0, rely=0.07, relwidth=1, relheight=1)
        

        #self.ddbackupbox = tk.Listbox(self.ptl_frame, selectmode=tk.MULTIPLE, height=15, bg="black", fg="White")
        #self.ddbackupbox.place(relx=0.05, rely=0.05, relwidth=0.9)

        # Suchfeld

        self.filtered_apps = self.apps.copy()  
        self.filtered_apps = [] 


        # Such-Button


        


        #Reboot buttons in reboot_options_frame
        self.Reboot_to_OS = tk.Button(self.reboot_options_frame, text="", command=self.reboot_to_OS)
        self.Reboot_to_OS.pack(side="top",pady=5)

        self.Reboot_to_Recovery = tk.Button(self.reboot_options_frame, text="", command=self.reboot_to_Recovery)
        self.Reboot_to_Recovery.pack(side="top",pady=5)

        self.Reboot_to_fastboot = tk.Button(self.reboot_options_frame, text="", command=self.restart_to_fastboot)
        self.Reboot_to_fastboot.pack(side="top",pady=5)

        self.Reboot_to_bootlaoder = tk.Button(self.reboot_options_frame, text="", command=self.reboot_to_Bootloader)
        self.Reboot_to_bootlaoder.pack(side="top",pady=5)

        self.partition_flash_frame = ttk.LabelFrame(self.fastboot_frame, text="")
        self.partition_flash_frame.place(relx=0.1, rely=0.18, relwidth=0.8, relheight=0.5)

        self.scroll_flash_partitions = tk.Frame(self.partition_flash_frame) #fastboot flash
        self.scroll_flash_partitions.pack(fill="both", expand="yes")



        self.canvas_flash_partitions = tk.Canvas(self.scroll_flash_partitions)
        self.scrollbar_flash_partitions = ttk.Scrollbar(self.scroll_flash_partitions, orient="vertical", command=self.canvas_flash_partitions.yview)
        self.scrollable_frame_flash_partitions = tk.Frame(self.canvas_flash_partitions)

        self.scrollable_frame_flash_partitions.bind("<Configure>", lambda e: self.canvas_flash_partitions.configure(scrollregion=self.canvas_flash_partitions.bbox("all")))

        self.canvas_flash_partitions.create_window((0, 0), window=self.scrollable_frame_flash_partitions, anchor="nw")
        
        self.scroll_area_partitions = ttk.LabelFrame(self.backup_twrp_frame, text="")
        self.scroll_area_partitions.place(relx=0.01, rely=0.01, relwidth=0.48, relheight=0.57)

        # Canvas und Scrollbar
        self.canvas_partitions = tk.Canvas(self.scroll_area_partitions)
        self.scrollbar_partitions = ttk.Scrollbar(self.canvas_partitions, orient="vertical", command=self.canvas_partitions.yview)
        self.scrollable_frame_partitions = tk.Frame(self.canvas_partitions)

        # Bind Configure Event
        self.scrollable_frame_partitions.bind("<Configure>", lambda e: self.canvas_partitions.configure(scrollregion=self.canvas_partitions.bbox("all")))
        
        # Erstelle das Fenster im Canvas
        self.canvas_partitions.create_window((0, 0), window=self.scrollable_frame_partitions, anchor="nw")

        # Pack Canvas und Scrollbar nebeneinander
        self.canvas_partitions.pack(side="top", fill="both", expand=True)
        self.scrollbar_partitions.place(relx=0.9, rely=0.01, relwidth=0.05, relheight=1)
        self.canvas_partitions.configure(yscrollcommand=self.scrollbar_partitions.set)

        
        self.canvas_flash_partitions.pack(side="left", fill="both", expand=True)
        self.scrollbar_flash_partitions.pack(side="right", fill="y")
        self.canvas_flash_partitions.configure(yscrollcommand=self.scrollbar_flash_partitions.set)

        # Restore Frame
        self.restore_frame = ttk.LabelFrame(self.backup_twrp_frame, text="")
        self.restore_frame.place(relx=0.51, rely=0.01, relwidth=0.48, relheight=0.57)

        self.restore_files_vars = {}  # Für die Checkbuttons der wiederherzustellenden Dateien

        self.restore_file_frame = tk.Frame(self.restore_frame)
        self.restore_file_frame.pack(fill="both", expand=True)

        self.listbox_restore_files = tk.Listbox(self.restore_file_frame, selectmode=tk.SINGLE)
        self.listbox_restore_files.pack(side=tk.LEFT, fill="both", expand=True, padx=10, pady=10)

        self.restore_scrollbar = ttk.Scrollbar(self.restore_file_frame, orient="vertical", command=self.listbox_restore_files.yview)
        self.restore_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.listbox_restore_files.configure(yscrollcommand=self.restore_scrollbar.set)

        # Backup Button
        self.backup_button = tk.Button(self.backup_twrp_frame, text='', command=self.show_backup_options)
        self.backup_button.place(relx=0.13, rely=0.6)

        # Restore Button
        self.restore_button = tk.Button(self.backup_twrp_frame, text='', command=self.show_restore_options)
        self.restore_button.place(relx=0.59, rely=0.6)

        # Execute Restore Button
        self.execute_restore_button = tk.Button(self.backup_twrp_frame, text='', command=self.execute_restore)
        self.execute_restore_button.place(relx=0.59, rely=0.76)

        # Update Device Info Button
        self.update_device_info_button = tk.Button(master, image=self.refresh_ico, command=self.restart_program)
        self.update_device_info_button.place(relx=0.95, rely=0.1, relwidth=0.04, height=30)
       
        # öffnet format frame
        self.open_format_frame_button = tk.Button(master, image=self.müll_ico, command=None)
        self.open_format_frame_button.place(relx=0.95, rely=0.15, relwidth=0.04, height=30)

        # öffnet Home
        self.go_home_button = tk.Button(master, image=self.home_ico, command=self.close_all_Frames)
        self.go_home_button.place(relx=0.03, rely=0.05, relwidth=0.05, height=30)

        self.Screen_share_button = tk.Button(master, image=self.screen_ico, command=self.start_screen_share)
        self.Screen_share_button.place(relx=0.03, rely=0.1, relwidth=0.05, height=30,)

        self.exploer_button = tk.Button(master, image=self.explorer_ico, command=self.start_data)
        self.exploer_button.place(relx=0.03, rely=0.15, relwidth=0.05, height=30,)

        # öffnet power frame
        self.open_power_frame_button = tk.Button(master, image=self.Power_ico, command=self.open_reboot_frame)
        self.open_power_frame_button.place(relx=0.95, rely=0.05, relwidth=0.04, height=30)

        # Progress Bar
        self.progress = ttk.Progressbar(master, orient="horizontal", length=400, mode="determinate")
        self.progress.place(relx=0.01, rely=0.5, relwidth=0.98, height=30)

        # Console Output
        #self.console_output = scrolledtext.ScrolledText(master, wrap=tk.WORD, height=10, state="normal", bg="black", fg="#F6F6F6")
        #self.console_output.place(relx=0.01, rely=0.55, relwidth=0.98, relheight=0.98)


        #self.console_output.tag_config('del', foreground='Green')

        frame = tk.Frame(master)
        frame.place(relx=0.01, rely=0.55, relwidth=0.98, relheight=0.4)

        # Text-Widget erstellen
        self.console_output = tk.Text(frame, wrap=tk.WORD, bg="black", fg="#F6F6F6")
        self.console_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar erstellen und mit dem Text-Widget verknüpfen
        self.scrollbar = tk.Scrollbar(frame, command=self.console_output.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_label = tk.Label(self.buttons, text="Root Status: ", bg="#2C2C2C")
        self.status_label.place(relx=0.01, rely=0.01)

        # Geräteinformationen Frame
        self.device_info_frame = ttk.LabelFrame(master, text="", style="Custom.TLabelframe")
        self.device_info_frame.place_forget()
        style = ttk.Style()
        style.configure("Custom.TLabelframe", background="black")
        style.configure("Custom.TLabelframe.Label", background="black", foreground="Red", font=("Helvetica", 13, "bold"))

        self.device_info_text = scrolledtext.ScrolledText(self.device_info_frame, wrap=tk.WORD, height=10, state="normal", bg="black", fg="Green")
        self.device_info_text.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.safe_info = tk.Button(self.master, text="")
        self.safe_info.place_forget()
        
        self.load_installed_apps()
        self.flash_file_path = None

            # Mausrad-Ereignis für vertikales Scrollen binden
        if self.current_volume is not None:
            self.volume_slider.set(self.current_volume)
        

        # Geräteinformationen beim Start abrufen
        self.update_device_info()
        self.frame_visible = False

        self.previous_progress = -1
        self.partitions_list = self.get_partitions()
        self.update_device_info()
        self.check_root_status()
        self.load_installed_apps()
        self.get_device_info()
        self.get_bluetooth_status()
        self.get_gps_status()
        self.check_mobile_data_periodically()
        self.refresh_app_list()
        self.update_bluetooth_text()
        self.master.after(10000, self.check_bluetooth_periodically)
        self.process = None
        self.is_mouse_down = False
        directory = ("/data/system")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", background="darkgray", 
                        troughcolor="darkgray", arrowcolor="darkgray", gripcount=0,
                        borderwidth=0)

        if self.current_brightness is not None:
            self.brightness_slider.set(self.current_brightness)
        
        # Event-Handler, um Canvas-Größe anzupassen, wenn sich das Frame ändert
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)#
        self.update_hotspot_button_text()

        # Scrollen mit zwei Fingern ermöglichen
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)  # Windows und macOS für vertikales Scrollen
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_shift_mouse_wheel)  # Horizontales Scrollen bei Shift
        self.load_apks()

        self.language_code = self.load_language_setting()

        # Übersetzungen und Texte laden
        self.translations = self.load_translations()
        self.texts = self.get_texts(self.language_code)

        self.language_var = tk.StringVar(value=self.language_code)
        self.language_dropdown = ttk.Combobox(self.buttons, textvariable=self.language_var, values=list(self.translations.keys()))
        
        
        self.language_dropdown.bind("<<ComboboxSelected>>", self.change_language)
        
        self.language_dropdown.place(relx=0.01, rely=0.9)
        

        
        for partition in self.partitions:
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(self.scrollable_frame_flash_partitions, text=partition, variable=var)
            checkbox.pack(anchor="w")
            self.partitions_vars[partition] = var

        for partition in self.partitions_list:
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(self.scrollable_frame_partitions, text=partition, variable=var)
            checkbox.pack(anchor="w")
            self.partition_vars[partition] = var

        self.files_to_delete = ["/data/systm/password.key", "/data/system/pattern.key", "/data/system/locksettings.db", "/data/system/locksettings.db-journal", "/data/system/locksettings.db-shm", 
                                "/data/system/locksettings.db-wal", "/data/system/gesture.key",
                                "/data/systemgatekeeper.pin.key", "/data/system/gatekeeper.pattern.key", "/data/system/*.key", "/data/system/applockpin.key"]  # Hier Dateipfade anpassen
        self.update_texts()
        


    ############# BATTERIE ##############




    # Auswahl des Boot-Image-Pfads
    def select_boot_image(self):
        self.boot_image_path = filedialog.askopenfilename(filetypes=[("Image-Dateien", "*.img")])
        
        if self.boot_image_path:
            self.console_output.insert(tk.End, f"Ausgewähltes Boot-Image: {self.boot_image_path}")

            choice = messagebox.askquestion("Wählen Sie aus", "Start Patching?", icon='question')
            
            if choice == 'yes':
                # Prüfen, ob eine Boot-Image-Datei ausgewählt wurde
                if self.boot_image_path:
                    self.console_output.insert(tk.END,"Starte den Patching-Prozess...")
                    self.run_patching_in_thread()  # Datei kopieren und patchen
                else:
                    self.console_output.insert(tk.END,"Keine Boot-Image-Datei ausgewählt. Abbrechen.")
                    return  # Abbrechen, wenn keine Datei ausgewählt wurde
            else:
                self.console_output.insert(tk.END, "Patching abgebrochen.")
                return  # Abbrechen, wenn der Benutzer nicht fortfahren möchte
        else:
            self.console_output.insert(tk.END, "Keine Boot-Image-Datei ausgewählt.")  # Benutzer informierender

    # Starte Patching-Prozess in einem neuen Thread
    def run_patching_in_thread(self):
        patching_thread = threading.Thread(target=self.start_patching)
        patching_thread.start()

    # Startet den gesamten Patching-Prozess
    def start_patching(self):
        if not self.boot_image_path or not os.path.isfile(self.boot_image_path):
            messagebox.showerror("Fehler", "Bitte wähle ein gültiges Boot-Image aus.")
            return
        if not os.path.isdir(self.magisk_folder_path):
            messagebox.showerror("Fehler", "Magisk-Ordner existiert nicht oder ist ungültig.")
            return

        # Extrahiere, modifiziere und repacke das Boot-Image
        self.extract_boot_image()
        self.modify_init_rc()
        self.repack_boot_image()
        messagebox.showinfo("Erfolg", "Boot-Image-Patching abgeschlossen.")

    # Extrahieren des Boot-Images mit magiskboot
    def extract_boot_image(self):
        try:
            self.console_output.insert(tk.END,"Extrahiere Boot-Image mit magiskboot...")
            magiskboot_exe = os.path.join(self.magisk_folder_path, "magiskboot.exe")
            if not os.path.isfile(magiskboot_exe):
                self.console_output.insert(tk.END, "Fehler: magiskboot.exe wurde nicht gefunden.")
                return
            
            # Befehl und Parameter
            command = [magiskboot_exe, "unpack", self.boot_image_path]
            self.console_output.insert(tk.END, f"Ausgeführter Befehl: {' '.join(command)}")  # Log den Befehl
            
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.console_output.insert(tk.END, result.stdout)
            self.console_output.insert(tk.END, result.stderr)
            if result.returncode != 0:
                self.console_output.insert(tk.END,"Fehler beim Extrahieren des Boot-Images.")
            else:
                self.console_output.insert(tk.End, "Boot-Image erfolgreich extrahiert.")
        except subprocess.CalledProcessError as e:
            self.console_output.insert(tk.END, f"Fehler beim Extrahieren: {str(e)}")

    # Modifiziere die init.rc-Datei
    def modify_init_rc(self):
        init_rc_path = os.path.join(self.magisk_folder_path, "ramdisk.cpio")
        try:
            self.console_output.insert(tk.END, "Modifiziere init.rc...")
            with open(init_rc_path, "a") as init_rc:
                init_rc.write("\n# Magisk init\nexec /magiskinit\n")
            self.console_output.insert(tk.END, "init.rc erfolgreich modifiziert.")
        except FileNotFoundError:
            self.console_output.insert(tk.END,"init.rc konnte nicht gefunden werden.")

    # Repacke das Boot-Image mit magiskboot
    def repack_boot_image(self):
        try:
            self.console_output.insert(tk.END, "Packe Boot-Image mit magiskboot...")
            magiskboot_exe = os.path.join(self.magisk_folder_path, "magiskboot.exe")
            
            # Bestimme den Pfad für das gepackte Boot-Image
            new_boot_image_path = os.path.join(os.path.dirname(self.boot_image_path), "newboot.img")
            
            # Befehl und Parameter
            command = [magiskboot_exe, "repack", self.boot_image_path, new_boot_image_path]
            self.console_output.insert(tk.END, f"Ausgeführter Befehl: {' '.join(command)}")  # Log den Befehl
            
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.console_output.insert(tk.END, result.stdout)
            self.console_output.insert(tk.END, result.stderr)
            if result.returncode != 0:
                self.console_output.insert(tk.END, "Fehler beim Repacken des Boot-Images.")
            else:
                self.console_output.insert(tk.END, f"Boot-Image erfolgreich gepackt: {new_boot_image_path}")
        except subprocess.CalledProcessError:
            self.console_output.insert(tk.END, "Fehler beim Repacken des Boot-Images.")

    # Callback-Funktion für den Mausklick

    def start_flashing_process(self):
        """Starte den gesamten Flash-Prozess in einem Hintergrund-Thread."""
        threading.Thread(target=self.flash_zip_in_recovery, daemon=True).start()

    def flash_zip_in_recovery(self):
        """Überprüfen, ob das Gerät im Recovery-Modus ist, und gegebenenfalls neu starten."""
        recovery_mode_detected = False

        while not recovery_mode_detected:
            try:
                # Prüfen, ob das Gerät im Recovery-Modus ist
                command = "adb shell getprop ro.boot.mode"
                boot_mode = subprocess.check_output(command, shell=True).decode('utf-8').strip()

                if boot_mode == "":
                    self.console_output.insert(tk.END, "Das Gerät ist jetzt im Recovery-Modus.\n")
                    recovery_mode_detected = True
                    break  # Beende die Schleife, wenn der Recovery-Modus erkannt wird

                else:
                    self.console_output.insert(tk.END, "Das Gerät ist nicht im Recovery-Modus. Starte im Recovery...\n")
                    subprocess.run("adb reboot recovery", shell=True)
                    self.console_output.insert(tk.END, "Bitte warten Sie, bis das Gerät neu gestartet ist...\n")
                    time.sleep(15)  # Warte, damit das Gerät Zeit hat, neu zu starten
                    continue  # Überprüfe weiter, ohne die Schleife zu beenden

            except subprocess.CalledProcessError:
                # Ignoriere den Fehler und mache mit der nächsten Überprüfung weiter
                self.console_output.insert(tk.END, "Fehler beim Abrufen des Boot-Modus. Überprüfe erneut...\n")
                time.sleep(5)  # Überprüfen alle 5 Sekunden

        if recovery_mode_detected:
            self.select_zip_file()

    def select_zip_file(self):
        """Wähle die ZIP-Datei aus, die geflasht werden soll."""
        zip_file = filedialog.askopenfilename(title="Wählen Sie die ZIP-Datei zum Flashen aus", filetypes=[("ZIP files", "*.zip")])
        if zip_file:
            self.copy_and_flash(zip_file)

    def copy_and_flash(self, zip_file):
        """Kopiert die ZIP-Datei auf das Gerät und flasht sie."""
        try:
            # Pfad zur ZIP-Datei bestimmen
            zip_file_name = zip_file.split('/')[-1]
            destination_path = f"/sdcard/{zip_file_name}"

            self.format_data()

            # Kopiere die ZIP-Datei auf das Gerät
            self.console_output.insert(tk.END, f"Kopiere {zip_file_name} auf das Gerät...\n")
            subprocess.run(f"adb push \"{zip_file}\" \"{destination_path}\"", shell=True)

            # Flashen der ZIP-Datei über TWRP
            self.console_output.insert(tk.END, f"Flashe {zip_file_name}...\n")
            subprocess.run(f"adb shell twrp install \"{destination_path}\"", shell=True)

            self.console_output.insert(tk.END, "Flashing abgeschlossen!\n")

            self.open_toplevel()

        except subprocess.CalledProcessError as e:
            self.console_output.insert(tk.END, f"Fehler beim Kopieren oder Flashen der Datei: {e}\n")
        except Exception as e:
            self.console_output.insert(tk.END, f"Ein Fehler ist aufgetreten: {str(e)}\n")

    def open_toplevel(self):
        # Toplevel-Fenster erstellen
        toplevel = tk.Toplevel(self.root)
        toplevel.title("Toplevel Fenster")
        toplevel.geometry("300x300")

        # Stil für die Buttons
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 12), padding=10)

        # Buttons erstellen
        button1 = ttk.Button(toplevel, text="Flash again", command=self.start_flashing_process)
        button2 = ttk.Button(toplevel, text="Reboot", command=self.reboot_to_OS)
        button3 = ttk.Button(toplevel, text="Format Data", command=self.format_data)
        button4 = ttk.Button(toplevel, text="Wipe dalvik/cache", command=self.format_dalvik)

        # Buttons anordnen
        button1.pack(pady=10, padx=20, fill=tk.X)
        button2.pack(pady=10, padx=20, fill=tk.X)
        button3.pack(pady=10, padx=20, fill=tk.X)
        button4.pack(pady=10, padx=20, fill=tk.X)

    def format_data(self):
        # Bestätigungsdialog
        if messagebox.askyesno("Empfohlen", "Sie sollten die Daten vor dem Flashen Formatieren"):
            try:
                # ADB Befehl zum Formatieren der Datenpartition
               
                subprocess.run(f"adb shell twrp format /data", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # Erfolgreich informiert
                messagebox.showinfo("Erfolg", "Die Datenpartition wurde erfolgreich formatiert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Formatieren der Datenpartition: {e}")

    def format_dalvik(self):
        # Bestätigungsdialog
        
            try:
                # ADB Befehl zum Formatieren der Datenpartition
               
                subprocess.run(f"adb shell twrp format /dalvik", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(f"adb shell twrp format /cache", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # Erfolgreich informiert
                messagebox.showinfo("Erfolg", "Die Datenpartition wurde erfolgreich formatiert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Formatieren der Datenpartition: {e}")


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
          # Texte aktualisieren
        self.save_language_setting()  # Spracheinstellung speichern
        
    
    def update_texts(self):

        try:
            # Texte der UI-Elemente basierend auf `self.texts` aktualisieren
            self.safe_info.config(text=self.texts["safe_btn"])
            self.device_info_frame.config(text=self.texts["device_info_frame"])
            self.execute_restore_button.config(text=self.texts["execute_restore_button"])
            self.restore_button.config(text=self.texts["restore_button"])
            self.backup_button.config(text=self.texts["backup_button"])
            self.open_twrp_frame.config(text=self.texts["backup_restore_button"])
            self.restore_frame.config(text=self.texts["restore_frame"])
            self.scroll_area_partitions.config(text=self.texts["scroll_area_partitions"])
            self.partition_flash_frame.config(text=self.texts["partition_flash_frame"])
            self.Reboot_to_bootlaoder.config(text=self.texts["Reboot_to_bootloader"])
            self.Reboot_to_fastboot.config(text=self.texts["Reboot_to_fastboot"])
            self.Reboot_to_Recovery.config(text=self.texts["Reboot_to_Recovery"])
            self.Reboot_to_OS.config(text=self.texts["Reboot_to_OS"])
            self.remove_password_button.config(text=self.texts["remove_password_button"])
            self.remove_password_label.config(text=self.texts["remove_password_label"])
            self.get_info_button.config(text=self.texts["get_info_button"])
            self.save_info_button.config(text=self.texts["save_info_button"])
            self.start_flash_button.config(text=self.texts["start_flash_button"])
            self.select_flash_file_button.config(text=self.texts["select_flash_file_button"])
            self.apk_install_frame.config(text=self.texts["install_apk_button"])
            self.install_button.config(text=self.texts["install_adb_button"])
            self.open_install.config(text=self.texts["open_install"])
            self.open_install_frame.config(text=self.texts["open_install_frame"])
            self.open_settings_frame.config(text=self.texts["settings_button"])
            self.open_backup_frame.config(text=self.texts["backup_restore_button"])
            self.open_delete_apps_frame.config(text=self.texts["apps_button"])
            self.open_opti_frame.config(text=self.texts["phone_settings_button"])
            self.open_propp_frame.config(text=self.texts["properties_button"])
            self.open_lockscreen_frame.config(text=self.texts["lockscreen_button"])
            self.restore_dd_button.config(text=self.texts["restore_partitions_button"])
            self.save_dd_button.config(text=self.texts["save_partitions_button"])
            self.open_dd_frame.config(text=self.texts["backup_root_button"])

            self.APP_action = [

                self.texts['App Installieren'],
                self.texts['App Löschen'],
                self.texts['App Starten'],
                self.texts['App Stoppen'],
                self.texts['Cache löschen'],
                self.texts['Daten löschen'],

            ]

            self.List_action = [
                self.texts['Nur Benutzer APPS'],
                self.texts['Nur System APPS'],
                self.texts['Alle APPS'],

            ]

            self.Backup_options = [
                self.texts['Sichere alle APPS'],
                self.texts['Sichere ausgewählte APPS'],
                

            ]

            self.permissions = [
                self.texts['Kamera'],
                self.texts['Mikrofon'],
                self.texts['Speicher lesen'],
                self.texts['Speicher schreiben'],
                self.texts['Feiner Standort'],
                self.texts['Grob Standort'],
                self.texts['SMS senden'],
                self.texts['SMS empfangen'],
                self.texts['Internet'],
                self.texts['Kontakte lesen'],
                self.texts['Kontakte schreiben'],
                self.texts['Anrufliste lesen'],
                self.texts['Anrufliste schreiben'],
                self.texts['Telefonstatus lesen'],
                self.texts['Anrufe tätigen'],
                self.texts['Ausgehende Anrufe verarbeiten'],
                self.texts['Körpersensoren'],
                self.texts['Bluetooth'],
                self.texts['Bluetooth-Administration'],
                self.texts['WLAN-Status ändern'],
                self.texts['WLAN-Status anzeigen'],
                self.texts['NFC'],
                self.texts['Netzwerkstatus anzeigen'],
                self.texts['Beim Start ausführen'],
                self.texts['System-Overlay'],
                self.texts['Systemeinstellungen ändern'],
                self.texts['Fingerabdrucksensor verwenden'],
                self.texts['Konten abrufen'],
                self.texts['Biometrische Authentifizierung verwenden'],
                self.texts['Hintergrund-Standortzugriff'],
                self.texts['Batterieoptimierung ignorieren'],
                self.texts['Vordergrunddienst'],
                self.texts['Vibration'],
                self.texts['Sichtbarkeit des Geräts'],
                self.texts['WLAN-Verbindung'],
                self.texts['APN ändern'],
                self.texts['Standortdienste'],
                self.texts['Statusbar anpassen'],
                self.texts['Systemapps nutzen'],
                self.texts['Mediendateien abspielen'],
                self.texts['Kalender lesen'],
                self.texts['Kalender ändern'],
                self.texts['Zugriff auf die Benutzeroberfläche'],
                self.texts['Zugriff auf die Hardware'],
                self.texts['Bluetooth-Admin'],
                self.texts['Task-Manager'],
                self.texts['Einstellungen ändern'],
                self.texts['Ereignisse überwachen'],
                self.texts['Standortdienste verwenden'],
                self.texts['Fehlersuche'],
                self.texts['Zugriff auf Benachrichtigungen'],
                self.texts['Root-Zugriff'],
                self.texts['Superuser-Zugriff'],
                self.texts['Zugriff auf Systemdateien'],
                self.texts['Zugriff auf alle Anwendungen'],
                self.texts['Zugriff auf gesperrte Apps'],
                self.texts['Zugriff auf versteckte Apps'],
                self.texts['Zugriff auf interne Speicherorte'],
                self.texts['Zugriff auf die Systemoberfläche'],
                self.texts['Zugriff auf das Dateisystem'],
                self.texts['Zugriff auf Hardware-Sensoren'],
                self.texts['Zugriff auf Systemdienste'],
                self.texts['Zugriff auf die Registrierungsdatenbank'],
            ]

        
        
            info_text = (
                f"\n\n{self.texts['Hersteller']}: {self.manufacturer}\n"
                f"{self.texts['device_model']}: {self.model}\n"
                f"{self.texts['android_version']}: {self.version}\n"
                f"{self.texts['cpu_architecture']}: {self.cpu_abi}\n"
                f"{self.texts['cpu_cores']}: {self.cpu_cores}\n\n"
                f"\n---- {self.texts['display']} ----\n"
                f"{self.texts['display_resolution']}: {self.display_auflösung}\n"
                f"{self.texts['pixel_density']}: {self.pixeldichte}\n"
                f"{self.texts['brightness']}: {self.display_helligkeit}\n"
                f"\n---- {self.texts['storage']} ----\n"
                f"{self.texts['total_storage']}: {self.total_gb:.2f} GB\n"
                f"{self.texts['used_storage']}: {self.used_gb:.2f} GB\n"
                f"{self.texts['free_storage']}: {self.available_gb:.2f} GB\n"
                f"\n---- {self.texts['ram']} ----\n"
                f"{self.texts['total_ram']}: {self.total_ram:.2f} MB\n"
                f"{self.texts['free_ram']}: {self.free_ram:.2f} MB\n"
                f"{self.texts['available_ram']}: {self.available_ram:.2f} MB\n"
                f"\n---- {self.texts['network_sim']} ----\n"
                f"{self.texts['sim_card_status']}: {self.sim_state}\n"
                f"{self.texts['sim_card_provider']}: {self.sim_host}\n"
                f"{self.texts['wifi']}: {self.ip_info}\n"
                f"\n---- {self.texts['bluetooth']} ----\n"
                f"{self.texts['bluetooth_status']}: {self.bluetooth_status}\n"     
                f"{self.texts['connected_devices']}: {', '.join(self.bluetooth_devices) if self.bluetooth_devices else self.texts['no_connected_devices']}\n"
                f"\n---- {self.texts['battery']} ----\n"
                f"\n{self.battery_info}\n"
            )

            self.info_label.config(state="normal")
            self.info_label.delete("1.0", tk.END)
            self.info_label.insert(tk.END, info_text)
            self.info_label.config(state="disabled")
        
        except Exception as e:
            # Optional: Fehlerprotokollierung oder -benachrichtigung
            print(f"Fehler beim Erstellen des Info-Textes: {str(e)}")
            # Hier könnte man auch eine Benachrichtigung für den Benutzer hinzufügen

        
        self.create()

    def change_language(self, event):
        # Messagebox mit Ja- und Abbrechen-Option
        self.switch_language()
        self.device_info()
        self.del_comboboxen()
        if messagebox.askyesno("Neustart erforderlich", "Sie müssen das Programm neu starten, um die Änderungen zu übernehmen. Möchten Sie jetzt neu starten?"):
            
            self.restart_program()


    def wrestart_program(self):
        """Callback-Funktion für den Button."""
        if self.restarter.restart_program():
            pass
        else:
            pass

    def restart_program(self):
        # Das aktuelle Skript neu starten
        self.switch_language()
        self.update_texts()
        
        self.device_info()
        os.execv(sys.executable, ['python'] + sys.argv)
        
       

    def del_comboboxen(self):

        if self.function_backup_combobox.winfo_exists():
            self.function_backup_combobox.destroy()
        if self.function_list_combobox.winfo_exists():
            self.function_list_combobox.destroy()
        if self.function_combobox.winfo_exists():
            self.function_combobox.destroy()
        if self.function_up_combobox.winfo_exists():
            self.function_up_combobox.destroy()
        if self.function_p_combobox.winfo_exists():
            self.function_p_combobox.destroy()
        self.create()
        

    def create(self):
        # Überprüfen, ob das OptionMenu bereits existiert, um doppelte Instanzen zu vermeiden
        if hasattr(self, 'function_p_combobox'):
            return  # Das OptionMenu existiert bereits, also verlasse die Methode
        
        self.selected_p_action = tk.StringVar(value=self.texts['Give Permissions'])
        self.function_p_combobox = tk.OptionMenu(self.delete_all_frame, self.selected_p_action, *self.permissions, command=self.select_p_option)

        self.selected_up_action = tk.StringVar(value=self.texts['Remove Permissions'])
        self.function_up_combobox = tk.OptionMenu(self.delete_all_frame, self.selected_up_action, *self.permissions, command=self.select_up_option)

        self.selected_action = tk.StringVar(value=self.texts['APP Action'])
        self.function_combobox = tk.OptionMenu(self.delete_all_frame, self.selected_action, *self.APP_action, command=self.execute_action)

        self.selected_list_action = tk.StringVar(value=self.texts['(System/User Apps) List'])
        self.function_list_combobox = tk.OptionMenu(self.delete_all_frame, self.selected_list_action, *self.List_action, command=self.select_listbox)

        self.selected_backup_action = tk.StringVar(value=self.texts['Backup Options'])
        self.function_backup_combobox = tk.OptionMenu(self.delete_all_frame, self.selected_backup_action, *self.Backup_options, command=self.select_backup_option)

        # Widgets anordnen
        self.function_backup_combobox.place(relx=0.7, rely=0.9)
        self.function_list_combobox.place(relx=0.01, rely=0.05)
        self.function_combobox.place(relx=0.01, rely=0.9)
        self.function_up_combobox.place(relx=0.3, rely=0.9)
        self.function_p_combobox.place(relx=0.3, rely=0.8)
        



    def Prop_toplevel(self):
        # Erstellen des Toplevel-Fensters
        toplevel = tk.Toplevel(self.master)
        toplevel.title("App Details")
        toplevel.geometry("350x400")
        toplevel.resizable(False, False)
        

        # Styling des Toplevel
        toplevel.configure(bg="#ffffff")

        # App Details
        self.app_info_frame = tk.Frame(toplevel, bg="#ffffff")
        self.app_info_frame.pack(pady=10)

        # App-Name und Kopieren-Button
        self.app_name_frame = tk.Frame(self.app_info_frame, bg="#ffffff")
        self.app_name_frame.pack(fill='x', padx=10)

        self.app_name = tk.Label(self.app_name_frame, text="App Name: None", bg="#ffffff")
        self.app_name.pack(side='left', anchor="w")

        self.copy_name_btn = ttk.Button(self.app_name_frame, text="Copy", command=None)
        self.copy_name_btn.pack(side='right', padx=(10, 0))

        # Paketname und Kopieren-Button
        self.package_name_frame = tk.Frame(self.app_info_frame, bg="#ffffff")
        self.package_name_frame.pack(fill='x', padx=10)

        self.package_name = tk.Label(self.package_name_frame, text="Packet Name: ", bg="#ffffff")
        self.package_name.pack(side='left', anchor="w")

        self.copy_package_btn = ttk.Button(self.package_name_frame, text="Copy", command=None)
        self.copy_package_btn.pack(side='right', padx=(10, 0))

        # Größe
        self.size = tk.Label(self.app_info_frame, text="Size: None", bg="#ffffff")
        self.size.pack(anchor="w", padx=10)

        # Daten und Cache löschen
        self.clear_data_btn = ttk.Button(self.app_info_frame, text="Clear Data", command=self.clear_data)
        self.clear_data_btn.pack(pady=(10, 5), padx=10, fill='x')

        self.clear_cache_btn = ttk.Button(self.app_info_frame, text="Clear Cache", command=self.clear_cache)
        self.clear_cache_btn.pack(pady=(5, 10), padx=10, fill='x')

        self.app_info()


    def app_info(self):
        try:
            selected_apps = [self.listbox_apks.item(i)['values'][0] for i in self.listbox_apks.selection()]


            if selected_apps:
                app_name = selected_apps[0]
                command_package = f"adb shell pm path {app_name}"
                output_package = subprocess.check_output(command_package, shell=True).decode().strip()

                if output_package:
                    package_name_value = output_package.split(":")[1].strip()

                    # Verwende du, um die Größe der APK zu ermitteln
                    command_size = f"adb shell du -b {package_name_value}"  # Verwende -b für Bytes
                    output_size = subprocess.check_output(command_size, shell=True).decode().strip()

                    only_name = app_name.split('.')


                    # Größe in Bytes extrahieren
                    size_in_bytes = self.get_size_in_bytes(output_size)

                    if size_in_bytes is not None:
                        self.package_name.config(text=f"Packet Name: {app_name}")
                        human_readable_size = self.human_readable_size(size_in_bytes)
                        self.size.config(text=f"Size: {human_readable_size}")
                        self.app_name.config(text=only_name)
                    else:
                        self.package_name.config(text=f"Packet Name: {package_name_value}")
                        self.size.config(text="Size: Keine Informationen gefunden.")
                else:
                    self.package_name.config(text="Paket nicht gefunden.")
                    self.size.config(text="Size: Keine Informationen gefunden.")

            else:
                self.package_name.config(text="Packet Name: None")
                self.size.config(text="Size: None")

        except subprocess.CalledProcessError as e:
            self.package_name.config(text="Fehler beim Abrufen der App-Größe.")
            self.size.config(text=str(e))

    def get_size_in_bytes(self, output):
        # Die Größe ist das erste Element in der Ausgabe
        parts = output.split()
        if len(parts) >= 1:  # Überprüfe, ob die Zeile genug Teile hat
            return int(parts[0])  # Rückgabe von Größe in Bytes als Integer

        return None  # Wenn keine Größe gefunden wurde

    def human_readable_size(self, size_in_bytes):
        """Konvertiere die Größe in eine lesbare Form (KB, MB, GB)."""
        if size_in_bytes < 1024:
            return f"{size_in_bytes} Bytes"
        elif size_in_bytes < 1024 ** 2:
            return f"{size_in_bytes / 1024:.2f} KB"
        elif size_in_bytes < 1024 ** 3:
            return f"{size_in_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{size_in_bytes / (1024 ** 3):.2f} GB"

    def on_canvas_click(self, event):
        # Überprüfe, ob der text_frame bereits existiert
        if self.text_frame is None:  # Nur erstellen, wenn es noch nicht existiert

            # Create the text widget with a scrollbar inside a frame
            self.text_frame = tk.Frame(self.master, height=300, background="grey")
            self.text_frame.pack(fill=tk.Y, expand=True)

            
            self.safe_info.place(relx=0.93, rely=0.5)
            self.safe_info.config(command=self.save_batt_text)

            self.text_widget = tk.Text(self.text_frame, wrap=tk.WORD, yscrollcommand=self.scrollbar.set, background="#1D1D1D", foreground="white")
            self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH)


            self.scrollbar = ttk.Scrollbar(self.text_frame, orient="vertical", command=self.text_widget.yview, style="Vertical.TScrollbar")
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            battery_info = subprocess.check_output([adb_path, "shell", "dumpsys", "battery"], text=True)

            text_info = (

                f"{battery_info}"
            )


            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert(tk.END, text_info)  # Neuer Inhalt einfügen
            self.update_scrollregion(None)



            self.text_widget.config(state=tk.DISABLED)


            self.scrollbar.config(command=self.text_widget.yview)


            # Setze den Fokus auf das Textfeld, damit es sofort bearbeitet werden kann
            self.text_widget.focus_set()
           
        else: # Wenn der Frame bereits existiert, verstecke ihn
            self.hide_text_frame()


    def on_root_click(self, event):
        # Finde das Widget unter dem Mauszeiger
        widget = self.master.winfo_containing(event.x_root, event.y_root)

        # Wenn der Klick außerhalb des Text-Widgets und des Canvas ist, schließe das Text-Frame
        if self.text_frame and widget not in (self.text_widget, self.canvas, self.text_frame):
            self.hide_text_frame()




    def hide_text_frame(self):
        """Verstecke das Text-Frame und setze die Referenzen zurück."""
        self.text_frame.pack_forget()  # Verstecke das Frame
        self.text_widget.delete("1.0", tk.END)
        self.safe_info.place_forget()
        self.text_frame = None  # Setze die Referenz zurück
        self.text_widget = None  # Setze das Text-Widget zurück

    def save_batt_text(self):
        # Holen Sie den Text aus dem Text-Widget
        text_to_save = self.text_widget.get("1.0", tk.END)  # get("1.0", "end") gibt den gesamten Text zurück

        # Öffnen Sie einen Dialog zur Auswahl des Speicherorts
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                   filetypes=[("Textdateien", "*.txt"),
                                                              ("Alle Dateien", "*.*")])

        if file_path:  # Prüfen, ob ein Dateipfad ausgewählt wurde
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(text_to_save.strip())  # Text in die Datei schreiben und Whitespace entfernen
            



    def get_battery_info(self):
        """Funktion zum Abrufen des Akkustatus über ADB."""
        try:
            result = subprocess.check_output(['adb', 'shell', 'dumpsys', 'battery'], encoding='utf-8')
            battery_info = {}
            for line in result.splitlines():
                if 'level' in line:
                    battery_info['level'] = int(line.split(": ")[1])
                if 'status' in line:
                    battery_info['status'] = int(line.split(": ")[1])  # 2 = Charging
                if 'plugged' in line:
                    battery_info['plugged'] = int(line.split(": ")[1])  # 1 = AC, 2 = USB, 4 = Wireless
            
            return battery_info
        except subprocess.CalledProcessError as e:
            
            return {"level": 0, "status": 0}

    def draw_static_battery(self):
        """Zeichnet das statische Batteriesymbol (verkleinert)."""
        # Rechteck für die Batterie (verkleinert)
        self.canvas.create_rectangle(5, 5, 50, 25, outline="black", width=2)  # Hauptbatterie
        self.canvas.create_rectangle(50, 10, 53, 20, outline="black", width=2, fill="black")  # Batteriekopf





    def update_battery_fill(self, level):
        """Aktualisiert den farbigen Teil, der den Ladezustand anzeigt."""
        fill_width = 45 * (level / 100)  # Dynamische Breite basierend auf Akku-Level

        # Bestimme die Farbe basierend auf dem Akkustand
        if level > 75:
            fill_color = "green"
        elif 50 < level <= 75:
            fill_color = "yellow"
        elif 25 < level <= 50:
            fill_color = "orange"
        else:
            fill_color = "red"

        # Falls bereits ein Ladezustand angezeigt wurde, diesen löschen
        if self.battery_fill_id:
            self.canvas.delete(self.battery_fill_id)

        # Neuer Ladezustand als farbiges Rechteck
        self.battery_fill_id = self.canvas.create_rectangle(
            6, 6, 6 + fill_width, 24, outline="", fill=fill_color
        )

    def update_battery_text(self, level):
        """Aktualisiert nur den Text im Batteriesymbol."""
        if self.battery_text_id:
            self.canvas.delete(self.battery_text_id)

        # Neuer Text für den Akkustand (in Prozent), zentriert in der Batterie
        self.battery_text_id = self.canvas.create_text(
            32, 15, text=f"{level}%", font=("Arial", 8), fill="blue"  # Blauer Text
        )

    def update_charging_symbol(self, is_charging, charge_type):
        """Aktualisiert das Blitzsymbol basierend auf dem Ladestatus und der Ladeart."""
        if self.charging_symbol_id:
            self.canvas.delete(self.charging_symbol_id)

        # Wähle die Farbe basierend auf der Ladeart
        if charge_type == 1:  # AC Charging (Schnelles Laden)
            lightning_color = "green"
        elif charge_type == 2:  # USB Charging (Langsames Laden)
            lightning_color = "blue"
        elif charge_type == 4:  # Wireless Charging
            lightning_color = "orange"
        else:
            lightning_color = "gray"  # Kein Laden

        if is_charging:
            # Blitz links neben dem Text
            self.charging_symbol_id = self.canvas.create_text(
                15, 15, text="⚡", font=("Arial", 10), fill=lightning_color  # Blitz links vom Text
            )
        else:
            self.charging_symbol_id = None  # Wenn nicht laden, kein Blitz anzeigen

    def update_battery_status(self):
        """Aktualisiert den Akkustand und lädt nur die erforderlichen Teile neu."""
        info = self.get_battery_info()
        battery_level = info.get('level', 0)
        is_charging = info.get('status', 0) == 2  # 2 = Charging
        charge_type = info.get('plugged', 0)  # Ladeart bestimmen

        

        if battery_level != self.battery_level:
            self.update_battery_fill(battery_level)
            self.update_battery_text(battery_level)
            self.battery_level = battery_level

        if is_charging != self.is_charging or charge_type != self.charge_type:
            self.update_charging_symbol(is_charging, charge_type)
            self.is_charging = is_charging
            self.charge_type = charge_type

        # Update alle 5 Sekunden
        self.master.after(5000, self.update_battery_status)

    # Funktion, um zu prüfen, ob das Gerät im Recovery-Modus ist
    def check_recovery_mode(self):
        try:
            
            result = subprocess.run([adb_path, 'get-state'], capture_output=True, text=True)
            if "recovery" in result.stdout:
                return True
            else:
                return False
        except Exception as e:
            self.console_output.insert(tk.END, f"Fehler beim Überprüfen des Modus: {e}\n")
            return False

    # Funktion, um das Gerät in den Recovery-Modus zu rebooten
    def reboot_to_recovery(self):
        try:
            self.console_output.insert(tk.END, "\n\n\n---------- Start Remove Lockscreen ----------\n\n\n")

            subprocess.run([adb_path, 'reboot', 'recovery'], capture_output=True, text=True)
            self.console_output.insert(tk.END, "\nGerät wird in den Recovery-Modus neugestartet...\n")
        except Exception as e:
            self.console_output.insert(tk.END, f"\nFehler beim Neustarten in den Recovery-Modus: {e}\n")

    # Funktion, um gezielte Dateien in /data zu löschen
    def start_delete_threads(self):
        # Startet den Löschvorgang in einem separaten Thread
        delete_thread = threading.Thread(target=self.delete_key_files_in_background)
        delete_thread.start()

    def delete_key_files_in_background(self):
        def delete_files():
            # Zuerst die Dateien aus self.files_to_delete löschen
            for file_path in self.files_to_delete:
                try:
                    check_file = subprocess.run([self.adb_path, 'shell', 'test', '-e', file_path], capture_output=True, text=True)
                    if check_file.returncode == 0:  # Datei existiert
                        subprocess.run([self.adb_path, 'shell', 'rm', '-f', file_path], capture_output=True, text=True)
                        self.console_output.insert(tk.END, f"\nDatei {file_path} wurde gelöscht.\n", 'del')
                    else:
                        self.console_output.insert(tk.END, f"\nDatei {file_path} existiert nicht.\n")
                except Exception as e:
                    self.console_output.insert(tk.END, f"Fehler beim Löschen von {file_path}: {str(e)}\n", 'error')
            
            # Nun alle .key-Dateien im /data-Verzeichnis suchen und löschen
            files = []
            directory = "/data/system"
            try:
                command = f"{self.adb_path} shell find \"{directory}\" -name \"*.key\""
                process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')

                # Zugriff auf stdout und stderr
                stdout = process.stdout
                stderr = process.stderr

                if process.returncode != 0:
                    self.console_output.insert(tk.END, f"Fehler: {stderr}\n", 'error')
                    self.console_output.see(tk.END)
                    return

                for line in stdout.splitlines():
                    line = line.strip()
                    if line:  # Prüfen, ob die Zeile nicht leer ist
                        files.append(line)
                        # Lösche die gefundene .key-Datei
                        delete_command = f"{self.adb_path} shell rm -f \"{line}\""
                        delete_process = subprocess.run(delete_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')

                        if delete_process.returncode == 0:
                            self.console_output.insert(tk.END, f"Datei {line} wurde gelöscht.\n", 'del')
                        else:
                            self.console_output.insert(tk.END, f"Fehler beim Löschen von {line}: {delete_process.stderr}\n", 'error')

                if not files:
                    self.console_output.insert(tk.END, "Keine .key-Dateien mehr gefunden.\n")
                    rcommand = f"{self.adb_path} reboot"
                    r_process = subprocess.run(rcommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
                    self.console_output.insert(tk.END, f"\nFertig Gerät wird neu gestartet\n", 'del')
            except Exception as e:
                self.console_output.insert(tk.END, f"Fehler: {str(e)}\n", 'error')
                self.console_output.see(tk.END)

        # Starte die Datei-Löschung in einem separaten Thread, um die GUI nicht zu blockieren
        thread = threading.Thread(target=delete_files)
        thread.start()


    # Funktion, um auf den Recovery-Modus zu warten
    def wait_for_recovery_mode(self):
        self.console_output.insert(tk.END, "\nWarte, bis das Gerät in den Recovery-Modus wechselt...\n")
        while not self.check_recovery_mode():
            time.sleep(5)  # Warte 5 Sekunden, bevor erneut überprüft wird
        self.console_output.insert(tk.END, "\nGerät ist jetzt im Recovery-Modus.\n")

    # Funktion, um das Gerät neu zu starten
    def reboot_device(self):
        try:
            subprocess.run([adb_path, 'reboot'], capture_output=True, text=True)
            self.console_output.insert(tk.END, "\n\n\n-------------- Finish --------------\n\n\n", 'del')

            self.console_output.insert(tk.END, "\nGerät wird nun neugestartet...\nIf it ask for a Passwort, type a random Passwort\n", 'del')
        except Exception as e:
            self.console_output.insert(tk.END, f"Fehler beim Neustart des Geräts: {e}\n")

    # Hauptfunktion: Überprüfe den Modus und lösche Dateien
    def check_and_delete_files(self):
        if not self.check_recovery_mode():
            # Falls das Gerät nicht im Recovery-Modus ist, starte es in den Recovery-Modus neu
            self.reboot_to_recovery()
            
            # Warte, bis das Gerät im Recovery-Modus ist
            self.wait_for_recovery_mode()

        # Überprüfe erneut, ob das Gerät im Recovery-Modus ist
        if self.check_recovery_mode():
            self.console_output.insert(tk.END, "Gerät ist im Recovery-Modus. Lösche nun die angegebenen Dateien...\n")
            self.delete_files_in_data()

            # Gerät nach dem Löschen neu starten
            self.reboot_device()
        else:
            self.console_output.insert(tk.END, "Das Gerät ist nicht im Recovery-Modus. Dateien konnten nicht gelöscht werden.\n")

    # Funktion für den Button-Click in einem separaten Thread
    def start_delete_thread(self):
        threading.Thread(target=self.check_and_delete_files).start()

    def only_numbers(self, new_value):
        if new_value.isdigit() or new_value == "":  # Akzeptiere nur Zahlen oder leere Eingabe
            return True
        else:
            return False

    def check_root_status(self):
        # Command to check root status
        result = subprocess.run([self.adb_path, 'shell', 'su', '-c', 'whoami'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # If output contains 'root', the device is rooted
        if "root" in result.stdout:
            self.status_label.config(text="Root Status: Device Rooted", fg="green")
        else:
            self.status_label.config(text="Root Status: Device Unrooted", fg="red")


    def start_selection(self, event):
        """Startet die Auswahl, wenn die linke Maustaste gedrückt wird."""
        index = self.listbox_apks.identify_row(event.y)  # Nächsten Index basierend auf der Mausposition erhalten
        self.listbox_apks.selection_set(index)  # Setzt die Auswahl

    def select_with_drag(self, event):
        """Ermöglicht die Auswahl mehrerer Apps beim Ziehen mit gedrückter Maustaste."""
        if self.is_mouse_down:  # Überprüfe, ob die Maustaste gedrückt ist
            index = self.listbox_apks.identify_row(event.y)  # Nächsten Index basierend auf der Mausposition erhalten
            self.listbox_apks.selection_set(index)  # Setzt die Auswahl

    def end_selection(self, event):
        """Beendet die Auswahl, wenn die linke Maustaste losgelassen wird."""
        self.is_mouse_down = False  # Setzt das Flag zurück

    def clear_selection(self, event):
        """Hebt alle Auswahlen in der Listbox auf, wenn ein Rechtsklick erkannt wird."""
        self.listbox_apks.selection_clear(0, tk.END)


    def toggle_selection(self, event):
        """Hebt die Auswahl der App auf, wenn die Maus darüber fährt und die linke Maustaste gedrückt ist."""
        if self.is_mouse_down:  # Überprüfe, ob die Maustaste gedrückt ist
            index = self.listbox_apks.nearest(event.y)  # Nächsten Index basierend auf der Mausposition erhalten
            if index >= 0:  # Überprüfe, ob der Index gültig ist
                if self.listbox_apks.selection_includes(index):  # Überprüfe, ob die App bereits ausgewählt ist
                    self.listbox_apks.selection_clear(index)  # Wenn ja, abwählen
                else:
                    self.listbox_apks.selection_set(index)  # Wenn nicht, auswählen




    def load_apks(self):
        """Lädt die Benutzer-APKs von ADB und zeigt sie im Treeview an."""
        try:
            # ADB Befehl, um nur User-Apps zu erhalten
            result = subprocess.run(['adb', 'shell', 'pm', 'list', 'packages', '-3'], capture_output=True, text=True)
            
            if result.returncode != 0:
                #self.console_output.insert("ADB Fehler: " + result.stderr.strip())
                pass
            # Pakete aus der Ausgabe filtern und formatieren
            packages = result.stdout.splitlines()
            packages = [pkg.replace("package:", "") for pkg in packages]
            self.apps = packages  # Speichere die User-Apps
            self.displayed_apps = self.apps.copy()  # Kopiere die Liste in displayed_apps
            self.update_listbox_apks()  # Aktualisiere das Treeview
            return packages
        except Exception as e:
            messagebox.showerror("Fehler", str(e))
            return []

    def load_all(self):
        """Lädt die Benutzer-APKs von ADB und zeigt sie im Treeview an."""
        try:
            # ADB Befehl, um nur User-Apps zu erhalten
            result = subprocess.run(['adb', 'shell', 'pm', 'list', 'packages'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("ADB Fehler: " + result.stderr.strip())

            # Pakete aus der Ausgabe filtern und formatieren
            packages = result.stdout.splitlines()
            packages = [pkg.replace("package:", "") for pkg in packages]
            self.apps = packages  # Speichere die User-Apps
            self.displayed_apps = self.apps.copy()  # Kopiere die Liste in displayed_apps
            self.update_listbox_apks()  # Aktualisiere das Treeview
            return packages
        except Exception as e:
            messagebox.showerror("Fehler", str(e))
            return []
    
    def load_system_apps(self):
        """Lädt die Benutzer-APKs von ADB und zeigt sie im Treeview an."""
        try:
            # ADB Befehl, um nur User-Apps zu erhalten
            result = subprocess.run(['adb', 'shell', 'pm', 'list', 'packages', '-s'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("ADB Fehler: " + result.stderr.strip())

            # Pakete aus der Ausgabe filtern und formatieren
            packages = result.stdout.splitlines()
            packages = [pkg.replace("package:", "") for pkg in packages]
            self.apps = packages  # Speichere die User-Apps
            self.displayed_apps = self.apps.copy()  # Kopiere die Liste in displayed_apps
            self.update_listbox_apks()  # Aktualisiere das Treeview
            return packages
        except Exception as e:
            messagebox.showerror("Fehler", str(e))
            return []

    def update_listbox_apks(self):
        """Aktualisiert die Treeview mit den geladenen APKs."""
        # Treeview leeren
        self.listbox_apks.delete(*self.listbox_apks.get_children())
        
        # Füge die Apps zur Treeview hinzu
        for app in self.displayed_apps:
            self.listbox_apks.insert("", tk.END, values=(app,))   # Füge die Apps zur Listbox hinzu

    def search_apks(self, event=None):
        search_term = self.search_app_var.get().lower()  # Den aktuellen Suchbegriff aus der search_var holen
        self.listbox_apks.delete(*self.listbox_apks.get_children())  # Leere das Treeview

        if search_term:
            # Filtere die Apps, die den Suchbegriff enthalten
            filtered_apps = [app for app in self.apps if search_term in app.lower()]
        else:
            # Zeige alle Apps, wenn kein Suchbegriff eingegeben wurde
            filtered_apps = self.apps.copy()
        
        # Füge die gefilterten Apps zum Treeview hinzu
        for app in filtered_apps:
            self.listbox_apks.insert('', 'end', values=(app,))  # Angenommen, app ist der Paketname, der in einer Spalte angezeigt wird

    def refresh_app_list(self):
        # User-Apps laden
        self.load_apks()

    def refresh_all_list(self):
        # Alle Apps laden
        self.load_all()


    def refresh_system_list(self):
        # Alle Apps laden
        self.load_system_apps()

    def select_listbox(self, selected_action):
        # Prüfen, welche Auswahl in der Combobox getroffen wurde
        if selected_action == self.texts['Nur Benutzer APPS']:
            self.refresh_app_list()  # User-Apps laden
        elif selected_action == self.texts['Alle APPS']:
            self.refresh_all_list()  # Alle Apps (System + User) laden
        elif selected_action == self.texts['Nur System APPS']:
            self.refresh_system_list() 
        

    def select_backup_option(self, selected_action):
        # Prüfen, welche Auswahl in der Combobox getroffen wurde
        if selected_action == self.texts['Sichere alle APPS']:
            self.backup_all_apkss()  # User-Apps laden
        elif selected_action == self.texts['Sichere ausgewählte APPS']:
            self.backup_selected_apps()  # Alle Apps (System + User) laden
        
   
    def select_p_option(self, selected_action):
 
        if selected_action == self.texts['Kamera']:
            self.load_camera_apps()
        elif selected_action == self.texts['Mikrofon']:
            self.load_microphone_apps()
        elif selected_action == self.texts['Speicher lesen']:
            self.load_read_storage_apps()
        elif selected_action == self.texts['Speicher schreiben']:
            self.load_write_storage_apps()
        elif selected_action == self.texts['Feiner Standort']:
            self.load_fine_location_apps()
        elif selected_action == self.texts['Grob Standort']:
            self.load_coarse_location_apps()
        elif selected_action == self.texts['SMS senden']:
            self.load_send_sms_apps()
        elif selected_action == self.texts['SMS empfangen']:
            self.load_receive_sms_apps()
        elif selected_action == self.texts['Internet']:
            self.load_internet_apps()
        elif selected_action == self.texts['Kontakte lesen']:
            self.load_read_contacts_apps()
        elif selected_action == self.texts['Kontakte schreiben']:
            self.load_write_contacts_apps()
        elif selected_action == self.texts['Anrufliste lesen']:
            self.load_call_log_apps()
        elif selected_action == self.texts['Anrufliste schreiben']:
            self.load_write_call_log_apps()
        elif selected_action == self.texts['Telefonstatus lesen']:
            self.load_read_phone_state_apps()
        elif selected_action == self.texts['Anrufe tätigen']:
            self.load_call_phone_apps()
        elif selected_action == self.texts['Ausgehende Anrufe verarbeiten']:
            self.load_process_outgoing_calls_apps()
        elif selected_action == self.texts['Körpersensoren']:
            self.load_body_sensors_apps()
        elif selected_action == self.texts['Bluetooth']:
            self.load_bluetooth_apps()
        elif selected_action == self.texts['Bluetooth-Administration']:
            self.load_bluetooth_admin_apps()
        elif selected_action == self.texts['WLAN-Status ändern']:
            self.load_change_wifi_state_apps()
        elif selected_action == self.texts['WLAN-Status anzeigen']:
            self.load_access_wifi_state_apps()
        elif selected_action == self.texts['NFC']:
            self.load_nfc_apps()
        elif selected_action == self.texts['Netzwerkstatus anzeigen']:
            self.load_access_network_state_apps()
        elif selected_action == self.texts['Beim Start ausführen']:
            self.load_receive_boot_completed_apps()
        elif selected_action == self.texts['System-Overlay']:
            self.load_system_alert_window_apps()
        elif selected_action == self.texts['Systemeinstellungen ändern']:
            self.load_write_settings_apps()
        elif selected_action == self.texts['Fingerabdrucksensor verwenden']:
            self.load_use_fingerprint_apps()
        elif selected_action == self.texts['Konten abrufen']:
            self.load_get_accounts_apps()
        elif selected_action == self.texts['Biometrische Authentifizierung verwenden']:
            self.load_use_biometric_apps()
        elif selected_action == self.texts['Hintergrund-Standortzugriff']:
            self.load_access_background_location_apps()
        elif selected_action == self.texts['Batterieoptimierung ignorieren']:
            self.load_request_ignore_battery_optimizations_apps()
        elif selected_action == self.texts['Vordergrunddienst']:
            self.load_foreground_service_apps()
        elif selected_action == self.texts['Vibration']:
            self.load_vibrate_apps()
        elif selected_action == self.texts['Sichtbarkeit des Geräts']:
            self.load_device_visibility_apps()
        elif selected_action == self.texts['WLAN-Verbindung']:
            self.load_wifi_connection_apps()
        elif selected_action == self.texts['APN ändern']:
            self.load_change_apn_apps()
        elif selected_action == self.texts['Standortdienste']:
            self.load_location_services_apps()
        elif selected_action == self.texts['Statusbar anpassen']:
            self.load_customize_status_bar_apps()
        elif selected_action == self.texts['Systemapps nutzen']:
            self.load_use_system_apps()
        elif selected_action == self.texts['Mediendateien abspielen']:
            self.load_play_media_files_apps()
        elif selected_action == self.texts['Kalender lesen']:
            self.load_read_calendar_apps()
        elif selected_action == self.texts['Kalender ändern']:
            self.load_write_calendar_apps()
        elif selected_action == self.texts['Zugriff auf die Benutzeroberfläche']:
            self.load_access_ui_apps()
        elif selected_action == self.texts['Zugriff auf die Hardware']:
            self.load_access_hardware_apps()
        elif selected_action == self.texts['Bluetooth-Admin']:
            self.load_bluetooth_admin_apps()
        elif selected_action == self.texts['Task-Manager']:
            self.load_task_manager_apps()
        elif selected_action == self.texts['Einstellungen ändern']:
            self.load_change_settings_apps()
        elif selected_action == self.texts['Ereignisse überwachen']:
            self.load_monitor_events_apps()
        elif selected_action == self.texts['Standortdienste verwenden']:
            self.load_use_location_services_apps()
        elif selected_action == self.texts['Fehlersuche']:
            self.load_debugging_apps()
        elif selected_action == self.texts['Zugriff auf Benachrichtigungen']:
            self.load_access_notifications_apps()
        elif selected_action == self.texts['Root-Zugriff']:
            self.load_root_access_apps()
        elif selected_action == self.texts['Superuser-Zugriff']:
            self.load_superuser_access_apps()
        elif selected_action == self.texts['Zugriff auf Systemdateien']:
            self.load_access_system_files_apps()
        elif selected_action == self.texts['Zugriff auf alle Anwendungen']:
            self.load_access_all_apps_apps()
        elif selected_action == self.texts['Zugriff auf gesperrte Apps']:
            self.load_access_locked_apps_apps()
        elif selected_action == self.texts['Zugriff auf versteckte Apps']:
            self.load_access_hidden_apps_apps()
        elif selected_action == self.texts['Zugriff auf interne Speicherorte']:
            self.load_access_internal_storage_apps()
        elif selected_action == self.texts['Zugriff auf die Systemoberfläche']:
            self.load_access_system_interface_apps()
        elif selected_action == self.texts['Zugriff auf das Dateisystem']:
            self.load_access_file_system_apps()
        elif selected_action == self.texts['Zugriff auf Hardware-Sensoren']:
            self.load_access_hardware_sensors_apps()
        elif selected_action == self.texts['Zugriff auf Systemdienste']:
            self.load_access_system_services_apps()
        elif selected_action == self.texts['Zugriff auf die Registrierungsdatenbank']:
            self.load_access_registry_apps()
        else:
            print("Unbekannte Option:", selected_action)
        
        


    def select_up_option(self, selected_action):
        if selected_action == self.texts['Kamera']:
            self.unload_camera_apps()
        elif selected_action == self.texts['Mikrofon']:
            self.unload_microphone_apps()
        elif selected_action == self.texts['Speicher lesen']:
            self.unload_read_storage_apps()
        elif selected_action == self.texts['Speicher schreiben']:
            self.unload_write_storage_apps()
        elif selected_action == self.texts['Feiner Standort']:
            self.unload_fine_location_apps()
        elif selected_action == self.texts['Grob Standort']:
            self.unload_coarse_location_apps()
        elif selected_action == self.texts['SMS senden']:
            self.unload_send_sms_apps()
        elif selected_action == self.texts['SMS empfangen']:
            self.unload_receive_sms_apps()
        elif selected_action == self.texts['Internet']:
            self.unload_internet_apps()
        elif selected_action == self.texts['Kontakte lesen']:
            self.unload_read_contacts_apps()
        elif selected_action == self.texts['Kontakte schreiben']:
            self.unload_write_contacts_apps()
        elif selected_action == self.texts['Anrufliste lesen']:
            self.unload_call_log_apps()
        elif selected_action == self.texts['Anrufliste schreiben']:
            self.unload_write_call_log_apps()
        elif selected_action == self.texts['Telefonstatus lesen']:
            self.unload_read_phone_state_apps()
        elif selected_action == self.texts['Anrufe tätigen']:
            self.unload_call_phone_apps()
        elif selected_action == self.texts['Ausgehende Anrufe verarbeiten']:
            self.unload_process_outgoing_calls_apps()
        elif selected_action == self.texts['Körpersensoren']:
            self.unload_body_sensors_apps()
        elif selected_action == self.texts['Bluetooth']:
            self.unload_bluetooth_apps()
        elif selected_action == self.texts['Bluetooth-Administration']:
            self.unload_bluetooth_admin_apps()
        elif selected_action == self.texts['WLAN-Status ändern']:
            self.unload_change_wifi_state_apps()
        elif selected_action == self.texts['WLAN-Status anzeigen']:
            self.unload_access_wifi_state_apps()
        elif selected_action == self.texts['NFC']:
            self.unload_nfc_apps()
        elif selected_action == self.texts['Netzwerkstatus anzeigen']:
            self.unload_access_network_state_apps()
        elif selected_action == self.texts['Beim Start ausführen']:
            self.unload_receive_boot_completed_apps()
        elif selected_action == self.texts['System-Overlay']:
            self.unload_system_alert_window_apps()
        elif selected_action == self.texts['Systemeinstellungen ändern']:
            self.unload_write_settings_apps()
        elif selected_action == self.texts['Fingerabdrucksensor verwenden']:
            self.unload_use_fingerprint_apps()
        elif selected_action == self.texts['Konten abrufen']:
            self.unload_get_accounts_apps()
        elif selected_action == self.texts['Biometrische Authentifizierung verwenden']:
            self.unload_use_biometric_apps()
        elif selected_action == self.texts['Hintergrund-Standortzugriff']:
            self.unload_access_background_location_apps()
        elif selected_action == self.texts['Batterieoptimierung ignorieren']:
            self.unload_request_ignore_battery_optimizations_apps()
        elif selected_action == self.texts['Vordergrunddienst']:
            self.unload_foreground_service_apps()
        elif selected_action == self.texts['Vibration']:
            self.unload_vibrate_apps()
        elif selected_action == self.texts['Sichtbarkeit des Geräts']:
            self.unload_device_visibility_apps()
        elif selected_action == self.texts['WLAN-Verbindung']:
            self.unload_wifi_connection_apps()
        elif selected_action == self.texts['APN ändern']:
            self.unload_change_apn_apps()
        elif selected_action == self.texts['Standortdienste']:
            self.unload_location_services_apps()
        elif selected_action == self.texts['Statusbar anpassen']:
            self.unload_customize_status_bar_apps()
        elif selected_action == self.texts['Systemapps nutzen']:
            self.unload_use_system_apps()
        elif selected_action == self.texts['Mediendateien abspielen']:
            self.unload_play_media_files_apps()
        elif selected_action == self.texts['Kalender lesen']:
            self.unload_read_calendar_apps()
        elif selected_action == self.texts['Kalender ändern']:
            self.unload_write_calendar_apps()
        elif selected_action == self.texts['Zugriff auf die Benutzeroberfläche']:
            self.unload_access_ui_apps()
        elif selected_action == self.texts['Zugriff auf die Hardware']:
            self.unload_access_hardware_apps()
        elif selected_action == self.texts['Bluetooth-Admin']:
            self.unload_bluetooth_admin_apps()
        elif selected_action == self.texts['Task-Manager']:
            self.unload_task_manager_apps()
        elif selected_action == self.texts['Einstellungen ändern']:
            self.unload_change_settings_apps()
        elif selected_action == self.texts['Ereignisse überwachen']:
            self.unload_monitor_events_apps()
        elif selected_action == self.texts['Standortdienste verwenden']:
            self.unload_use_location_services_apps()
        elif selected_action == self.texts['Fehlersuche']:
            self.unload_debugging_apps()
        elif selected_action == self.texts['Zugriff auf Benachrichtigungen']:
            self.unload_access_notifications_apps()
        elif selected_action == self.texts['Root-Zugriff']:
            self.unload_root_access_apps()
        elif selected_action == self.texts['Superuser-Zugriff']:
            self.unload_superuser_access_apps()
        elif selected_action == self.texts['Zugriff auf Systemdateien']:
            self.unload_access_system_files_apps()
        elif selected_action == self.texts['Zugriff auf alle Anwendungen']:
            self.unload_access_all_apps_apps()
        elif selected_action == self.texts['Zugriff auf gesperrte Apps']:
            self.unload_access_locked_apps_apps()
        elif selected_action == self.texts['Zugriff auf versteckte Apps']:
            self.unload_access_hidden_apps_apps()
        elif selected_action == self.texts['Zugriff auf interne Speicherorte']:
            self.unload_access_internal_storage_apps()
        elif selected_action == self.texts['Zugriff auf die Systemoberfläche']:
            self.unload_access_system_interface_apps()
        elif selected_action == self.texts['Zugriff auf das Dateisystem']:
            self.unload_access_file_system_apps()
        elif selected_action == self.texts['Zugriff auf Hardware-Sensoren']:
            self.unload_access_hardware_sensors_apps()
        elif selected_action == self.texts['Zugriff auf Systemdienste']:
            self.unload_access_system_services_apps()
        elif selected_action == self.texts['Zugriff auf die Registrierungsdatenbank']:
            self.unload_access_registry_apps()
        else:
            print("Unbekannte Option:", selected_action)
        

    def execute_action(self, selected_action):

        
        try:
            # Für die Aktion "App Installieren" keine Auswahlüberprüfung
            if selected_action == "App Installieren":
                self.install_apk()
                return  # Nach der Installation beenden

            # Für alle anderen Aktionen Überprüfung, ob eine App ausgewählt wurde
            selected_index = self.listbox_apks.selection()
            if not selected_index:
                messagebox.showerror("Error", self.texts['adb_error2'])
                return

            selected_app = self.listbox_apks.item(selected_index[0])

            # Führe die entsprechende Aktion aus
            if selected_action == self.texts['App Installieren']:
                self.delete_selected_apps()
            elif selected_action == self.texts['App Starten']:
                self.start_app(selected_app)
            elif selected_action == self.texts['App Stoppen']:
                self.stop_app(selected_app)
            elif selected_action == self.texts['Cache löschen']:
                self.clear_cache()
            elif selected_action == self.texts['Daten löschen']:
                self.clear_data()
            else:
                messagebox.showerror("Fehler", self.texts['adb_error3'])
        except Exception as e:
            messagebox.showerror("Error", str(e))
        
        




    #####################################################################################

    def load_camera_apps(self):
        self.load_permission("android.permission.CAMERA")

    def load_microphone_apps(self):
        self.load_permission("android.permission.RECORD_AUDIO")

    def load_read_storage_apps(self):
        self.load_permission("android.permission.READ_EXTERNAL_STORAGE")

    def load_write_storage_apps(self):
        self.load_permission("android.permission.WRITE_EXTERNAL_STORAGE")

    def load_fine_location_apps(self):
        self.load_permission("android.permission.ACCESS_FINE_LOCATION")

    def load_coarse_location_apps(self):
        self.load_permission("android.permission.ACCESS_COARSE_LOCATION")

    def load_send_sms_apps(self):
        self.load_permission("android.permission.SEND_SMS")

    def load_receive_sms_apps(self):
        self.load_permission("android.permission.RECEIVE_SMS")

    def load_internet_apps(self):
        self.load_permission("android.permission.INTERNET")

    def load_read_contacts_apps(self):
        self.load_permission("android.permission.READ_CONTACTS")

    def load_write_contacts_apps(self):
        self.load_permission("android.permission.WRITE_CONTACTS")

    def load_call_log_apps(self):
        self.load_permission("android.permission.READ_CALL_LOG")

    def load_write_call_log_apps(self):
        self.load_permission("android.permission.WRITE_CALL_LOG")

    def load_read_phone_state_apps(self):
        self.load_permission("android.permission.READ_PHONE_STATE")

    def load_call_phone_apps(self):
        self.load_permission("android.permission.CALL_PHONE")

    def load_process_outgoing_calls_apps(self):
        self.load_permission("android.permission.PROCESS_OUTGOING_CALLS")

    def load_body_sensors_apps(self):
        self.load_permission("android.permission.BODY_SENSORS")

    def load_bluetooth_apps(self):
        self.load_permission("android.permission.BLUETOOTH")

    def load_bluetooth_admin_apps(self):
        self.load_permission("android.permission.BLUETOOTH_ADMIN")

    def load_change_wifi_state_apps(self):
        self.load_permission("android.permission.CHANGE_WIFI_STATE")

    def load_access_wifi_state_apps(self):
        self.load_permission("android.permission.ACCESS_WIFI_STATE")

    def load_nfc_apps(self):
        self.load_permission("android.permission.NFC")

    def load_access_network_state_apps(self):
        self.load_permission("android.permission.ACCESS_NETWORK_STATE")

    def load_receive_boot_completed_apps(self):
        self.load_permission("android.permission.RECEIVE_BOOT_COMPLETED")

    def load_system_alert_window_apps(self):
        self.load_permission("android.permission.SYSTEM_ALERT_WINDOW")

    def load_write_settings_apps(self):
        self.load_permission("android.permission.WRITE_SETTINGS")

    def load_use_fingerprint_apps(self):
        self.load_permission("android.permission.USE_FINGERPRINT")

    def load_get_accounts_apps(self):
        self.load_permission("android.permission.GET_ACCOUNTS")

    def load_use_biometric_apps(self):
        self.load_permission("android.permission.USE_BIOMETRIC")

    def load_access_background_location_apps(self):
        self.load_permission("android.permission.ACCESS_BACKGROUND_LOCATION")

    def load_request_ignore_battery_optimizations_apps(self):
        self.load_permission("android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS")

    def load_foreground_service_apps(self):
        self.load_permission("android.permission.FOREGROUND_SERVICE")

    def load_vibrate_apps(self):
        self.load_permission("android.permission.VIBRATE")

    def load_device_visibility_apps(self):
        self.load_permission("android.permission.CHANGE_DEVICE_ANIMATION");

    def load_wifi_connection_apps(self):
        self.load_permission("android.permission.ACCESS_WIFI_STATE")

    def load_change_apn_apps(self):
        self.load_permission("android.permission.CHANGE_APN")

    def load_location_services_apps(self):
        self.load_permission("android.permission.ACCESS_LOCATION_EXTRA_COMMANDS")

    def load_customize_status_bar_apps(self):
        self.load_permission("android.permission.STATUS_BAR_SERVICE")

    def load_use_system_apps(self):
        self.load_permission("android.permission.MANAGE_SYSTEM_APPS")

    def load_play_media_files_apps(self):
        self.load_permission("android.permission.READ_MEDIA_AUDIO")

    def load_read_calendar_apps(self):
        self.load_permission("android.permission.READ_CALENDAR")

    def load_write_calendar_apps(self):
        self.load_permission("android.permission.WRITE_CALENDAR")

    def load_access_ui_apps(self):
        self.load_permission("android.permission.SYSTEM_UI")

    def load_access_hardware_apps(self):
        self.load_permission("android.permission.HARDWARE_TEST")

    def load_task_manager_apps(self):
        self.load_permission("android.permission.KILL_BACKGROUND_PROCESSES")

    def load_change_settings_apps(self):
        self.load_permission("android.permission.WRITE_SETTINGS")

    def load_monitor_events_apps(self):
        self.load_permission("android.permission.READ_EXTERNAL_STORAGE")

    def load_use_location_services_apps(self):
        self.load_permission("android.permission.ACCESS_FINE_LOCATION")

    def load_debugging_apps(self):
        self.load_permission("android.permission.READ_LOGS")

    def load_access_notifications_apps(self):
        self.load_permission("android.permission.ACCESS_NOTIFICATION_POLICY")

    def load_root_access_apps(self):
        self.load_permission("android.permission.ACCESS_SUPERUSER");

    def load_superuser_access_apps(self):
        self.load_permission("android.permission.ACCESS_SUPERUSER");

    def load_access_system_files_apps(self):
        self.load_permission("android.permission.READ_EXTERNAL_STORAGE");

    def load_access_all_apps_apps(self):
        self.load_permission("android.permission.QUERY_ALL_PACKAGES");

    def load_access_locked_apps_apps(self):
        self.load_permission("android.permission.PACKAGE_USAGE_STATS");

    def load_access_hidden_apps_apps(self):
        self.load_permission("android.permission.MANAGE_EXTERNAL_STORAGE");

    def load_access_internal_storage_apps(self):
        self.load_permission("android.permission.MANAGE_EXTERNAL_STORAGE");

    def load_access_system_interface_apps(self):
        self.load_permission("android.permission.WRITE_SETTINGS");

    def load_access_file_system_apps(self):
        self.load_permission("android.permission.READ_EXTERNAL_STORAGE");

    def load_access_hardware_sensors_apps(self):
        self.load_permission("android.permission.BODY_SENSORS");

    def load_access_system_services_apps(self):
        self.load_permission("android.permission.BIND_ACCESSIBILITY_SERVICE");

    def load_access_registry_apps(self):
        self.load_permission("android.permission.READ_LOGS");


######################


    def unload_camera_apps(self):
        self.unload_permission("android.permission.CAMERA")

    def unload_microphone_apps(self):
        self.unload_permission("android.permission.RECORD_AUDIO")

    def unload_read_storage_apps(self):
        self.unload_permission("android.permission.READ_EXTERNAL_STORAGE")

    def unload_write_storage_apps(self):
        self.unload_permission("android.permission.WRITE_EXTERNAL_STORAGE")

    def unload_fine_location_apps(self):
        self.unload_permission("android.permission.ACCESS_FINE_LOCATION")

    def unload_coarse_location_apps(self):
        self.unload_permission("android.permission.ACCESS_COARSE_LOCATION")

    def unload_send_sms_apps(self):
        self.unload_permission("android.permission.SEND_SMS")

    def unload_receive_sms_apps(self):
        self.unload_permission("android.permission.RECEIVE_SMS")

    def unload_internet_apps(self):
        self.unload_permission("android.permission.INTERNET")

    def unload_read_contacts_apps(self):
        self.unload_permission("android.permission.READ_CONTACTS")

    def unload_write_contacts_apps(self):
        self.unload_permission("android.permission.WRITE_CONTACTS")

    def unload_call_log_apps(self):
        self.unload_permission("android.permission.READ_CALL_LOG")

    def unload_write_call_log_apps(self):
        self.unload_permission("android.permission.WRITE_CALL_LOG")

    def unload_read_phone_state_apps(self):
        self.unload_permission("android.permission.READ_PHONE_STATE")

    def unload_call_phone_apps(self):
        self.unload_permission("android.permission.CALL_PHONE")

    def unload_process_outgoing_calls_apps(self):
        self.unload_permission("android.permission.PROCESS_OUTGOING_CALLS")

    def unload_body_sensors_apps(self):
        self.unload_permission("android.permission.BODY_SENSORS")

    def unload_bluetooth_apps(self):
        self.unload_permission("android.permission.BLUETOOTH")

    def unload_bluetooth_admin_apps(self):
        self.unload_permission("android.permission.BLUETOOTH_ADMIN")

    def unload_change_wifi_state_apps(self):
        self.unload_permission("android.permission.CHANGE_WIFI_STATE")

    def unload_access_wifi_state_apps(self):
        self.unload_permission("android.permission.ACCESS_WIFI_STATE")

    def unload_nfc_apps(self):
        self.unload_permission("android.permission.NFC")

    def unload_access_network_state_apps(self):
        self.unload_permission("android.permission.ACCESS_NETWORK_STATE")

    def unload_receive_boot_completed_apps(self):
        self.unload_permission("android.permission.RECEIVE_BOOT_COMPLETED")

    def unload_system_alert_window_apps(self):
        self.unload_permission("android.permission.SYSTEM_ALERT_WINDOW")

    def unload_write_settings_apps(self):
        self.unload_permission("android.permission.WRITE_SETTINGS")

    def unload_use_fingerprint_apps(self):
        self.unload_permission("android.permission.USE_FINGERPRINT")

    def unload_get_accounts_apps(self):
        self.unload_permission("android.permission.GET_ACCOUNTS")

    def unload_use_biometric_apps(self):
        self.unload_permission("android.permission.USE_BIOMETRIC")

    def unload_access_background_location_apps(self):
        self.unload_permission("android.permission.ACCESS_BACKGROUND_LOCATION")

    def unload_request_ignore_battery_optimizations_apps(self):
        self.unload_permission("android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS")

    def unload_foreground_service_apps(self):
        self.unload_permission("android.permission.FOREGROUND_SERVICE")

    def unload_vibrate_apps(self):
        self.unload_permission("android.permission.VIBRATE")

    def unload_device_visibility_apps(self):
        self.unload_permission("android.permission.CHANGE_DEVICE_ANIMATION");

    def unload_wifi_connection_apps(self):
        self.unload_permission("android.permission.ACCESS_WIFI_STATE")

    def unload_change_apn_apps(self):
        self.unload_permission("android.permission.CHANGE_APN")

    def unload_location_services_apps(self):
        self.unload_permission("android.permission.ACCESS_LOCATION_EXTRA_COMMANDS")

    def unload_customize_status_bar_apps(self):
        self.unload_permission("android.permission.STATUS_BAR_SERVICE")

    def unload_use_system_apps(self):
        self.unload_permission("android.permission.MANAGE_SYSTEM_APPS")

    def unload_play_media_files_apps(self):
        self.unload_permission("android.permission.READ_MEDIA_AUDIO")

    def unload_read_calendar_apps(self):
        self.unload_permission("android.permission.READ_CALENDAR")

    def unload_write_calendar_apps(self):
        self.unload_permission("android.permission.WRITE_CALENDAR")

    def unload_access_ui_apps(self):
        self.unload_permission("android.permission.SYSTEM_UI")

    def unload_access_hardware_apps(self):
        self.unload_permission("android.permission.HARDWARE_TEST")

    def unload_task_manager_apps(self):
        self.unload_permission("android.permission.KILL_BACKGROUND_PROCESSES")

    def unload_change_settings_apps(self):
        self.unload_permission("android.permission.WRITE_SETTINGS")

    def unload_monitor_events_apps(self):
        self.unload_permission("android.permission.READ_EXTERNAL_STORAGE")

    def unload_use_location_services_apps(self):
        self.unload_permission("android.permission.ACCESS_FINE_LOCATION")

    def unload_debugging_apps(self):
        self.unload_permission("android.permission.READ_LOGS")

    def unload_access_notifications_apps(self):
        self.unload_permission("android.permission.ACCESS_NOTIFICATION_POLICY")

    def unload_root_access_apps(self):
        self.unload_permission("android.permission.ACCESS_SUPERUSER");

    def unload_superuser_access_apps(self):
        self.unload_permission("android.permission.ACCESS_SUPERUSER");

    def unload_access_system_files_apps(self):
        self.unload_permission("android.permission.READ_EXTERNAL_STORAGE");

    def unload_access_all_apps_apps(self):
        self.unload_permission("android.permission.QUERY_ALL_PACKAGES");

    def unload_access_locked_apps_apps(self):
        self.unload_permission("android.permission.PACKAGE_USAGE_STATS");

    def unload_access_hidden_apps_apps(self):
        self.unload_permission("android.permission.MANAGE_EXTERNAL_STORAGE");

    def unload_access_internal_storage_apps(self):
        self.unload_permission("android.permission.MANAGE_EXTERNAL_STORAGE");

    def unload_access_system_interface_apps(self):
        self.unload_permission("android.permission.WRITE_SETTINGS");

    def unload_access_file_system_apps(self):
        self.unload_permission("android.permission.READ_EXTERNAL_STORAGE");

    def unload_access_hardware_sensors_apps(self):
        self.unload_permission("android.permission.BODY_SENSORS");

    def unload_access_system_services_apps(self):
        self.unload_permission("android.permission.BIND_ACCESSIBILITY_SERVICE");

    def unload_access_registry_apps(self):
        self.unload_permission("android.permission.READ_LOGS");



    def load_permission(self, permission):
        try:
            selected_item = self.listbox_apks.selection()
            if not selected_item:
                raise Exception("Keine App ausgewählt")

            # Paketname aus dem Treeview extrahieren
            selected_app = self.listbox_apks.item(selected_item)['values'][0]  # Annahme: Paketname ist der erste Wert
            
            # ADB-Befehl zum Entfernen der Berechtigung
            result = subprocess.run(['adb', 'shell', 'pm', 'grant', selected_app, permission], capture_output=True, text=True)
            if result.returncode == 0:
                self.console_output.insert(tk.END, f"{self.texts['Erfolgt1']} {selected_app}\n")
            else:
                self.console_output.insert(tk.END, f"{self.texts['error']} {selected_app}\n")
        except Exception as e:
            self.console_output.insert(tk.END, f"{str(e)}\n")

    def unload_permission(self, permission):
        try:
            # Abrufen des aktuell ausgewählten Elements im Treeview
            selected_item = self.listbox_apks.selection()
            if not selected_item:
                raise Exception("Keine App ausgewählt")

            # Paketname aus dem Treeview extrahieren
            selected_app = self.listbox_apks.item(selected_item)['values'][0]  # Annahme: Paketname ist der erste Wert
            
            # ADB-Befehl zum Entfernen der Berechtigung
            result = subprocess.run(['adb', 'shell', 'pm', 'revoke', selected_app, permission], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console_output.insert(tk.END, f"{self.texts['Erfolgt2']} {selected_app}\n")
            else:
                self.console_output.insert(tk.END, f"{self.texts['error2']} {selected_app}: {result.stderr}\n")
        except Exception as e:
            self.console_output.insert(tk.END, str(e) + "\n")



    #########################################################################################


    def start_app(self, app):
        try:
            selected_items = self.listbox_apks.selection()  # Holt die IDs der ausgewählten Elemente
            if not selected_items:
                raise Exception("Keine App ausgewählt")

            # Hier nehmen wir an, dass wir den ersten ausgewählten Eintrag verwenden möchten
            selected_app_id = selected_items[0]  # Nimm die ID des ersten ausgewählten Elements
            selected_app = self.listbox_apks.item(selected_app_id)['values'][0]  # Hier wird der Wert (z.B. Paketname) abgerufen

            # ADB Befehl zum Starten der App
            result = subprocess.run(['adb', 'shell', 'monkey', '-p', selected_app, '-c', 'android.intent.category.LAUNCHER', '1'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console_output.insert(tk.END, f"{self.texts['start_erfolg']} {selected_app}\n")
            else:
                self.console_output.insert(tk.END, f"{self.texts['start_error']} {selected_app}\n")
        except Exception as e:
            self.console_output.insert(tk.END, str(e) + "\n")  # Fehlerausgabe an die Konsole



    def clear_data(self):
        """Löscht die Daten der ausgewählten App."""
        try:
            # Abrufen der aktuell ausgewählten App im Treeview
            selected_item = self.listbox_apks.selection()
            if not selected_item:
                raise Exception("Keine App ausgewählt")

            # Paketname aus dem Treeview extrahieren
            selected_app = self.listbox_apks.item(selected_item)['values'][0]  # Annahme: Paketname ist der erste Wert
            command = f"adb shell pm clear {selected_app}"

            # Ausführen des ADB-Befehls
            result = subprocess.run(command.split(), capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console_output.insert(tk.END, f"{self.texts['del_data_erfolg']}\n")
            else:
                self.console_output.insert(tk.END, f"{self.texts['del_data_error']}\n")
        except Exception as e:
            self.console_output(tk.END, str(e))


    def stop_app(self, app):
        try:
            # Abrufen der aktuell ausgewählten App im Treeview
            selected_item = self.listbox_apks.selection()
            if not selected_item:
                raise Exception("Keine App ausgewählt")

            # Paketname aus dem Treeview extrahieren
            selected_app = self.listbox_apks.item(selected_item)['values'][0]  # Annahme: Paketname ist der erste Wert
            command = f"adb shell am force-stop {selected_app}"

            # Ausführen des ADB-Befehls
            result = subprocess.run(command.split(), capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console_output.insert(tk.END, f"{self.texts['stop_app']}\n")
            else:
                self.console_output.insert(tk.END, f"{self.texts['no_stop_app']}\n")
                  # Fehler in der Konsole ausgeben
        except Exception as e:
            self.console_output.insert(tk.END, str(e),"\n")
              # Fehler in der Konsole ausgeben

    def clear_cache(self):
        try:
            # Abrufen der aktuell ausgewählten App im Treeview
            selected_item = self.listbox_apks.selection()
            if not selected_item:
                raise Exception("Keine App ausgewählt")

            # Paketname aus dem Treeview extrahieren
            selected_app = self.listbox_apks.item(selected_item)['values'][0]  # Annahme: Paketname ist der erste Wert
            command = f"adb shell pm clear {selected_app}"

            # Ausführen des ADB-Befehls
            result = subprocess.run(command.split(), capture_output=True, text=True)
            if result.returncode == 0:
                self.console_output.insert(tk.END, f"{self.texts['del_cache_erfolg']}\n")
            else:
                self.console_output.insert(tk.END, f"{self.texts['del_cache_eror']}\n")
                  # Fehler in der Konsole ausgeben
        except Exception as e:
            self.console_output.insert(tk.END, str(e),"\n")
             # Fehler in der Konsole ausgeben

    def backup_all_apkss(self):
        """Sichert alle installierten Benutzer-Apps (ohne System-Apps)."""
        all_apps = [self.listbox_apks.item(item)['values'][0] for item in self.listbox_apks.get_children()]
        
        # Filtere nur Benutzer-Apps (hier kannst du die Bedingung anpassen)
        selected_apps = [app for app in all_apps if "system" not in app]  

        if not selected_apps:
            self.console_output.insert(tk.END, "Keine Benutzer-Apps zum Sichern gefunden.\n")
            return

        # Speicherort nur einmal auswählen
        backup_directory = filedialog.askdirectory(title="Select Backup Folder")
        if not backup_directory:
            self.console_output.insert(tk.END, f"{self.texts['no_safe_place']}\n")
            return

        # Starte den Sicherungsprozess in einem neuen Thread
        threading.Thread(target=self.all_apk_backup, args=(selected_apps, backup_directory), daemon=True).start()

    def all_apk_backup(self, selected_apps, backup_directory):
        for app in selected_apps:
            self.console_output.insert(tk.END, f"{self.texts['backup_app']} {app}...\n")
            try:
                # Ermitteln des APK-Pfads
                command = f'"{self.adb_path}" shell pm path {app}'
                apk_path = subprocess.check_output(command, shell=True).decode('utf-8').strip().replace('package:', '')

                # APK sichern
                original_apk_name = f"{app.split('.')[-1]}.apk"  # Originalname der App
                destination_path = os.path.join(backup_directory, original_apk_name)

                pull_command = f'"{self.adb_path}" pull {apk_path} "{destination_path}"'
                subprocess.run(pull_command, shell=True)

                # Überprüfen, ob die gesicherte APK den Namen 'base.apk' hat
                if original_apk_name == "base.apk":
                    # Wenn der Name 'base.apk' ist, generiere einen benutzerfreundlicheren Namen
                    app_name = app.split('.')[-1]  # Der Name der App
                    destination_path = os.path.join(backup_directory, f"{app_name}.apk")  # Benenne die Datei um

                    # Die 'base.apk' umbenennen
                    os.rename(destination_path, f"{backup_directory}/{app_name}.apk")
                    
                self.console_output.insert(tk.END, f"{app} {self.texts['safet_to']} {destination_path}!\n")

            except subprocess.CalledProcessError as e:
                self.console_output.insert(tk.END, f"{self.texts['safe_error']} {app}: {e}\n")
            except Exception as e:
                self.console_output.insert(tk.END, f"Fehler: {str(e)}\n")



    def get_apk_path(self, package_name):
        """Gibt den Pfad der Haupt-APK einer App zurück."""
        try:
            command = [self.adb_path, 'shell', 'pm', 'path', package_name]
            output = subprocess.check_output(command).decode('utf-8').strip()
            return output.replace('package:', '')  # Rückgabe des Pfads
        except subprocess.CalledProcessError:
            return None

    def get_split_apk_paths(self, package_name):
        """Findet alle Split-APKs für das angegebene Paket."""
        try:
            command = [self.adb_path, 'shell', 'pm', 'path', package_name]
            output = subprocess.check_output(command).decode('utf-8').strip().split('\n')
            split_apk_paths = []
            for line in output:
                if "split" in line:
                    split_apk_paths.append(line.replace('package:', ''))  # Rückgabe des Pfads
            return split_apk_paths
        except subprocess.CalledProcessError:
            return []

    def get_obb_path(self, package_name):
        """Findet den OBB-Pfad für das angegebene Paket."""
        obb_path = f"/storage/emulated/0/Android/obb/{package_name}/"
        return obb_path

    def is_busybox_installed(self):
        """Überprüfen, ob BusyBox auf dem Gerät installiert ist"""
        
        result = subprocess.run([self.adb_path, 'shell', 'which', 'busybox'], capture_output=True, text=True)
        
        # Prüfen, ob der Befehl erfolgreich ausgeführt wurde und BusyBox gefunden wurde
        if result.returncode == 0 and result.stdout.strip() != "":
            
            return True
        else:
            
            return False

    def check_and_install_busybox(self):
        """Prüfen, ob BusyBox installiert ist und ggf. installieren"""
        if not self.is_busybox_installed():
            messagebox.showinfo({self.texts['no_busybox_installed']})
            
        else:
            pass

    def load_partitions(self):
        partitions = self.get_partitions()
        if partitions:
            self.ddbackupbox.delete(0, tk.END)  # Löscht vorherige Einträge in der Listbox
            for partition in partitions:
                size = self.get_partition_size(partition)
                if size:
                    partition_display = f"{partition} - {size}"
                    self.ddbackupbox.insert(tk.END, partition_display)

    def get_partitions(self):
        """Ermittelt alle Partitionen auf dem Gerät"""
        result = subprocess.run([self.adb, 'shell', 'ls', '/dev/block/by-name/'], capture_output=True, text=True)
        if result.returncode == 0:
            partitions = result.stdout.splitlines()
            return partitions
        else:
            messagebox.showerror("error", {self.texts['adb_error1']})
            return []

    def get_partition_size(self, partition_name):
        """Versuche, die Größe der Partition zu erhalten"""
        
         # Debug-Ausgabe

        # Verwende den Befehl blockdev für eine 64-Bit-Größe
        blockdev_command = f"blockdev --getsize64 /dev/block/by-name/{partition_name}"

        result = subprocess.run([self.adb_path, 'shell', 'su', '-c', blockdev_command], capture_output=True, text=True)
        
        if result.returncode == 0:
              # Debug-Ausgabe
            size_in_bytes = int(result.stdout.strip())  # Extrahiere die Größe in Bytes
            
            return self.convert_size(size_in_bytes)  # Aufruf der Instanzmethode
            
        else:
            
            return None

    def convert_size(self, size_in_bytes):
        """Konvertiert die Größe von Bytes in MB oder GB"""
        size_in_mb = size_in_bytes / (1024 * 1024)
        if size_in_mb > 1024:
            return f"{size_in_mb / 1024:.2f} GB"
        else:
            return f"{size_in_mb:.2f} MB"

    def save_selected_partitions(self):
        # Starte einen neuen Thread für das Laden der installierten Apps
        threading.Thread(target=self.start_save_selected_partitions).start()
        
    def start_save_selected_partitions(self):
        selected_indices = self.ddbackupbox.curselection()  # Ausgewählte Indizes
        selected_partitions = [self.ddbackupbox.get(i).split(' - ')[0] for i in selected_indices]  # Extrahiert die Partitionen

        if selected_partitions:
            self.backup_partitions_directly(selected_partitions)
        else:
            messagebox.showwarning("Error", {self.texts['no_partition_select']})

    def backup_partitions_directly(self, partitions):
        """Funktion zum Sichern mehrerer Partitionen direkt auf den PC"""
        save_dir = filedialog.askdirectory(title="Ordner für Partition-Sicherungen auswählen")
        if save_dir:
            for partition in partitions:
                save_path = os.path.join(save_dir, f"{partition}.img")

                # Befehl, um dd über adb zu verwenden und die Partition direkt auf den PC zu streamen
                partition_backup_command = f"busybox dd if=/dev/block/by-name/{partition}"

                # Prozess zum Ausführen des ADB-Befehls starten
                process = subprocess.Popen([self.adb_path, 'shell', 'su', '-c', partition_backup_command], stdout=subprocess.PIPE)

                self.console_output.insert(tk.END, f"{partition} {self.texts['safe_partition']}\n")
                self.console_output.see(tk.END)

                total_size = self.get_partition_size_bytes(partition)  # Gesamtgröße der Partition in Bytes
                bytes_read = 0

                with open(save_path, 'wb') as out_file:
                    for chunk in iter(lambda: process.stdout.read(4096), b''):
                        out_file.write(chunk)
                        bytes_read += len(chunk)

                        # Fortschritt aktualisieren
                        progress = (bytes_read / total_size) * 100
                        self.progress_bar['value'] = progress
                        self.master.update_idletasks()
                self.console_output.insert(tk.END, f"{partition} {self.texts['safe_erfolg']} {save_path}\n")
                self.console_output.see(tk.END)

    def restore_selected_partitions(self):
        # Starte einen neuen Thread für das Laden der installierten Apps
        threading.Thread(target=self.start_restore_selected_partitions).start()

    def start_restore_selected_partitions(self):
        selected_indices = self.ddbackupbox.curselection()  # Ausgewählte Indizes
        selected_partitions = [self.ddbackupbox.get(i).split(' - ')[0] for i in selected_indices]  # Extrahiert die Partitionen

        if selected_partitions:
            self.restore_partitions_directly(selected_partitions)
        else:
            pass


    def restore_partitions_directly(self, partitions):
        """Funktion zum Wiederherstellen mehrerer Partitionen direkt vom PC auf das Gerät."""
        file_paths = filedialog.askopenfilenames(title="Partition-Image-Dateien auswählen", filetypes=[("Image-Dateien", "*.img")])
        
        if file_paths:
            for file_path in file_paths:
                partition_name = os.path.basename(file_path).split('.')[0]  # Partition basierend auf dem Dateinamen extrahieren
                if partition_name not in partitions:
                    continue  # Wenn die Partition nicht in der Auswahl ist, überspringe sie

                # Befehl zum Wiederherstellen der Partition von der .img-Datei auf das Gerät
                partition_restore_command = f"busybox dd of=/dev/block/by-name/{partition_name}"

                # Prozess zum Ausführen des ADB-Befehls starten
                process = subprocess.Popen(
                    [self.adb_path, 'shell', 'su', '-c', partition_restore_command],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                self.console_output.insert(tk.END, f"{self.texts['restor_start']} {partition_name}\n")
                self.console_output.see(tk.END)

                with open(file_path, 'rb') as img_file:
                    while True:
                        chunk = img_file.read(4096)
                        if not chunk:
                            break
                        

                process.stdin.close()
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    self.console_output.insert(tk.END, f"{partition_name} {self.texts['restore_erfolg']}\n")
                else:
                    self.console_output.insert(tk.END, f"{self.texts['Restore_error']} {partition_name}: {stderr.decode()}\n")

                self.console_output.see(tk.END)

    def get_partition_size_bytes(self, partition_name):
        """Ermittelt die Größe der Partition in Bytes"""
        blockdev_command = f"blockdev --getsize64 /dev/block/by-name/{partition_name}"
        result = subprocess.run([self.adb_path, 'shell', 'su', '-c', blockdev_command], capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())  # Größe in Bytes
        else:
            return 0
        
    def start_data(self):
        try:
            # Schreibe den Ladehinweis in das Textfeld (Konsolenoutput)
            self.console_output.insert(tk.END, f"{self.texts['start_data']}\n")
            self.console_output.see(tk.END)  # Scrollt automatisch nach unten
            
            # Starte die exe-Datei
            self.process = subprocess.Popen(["data.exe"])
            
            # Warte 2 Sekunden und überprüfe dann, ob das Programm läuft
            self.master.after(2000, self.check_ift_running)
            
        except Exception as e:
            messagebox.showerror("Error", f"{self.texts['start_data_error']} {e}")

    def check_ift_running(self):
        # Überprüfe, ob das Programm läuft
        if self.process is not None:
            if psutil.pid_exists(self.process.pid):
                # Programm läuft: Lösche die Zeile mit "Screen Share wird geladen..." und füge neuen Text hinzu
                pass
                
            else:
                # Programm ist geschlossen worden
                pass
        else:
            pass
                

    def start_screen_share(self):
        try:
            # Schreibe den Ladehinweis in das Textfeld (Konsolenoutput)
            self.console_output.insert(tk.END, f"{self.texts['start_screen']}\n")
            self.console_output.see(tk.END)  # Scrollt automatisch nach unten
            
            # Starte die exe-Datei
            self.process = subprocess.Popen([r"tools\scrcpy\scrcpy.exe"])
            
            # Warte 2 Sekunden und überprüfe dann, ob das Programm läuft
            self.master.after(2000, self.check_if_running)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"{self.texts['start_data_error']} {e}")

    def check_if_running(self):
        # Überprüfe, ob das Programm läuft
        if self.process is not None:
            if psutil.pid_exists(self.process.pid):
                # Programm läuft: Lösche die Zeile mit "Screen Share wird geladen..." und füge neuen Text hinzu
                pass  # Lösche nur die Zeile mit dem Text
                
            else:
                # Programm ist geschlossen worden
                pass
        else:
            pass

    def remove_line(self, text):
        # Durchsuchen des gesamten Textes nach der Zeile mit dem Text
        lines = self.console_output.get("1.0", tk.END).splitlines()  # Alle Zeilen holen
        for i, line in enumerate(lines):
            if text in line:  # Wenn der Text in der Zeile enthalten ist
                # Lösche die Zeile, indem wir den entsprechenden Bereich angeben
                self.console_output.delete(f"{i+1}.0", f"{i+1}.end")
                break  # Beende die Schleife, wenn die Zeile gelöscht wurde




    def get_hotspot_status(self):
        """Überprüft den Hotspot-Status."""
        result = subprocess.run(f"{self.adb_path} shell dumpsys connectivity | findstr \"Tethering\"",
                                shell=True, capture_output=True, text=True)
        if "Tethering: TetheringEnabled" in result.stdout:
            return "ON"
        elif "Tethering: TetheringDisabled" in result.stdout:
            return "OFF"
        else:
            return "UNKNOWN"
        
    def toggle_hotspot(self):
        """Schaltet den Hotspot ein oder aus."""
        current_status = self.get_hotspot_status()
        if current_status == "ON":
            subprocess.run(f"{self.adb_path} shell svc wifi disable", shell=True)
            
        else:
            subprocess.run(f"{self.adb_path} shell svc wifi enable", shell=True)
            

    def update_hotspot_button(self):
        """Aktualisiert den Text des Hotspot Buttons je nach Status."""
        status = self.get_hotspot_status()
        if status == "ON":
            self.hotspot_button.config(image=self.hotspot_ico, bg="green")
        elif status == "OFF":
            self.hotspot_button.config(image=self.hotspot_ico, bg="red")
        else:
            self.hotspot_button.config(image=self.hotspot_ico, bg="gray")

    def update_hotspot_button_text(self):
        """Aktualisiert den Text des Buttons je nach mobilem Daten-Status."""
        self.update_hotspot_button() 
        self.master.after(5000, self.update_hotspot_button_text) 


    def get_mobile_data_status(self):
        """Überprüft den Status der mobilen Daten."""
        result = subprocess.run(f"{self.adb_path} shell settings get global mobile_data", 
                                shell=True, capture_output=True, text=True)
        if result.stdout.strip() == "1":
            return "ON"
        elif result.stdout.strip() == "0":
            return "OFF"
        else:
            return "UNKNOWN"
        
    def toggle_mobile_data(self):
        """Schaltet die mobilen Daten ein oder aus."""
        current_status = self.get_mobile_data_status()

        if current_status == "ON":
            # Mobile Daten ausschalten
            subprocess.run(f"{self.adb_path} shell svc data disable", shell=True)
            
        else:
            # Mobile Daten einschalten
            subprocess.run(f"{self.adb_path} shell svc data enable", shell=True)
           
        
        # Buttontext nach Status aktualisieren
        self.update_mobile_data_button_text()

    def update_mobile_data_button_text(self):
        """Aktualisiert den Text des Buttons je nach mobilem Daten-Status."""
        current_status = self.get_mobile_data_status()

        if current_status == "ON":
            self.data_button.config(image=self.data_ico, background="green")
        elif current_status == "OFF":
            self.data_button.config(image=self.data_ico, background="red")
        else:
            self.data_button.config(image=self.data_ico, background="yellow")

    def check_mobile_data_periodically(self):
        """Überprüft den Status der mobilen Daten alle 5 Sekunden."""
        self.update_mobile_data_button_text()  # Button-Text aktualisieren
        self.master.after(5000, self.check_mobile_data_periodically) 


    
    def get_gps_status(adb_path):
        """Überprüft, ob GPS aktiviert ist, indem die Ausgabe von dumpsys location analysiert wird."""
        result = subprocess.run(f"{adb_path} shell dumpsys location", shell=True, capture_output=True, text=True)
        
        # Suchen nach der Zeile, die den GPS-Status beschreibt
        if 'location [u0]' in result.stdout and 'enabled' in result.stdout:
            return "ON"  # GPS ist aktiviert
        else:
            return "OFF"  # GPS ist deaktiviert

    



    def get_wifi_status(self):
        """Überprüft den WLAN-Status durch Android-Systemeinstellungen."""
        result = subprocess.run(f"{self.adb_path} shell settings get global wifi_on", 
                                shell=True, capture_output=True, text=True)
        
        if result.stdout.strip() == "1":
            return "ON"
        elif result.stdout.strip() == "0":
            return "OFF"
        else:
            return "UNKNOWN"
        
    def check_wifi_periodically(self):
        """Überprüft den WLAN-Status alle 5 Sekunden."""
        self.update_wifi_button_text()  # Aktualisiere den WLAN-Button-Text
        self.master.after(5000, self.check_wifi_periodically)


    
    
    
    def get_bluetooth_status(self):
        """Überprüft den Bluetooth-Status durch Android-Systemeinstellungen."""
        result = subprocess.run(f"{adb_path} shell settings get global bluetooth_on", 
                                shell=True, capture_output=True, text=True)
        if result.stdout.strip() == "1":
            return "ON"
        elif result.stdout.strip() == "0":
            return "OFF"
        else:
            return "UNKNOWN"
        
    def check_bluetooth_periodically(self):
        """Überprüft den Bluetooth-Status alle 5 Sekunden."""
        self.update_bluetooth_text()  # Aktualisiere den Button-Text
        self.master.after(5000, self.check_bluetooth_periodically) 



    def update_gps_text(self):
        """Aktualisiert den Text des Buttons je nach GPS-Status."""
        gps_status = self.get_gps_status()
        
        if gps_status == "ON":
            self.gps_button.config(image=self.gps_ico, background="Green")
        elif gps_status == "OFF":
            self.gps_button.config(image=self.gps_ico, background="Red")
        else:
            self.gps_button.config(text="gps Status unbekannt")

    def check_gps_periodically(self):
        """Überprüft den WLAN-Status alle 5 Sekunden."""
        self.update_gps_text()  # Aktualisiere den WLAN-Button-Text
        self.master.after(5000, self.check_gps_periodically)

    def toggle_wifi(self):
        """Schaltet WLAN ein oder aus, je nachdem, ob es gerade aktiviert oder deaktiviert ist."""
        current_status = self.get_wifi_status()

        if current_status == "ON":
            # WLAN ausschalten
            adb_command = f"{self.adb_path} shell svc wifi disable"
            subprocess.run(adb_command, shell=True)
            
        else:
            # WLAN einschalten
            adb_command = f"{self.adb_path} shell svc wifi enable"
            subprocess.run(adb_command, shell=True)
            

        # Buttontext nach Status aktualisieren
        self.update_wifi_button_text()


    def update_wifi_button_text(self):
        """Aktualisiert den Text des WLAN-Buttons je nach Status."""
        current_status = self.get_wifi_status()

        if current_status == "ON":
            self.wifi_button.config(image=self.wifi_ico, background="Green")
        elif current_status == "OFF":
            self.wifi_button.config(image=self.wifi_ico, background="Red")
        else:
            self.wifi_button.config(text="WLAN Status unbekannt")

        

    def toggle_bluetooth(self):
        """Schaltet Bluetooth ein oder aus, je nachdem, ob es gerade aktiviert oder deaktiviert ist."""
        current_status = self.get_bluetooth_status()

        if current_status == "ON":
            # Bluetooth ausschalten
            adb_command = f"{self.adb_path} shell am start -a android.bluetooth.adapter.action.REQUEST_DISABLE"
            subprocess.run(adb_command, shell=True)
            
        else:
            # Bluetooth einschalten
            adb_command = f"{self.adb_path} shell am start -a android.bluetooth.adapter.action.REQUEST_ENABLE"
            subprocess.run(adb_command, shell=True)
            
        
        # Buttontext nach Status aktualisieren
        self.get_bluetooth_status()
        self.update_bluetooth_text()

    def update_bluetooth_text(self):
        """Aktualisiert den Text des Buttons je nach Bluetooth-Status."""
        current_status = self.get_bluetooth_status()

        if current_status == "ON":
            self.bluetooth_button.config(image=self.bluetooth_ico, background="Green")
        elif current_status == "OFF":
            self.bluetooth_button.config(image=self.bluetooth_ico, background="red")
        else:
            self.bluetooth_button.config(text="Bluetooth Status unbekannt")

    def get_current_brightness(self):
        """Holt die aktuelle Helligkeit des Geräts."""
        adb_command = "adb shell settings get system screen_brightness"
        result = subprocess.run(adb_command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            return int(result.stdout.strip())
        else:
            
            return 128  # Standardwert falls Fehler auftreten

    def on_brightness_change(self, target_brightness):
        """Startet den Helligkeitsänderungsprozess in einem separaten Thread."""
        target_brightness = int(target_brightness)
        threading.Thread(target=self.set_brightness, args=(target_brightness,)).start()

    def set_brightness(self, value):
        """Setzt die Helligkeit auf dem Gerät basierend auf dem Sliderwert."""
        adb_command = f"adb shell settings put system screen_brightness {value}"
        subprocess.run(adb_command, shell=True)
        

    
    def set_volume(self):
        # Starte einen neuen Thread für das Laden der installierten Apps
        threading.Thread(target=self.start_set_volume).start()




    def get_current_volume(self):
        """Holt die aktuelle Medienlautstärke des Geräts über ADB."""
        adb_command = f"{self.adb_path} shell dumpsys audio"
        result = subprocess.run(adb_command, shell=True, capture_output=True, text=True)

        # Suche nach der aktuellen STREAM_MUSIC Lautstärke
        match = re.search(r'STREAM_BLUETOOTH_SCO*?index=\d+,\s*(\d+)', result.stdout)
        if match:
            current_volume = int(match.group(1))  # Aktuelle Lautstärke
            return current_volume
        else:
            
            return 7  # Standardwert, falls nichts gefunden wird

    def set_volume(self, target_volume):
        """Startet den Volume-Änderungsprozess in einem separaten Thread."""
        target_volume = int(target_volume)
        threading.Thread(target=self.start_set_volume, args=(target_volume,)).start()

    def start_set_volume(self, target_volume):
        """Steuert die Lautstärke über adb durch Senden von KEYEVENTs in einem separaten Thread."""
        if target_volume > self.current_volume:
            # Erhöhe die Lautstärke
            for _ in range(target_volume - self.current_volume):
                adb_command = f"{self.adb_path} shell input keyevent 24"  # KEYCODE_VOLUME_UP
                subprocess.run(adb_command, shell=True)
        elif target_volume < self.current_volume:
            # Verringere die Lautstärke
            for _ in range(self.current_volume - target_volume):
                adb_command = f"{self.adb_path} shell input keyevent 25"  # KEYCODE_VOLUME_DOWN
                subprocess.run(adb_command, shell=True)

        # Aktualisiere das aktuelle Volumen
        self.current_volume = target_volume

        # Aktualisiere das aktuelle Volumen
        self.current_volume = target_volume

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mouse_wheel(self, event):
        # Vertikales Scrollen
        self.canvas.yview_scroll(-1 * int((event.delta / 120)), "units")

    def _on_shift_mouse_wheel(self, event):
        # Horizontales Scrollen bei gedrückter Shift-Taste
        self.canvas.xview_scroll(-1 * int((event.delta / 120)), "units") 

    def get_device_info(self):
        # Starte einen neuen Thread für das Laden der installierten Apps
        threading.Thread(target=self.device_info).start()

    def update_scrollregion(self, event):
        """Aktualisiert die Scrollregion des Canvas."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))






    def device_info(self):
        """Informationen vom Gerät abrufen und im Label anzeigen."""
        
        try:
            # Gesamtspeicher abrufen
            storage = subprocess.check_output([adb_path, "shell", "df", "/data"], text=True)
            lines = storage.strip().splitlines()
            if len(lines) > 1:
                self.total_kb, used_kb, available_kb = map(int, lines[1].split()[1:4])
                self.total_gb = self.total_kb / 1024 / 1024
                self.used_gb = used_kb / 1024 / 1024
                self.available_gb = available_kb / 1024 / 1024

            # Android-Version abrufen
            self.version = subprocess.check_output([adb_path, "shell", "getprop", "ro.build.version.release"], text=True).strip()

            # Gerätemodell abrufen
            self.model = subprocess.check_output([adb_path, "shell", "getprop", "ro.product.model"], text=True).strip()

            # Hersteller abrufen
            self.manufacturer = subprocess.check_output([adb_path, "shell", "getprop", "ro.product.manufacturer"], text=True).strip()

            # Prozessorarchitektur abrufen
            self.cpu_abi = subprocess.check_output([adb_path, "shell", "getprop", "ro.product.cpu.abi"], text=True).strip()
            self.cpu_cores = subprocess.check_output([adb_path, "shell", "nproc"], text=True).strip()

            # RAM abrufen
            self.ram_info = subprocess.check_output([adb_path, "shell", "cat", "/proc/meminfo"], text=True)
            self.ram_lines = self.ram_info.strip().splitlines()
            self.total_ram = int(self.ram_lines[0].split()[1]) / 1024  # MemTotal
            self.free_ram = int(self.ram_lines[1].split()[1]) / 1024   # MemFree
            self.available_ram = int(self.ram_lines[2].split()[1]) / 1024  # MemAvailable

            # SIM-Karten-Informationen abrufen
            self.sim_state = subprocess.check_output([adb_path, "shell", "getprop", "gsm.sim.state"], text=True).strip()
            self.sim_host = subprocess.check_output([adb_path, "shell", "getprop", "gsm.sim.operator.alpha"], text=True).strip()
            self.ip_info = subprocess.check_output([adb_path, "shell", "ip", "address", "show", "wlan0"], text=True).strip()

            # Display-Infos
            self.display_auflösung = subprocess.check_output([adb_path, "shell", "wm", "size"], text=True).strip()
            self.pixeldichte = subprocess.check_output([adb_path, "shell", "wm", "density"], text=True).strip()
            self.display_helligkeit = subprocess.check_output([adb_path, "shell", "settings", "get", "system", "screen_brightness"], text=True).strip()

            # Bluetooth-Status abrufen
            self.bluetooth_status = subprocess.check_output([adb_path, "shell", "settings", "get", "global", "bluetooth_on"], text=True).strip()
            self.bluetooth_status = "Ein" if self.bluetooth_status == "1" else "Aus"

            # Akku-Informationen abrufen
            self.battery_info = subprocess.check_output([adb_path, "shell", "dumpsys", "battery"], text=True)

            # Audio-Infos (Lautstärkewerte)
            self.audio_info = subprocess.check_output([adb_path, "shell", "dumpsys", "audio"], text=True)
            
            # Bluetooth-Geräte suchen
            self.bluetooth_devices = []
            for line in self.audio_info.splitlines():
                if "mBluetoothName" in line:
                    match = re.search(r"mBluetoothName=(.+?)\s*\n", line)
                    if match:
                        device_name = match.group(1).strip()
                        self.bluetooth_devices.append(device_name)

            # Informationen in das Label einfügen
            self.update_label()
            self.switch_language()

        except subprocess.CalledProcessError as e:
            pass
        except Exception as e:
            pass

    def update_label(self):

        info_text = (
                f"\n\n{self.texts['Hersteller']}: {self.manufacturer}\n"
                f"{self.texts['device_model']}: {self.model}\n"
                f"{self.texts['android_version']}: {self.version}\n"
                f"{self.texts['cpu_architecture']}: {self.cpu_abi}\n"
                f"{self.texts['cpu_cores']}: {self.cpu_cores}\n\n"
                f"\n---- {self.texts['display']} ----\n"
                f"{self.texts['display_resolution']}: {self.display_auflösung}\n"
                f"{self.texts['pixel_density']}: {self.pixeldichte}\n"
                f"{self.texts['brightness']}: {self.display_helligkeit}\n"
                f"\n---- {self.texts['storage']} ----\n"
                f"{self.texts['total_storage']}: {self.total_gb:.2f} GB\n"
                f"{self.texts['used_storage']}: {self.used_gb:.2f} GB\n"
                f"{self.texts['free_storage']}: {self.available_gb:.2f} GB\n"
                f"\n---- {self.texts['ram']} ----\n"
                f"{self.texts['total_ram']}: {self.total_ram:.2f} MB\n"
                f"{self.texts['free_ram']}: {self.free_ram:.2f} MB\n"
                f"{self.texts['available_ram']}: {self.available_ram:.2f} MB\n"
                f"\n---- {self.texts['network_sim']} ----\n"
                f"{self.texts['sim_card_status']}: {self.sim_state}\n"
                f"{self.texts['sim_card_provider']}: {self.sim_host}\n"
                f"{self.texts['wifi']}: {self.ip_info}\n"
                f"\n---- {self.texts['bluetooth']} ----\n"
                f"{self.texts['bluetooth_status']}: {self.bluetooth_status}\n"     
                f"{self.texts['connected_devices']}: {', '.join(self.bluetooth_devices) if self.bluetooth_devices else self.texts['no_connected_devices']}\n"
                f"\n---- {self.texts['battery']} ----\n"
                f"\n{self.battery_info}\n"

            )

        self.info_label.config(state="normal")
        self.info_label.delete("1.0", tk.END)
        self.info_label.insert(tk.END, info_text)
        self.info_label.config(state="disabled")

    def update_info(self):
        self.info_label.config(text="info_text")
    
        self.info_label.after(1000, self.update_info)  # Führt `update_info` nach 1000 ms aus






    def update_device_info(self):
        """Aktualisiert die Informationen."""
        self.get_device_info() 



    def adb():
        adb_directory = r"platform-tools"
        os.environ["PATH"] += os.pathsep + adb_directory
    


    def check_adb_installed():
        try:
            adb_path = os.path.join(os.environ["PATH"], "adb.exe")
            if os.path.exists(adb_path):
                
                return True
            else:
                
                return False
        except Exception as e:
            
            return False



    def set_password(self):
        # Starte einen neuen Thread für das Laden der installierten Apps
        threading.Thread(target=self.set_start_password).start()

    def set_pin(self):
        # Starte einen neuen Thread für das Laden der installierten Apps
        threading.Thread(target=self.set_start_pin).start()

    def clear_password(self):
        # Starte einen neuen Thread für das Laden der installierten Apps
        threading.Thread(target=self.clear_start_password).start()

    def clear_pin(self):
        # Starte einen neuen Thread für das Laden der installierten Apps
        threading.Thread(target=self.clear_start_pin).start()

    def set_start_password(self):
        # Alte und neue Passwörter abfragen
        old_password = self.old_password_var.get()
        new_password = self.new_password_var.get()

        # Überprüfen, ob die Eingabefelder gültige Werte enthalten
        old_password_valid = old_password != "" and old_password != "OLD PASSWORD"  # Placeholder prüfen
        new_password_valid = new_password != "" and new_password != "NEW PASSWORD"  # Placeholder prüfen

        if new_password_valid:
            if old_password_valid:  # Wenn sowohl altes als auch neues Passwort vorhanden sind
                command = f"adb shell locksettings set-password --old '{old_password}' '{new_password}'"
            else:  # Wenn kein altes Passwort angegeben wurde
                command = f"adb shell locksettings set-password '{new_password}'"
        else:
            self.console_output.insert(tk.END, f"{self.texts['passwort_error1']}\n")
            self.console_output.yview(tk.END)
            return  # Verlasse die Methode, wenn das neue Passwort nicht gültig ist

        try:
            # Führen Sie den ADB-Befehl aus und leiten Sie die Ausgabe um
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            self.console_output.insert(tk.END, result.stdout)  # Füge die Standardausgabe hinzu
            self.console_output.insert(tk.END, result.stderr)   # Füge die Fehlerausgabe hinzu (falls vorhanden)
            self.console_output.yview(tk.END)  # Scrolle zum Ende des Textfelds
        except subprocess.CalledProcessError as e:
            self.console_output.insert(tk.END, f"{self.texts['passwort_error2']} {e}\n")
            self.console_output.yview(tk.END)  # Scrolle zum Ende des Textfelds


    def set_start_pin(self):
        # Alte und neue Passwörter abfragen
        old_pin = self.old_PIN_var.get()
        new_pin = self.new_PIN_var.get()

        # Überprüfen, ob die Eingabefelder gültige Werte enthalten
        old_password_valid = old_pin != "" and old_pin != "OLD PIN"  # Placeholder prüfen
        new_password_valid = new_pin != "" and new_pin != "OLD PIN"  # Placeholder prüfen

        if new_password_valid:
            if old_password_valid:  # Wenn sowohl altes als auch neues Passwort vorhanden sind
                command = f"adb shell locksettings set-pin --old '{old_pin}' '{new_pin}'"
            else:  # Wenn kein altes Passwort angegeben wurde
                command = f"adb shell locksettings set-pin '{new_pin}'"
        else:
            self.console_output.insert(tk.END, f"{self.texts['pin_error1']}\n")
            self.console_output.yview(tk.END)
            return  # Verlasse die Methode, wenn das neue Passwort nicht gültig ist

        try:
            # Führen Sie den ADB-Befehl aus und leiten Sie die Ausgabe um
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            self.console_output.insert(tk.END, result.stdout)  # Füge die Standardausgabe hinzu
            self.console_output.insert(tk.END, result.stderr)   # Füge die Fehlerausgabe hinzu (falls vorhanden)
            self.console_output.yview(tk.END)  # Scrolle zum Ende des Textfelds
        except subprocess.CalledProcessError as e:
            self.console_output.insert(tk.END, f"{self.texts['pin_error1']} {e}\n")
            self.console_output.yview(tk.END)  # Scrolle zum Ende des Textfelds

    def save_prop_text(self):
        # Holen Sie den Text aus dem Text-Widget
        text_to_save = self.info_label.get("1.0", tk.END)  # get("1.0", "end") gibt den gesamten Text zurück

        # Öffnen Sie einen Dialog zur Auswahl des Speicherorts
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                   filetypes=[("Textdateien", "*.txt"),
                                                              ("Alle Dateien", "*.*")])

        if file_path:  # Prüfen, ob ein Dateipfad ausgewählt wurde
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(text_to_save.strip())  # Text in die Datei schreiben und Whitespace entfernen
            


    # Funktion zum Löschen des Entsperr-Passworts
    def clear_start_pin(self):

        old_pin = self.old_PIN_var.get()
        try:
            command = f'"{adb_path}" shell locksettings clear --old {old_pin}'
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            
            self.console_output.insert(tk.END, f"{self.texts['del_passwort_erfolg']}\n")
        except subprocess.CalledProcessError:
            self.console_output.insert(tk.END, f"{self.texts['del_passwort_error']}\n")

    # Funktion zum Löschen des Entsperr-Passworts
    def clear_start_password(self):

        old_password = self.old_password_var.get()
        try:
            command = f'"{adb_path}" shell locksettings clear --old {old_password}'
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            
            self.console_output.insert(tk.END, f"{self.texts['del_passwort_erfolg']}\n")
        except subprocess.CalledProcessError:
            self.console_output.insert(tk.END, f"{self.texts['del_passwort_erfolg']}\n")


    def start_installation(self):
        # Installation in einem separaten Thread starten
        threading.Thread(target=self.install_adb).start()

    def log(self, message):
        # Ausgabe zur Konsole hinzufügen
        self.console_output.insert(tk.END, message + "\n")
        self.console_output.see(tk.END)  # Scrollen zum Ende

    def download_adb(self):
        self.log(f"{self.texts['download_adb']}\n")

        # Überprüfen, ob eine Internetverbindung besteht
        try:
            socket.create_connection(("www.google.com", 80))
        except OSError:
            self.log(f"{self.texts['no_wifi']}\n")
            return None  # Frühzeitiger Abbruch, wenn keine Verbindung besteht

        response = requests.get(ADB_URL, stream=True)
        zip_path = os.path.join(os.getcwd(), "platform-tools.zip")
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        start_time = time.time()  # Startzeit für die Geschwindigkeitsberechnung

        with open(zip_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=128):
                if chunk:  # Sicherstellen, dass der Chunk nicht leer ist
                    file.write(chunk)
                    downloaded_size += len(chunk)

                    # Berechne den Fortschritt in Prozent
                    progress_percent = (downloaded_size / total_size) * 100
                    elapsed_time = time.time() - start_time

                    # Logge nur, wenn sich der Fortschritt geändert hat
                    self.console_output.delete(1.0, tk.END) 
                    self.log(f"Fortschritt: {int(progress_percent)}%")

        return zip_path

    def extract_zip(self, zip_path):
        self.log("Extract ADB...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.getcwd())

            adb_directory = os.path.join(os.getcwd(), ADB_FOLDER)

            if os.path.exists(adb_directory):
                pass
                return adb_directory
            else:
                pass
                return None

        except zipfile.BadZipFile:
            pass
            return None
        except Exception as e:
            pass
            return None

    def cleanup(self, zip_path):
        # Löscht die heruntergeladene ZIP-Datei
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
                

        except Exception as e:
            pass

    def check_admin(self):
        # Prüfen, ob das Programm mit Administratorrechten ausgeführt wird
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def install_adb(self):
        zip_path = self.download_adb()
        adb_directory = self.extract_zip(zip_path)

        if adb_directory:
            self.log(f"{self.texts['adb_u']}\n")
            if self.add_to_path(adb_directory):
                self.log(f"{self.texts['adb_install_erfolg']}\n")
            else:
                pass
            self.cleanup(zip_path)



    def add_to_path(self, adb_directory):
        # Definiere den Pfad zum PowerShell-Skript
        bat_file_path = os.path.join(adb_directory, 'set_adb_path.ps1')
        # Füge den ADB-Pfad zur PATH-Umgebungsvariablen hinzu
        adb_executable = os.path.join(adb_directory, "adb.exe")
        
        if not os.path.exists(adb_executable):
            self.log(f"{self.texts['no_adb']}\n")
            return False

        current_path = os.environ['PATH']
        if adb_directory not in current_path:
            new_path = f"{current_path};{adb_directory}"
            # Füge den neuen Pfad mit setx hinzu

            # Führe das PowerShell-Skript aus
            result = subprocess.run(['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', bat_file_path], capture_output=True, text=True)

            if result.returncode == 0:
                # Aktualisiere den aktuellen Python-Prozess
                os.environ["PATH"] = new_path  
                pass
                return True
            else:
                pass
                return False
        else:
            pass
            return True

    def backup_non_system_apps(self):
        """Ermöglicht das Sichern aller Nicht-System-Apps nach Auswahl eines Speicherorts."""
        # Speicherort für das Backup auswählen
        backup_directory = filedialog.askdirectory(title="Wähle den Speicherort für alle Nicht-System-Apps")

        if not backup_directory:
            self.console_output.insert(tk.END, f"{self.texts['no_safe_place']}\n")
            return

        # Starte den Sicherungsprozess in einem neuen Thread
        threading.Thread(target=self.perform_backup_non_system_apps, args=(backup_directory,), daemon=True).start()



    def get_installed_apps(self):
        adb_path = r"platform-tools\adb.exe"
        command = f'"{adb_path}" shell pm list packages -3'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            installed_apps = result.stdout.strip().splitlines()
            return [app.replace("package:", "").strip() for app in installed_apps]
        else:
            pass
            return []  # Stelle sicher, dass hier eine leere Liste zurückgegeben wird

    def backup_all_apps(self):
        """Sichert alle installierten Benutzer-Apps (ohne System-Apps)."""
        # Holen Sie sich alle Apps aus der Listbox (ersetze dies mit dem Treeview)
        all_apks = self.listbox_apks.get_children()  # Bei Treeview verwenden wir get_children()
        selected_apps = [self.listbox_apks.item(app)['values'][0] for app in all_apks if "system" not in self.listbox_apks.item(app)['values'][0]]

        if not selected_apps:
            self.console_output.insert(tk.END, "Keine Benutzer-Apps gefunden.\n")
            return

        # Speicherort nur einmal auswählen
        backup_directory = filedialog.askdirectory(title="Wähle den Speicherort für die Backups")
        if not backup_directory:
            self.console_output.insert(tk.END, f"{self.texts['no_safe_place']}\n")
            return

        # Starte den Sicherungsprozess in einem neuen Thread
        threading.Thread(target=self.all_perform_backup, args=(selected_apps, backup_directory), daemon=True).start()




    def all_perform_backup(self, selected_apps, backup_directory):
        adb_path = r"platform-tools\adb.exe"
        apktool_path = os.path.join(os.path.dirname(__file__), 'apktool.jar')
        keystore_path = os.path.join(os.path.dirname(__file__), 'my-release-key.jks')

        for app in selected_apps:
            self.console_output.insert(tk.END, f"{self.texts['backup_app']} {app}...\n")
            try:
                command = f'"{adb_path}" shell pm path {app}'
                result = subprocess.run(command, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    apk_paths_on_device = result.stdout.strip().splitlines()
                    apk_paths_on_device = [path.replace("package:", "").strip() for path in apk_paths_on_device]

                    base_apk_path = ""
                    split_apk_paths = []

                    for apk_path in apk_paths_on_device:
                        destination_path = os.path.join(backup_directory, os.path.basename(apk_path))

                        pull_result = subprocess.run([adb_path, "pull", apk_path, destination_path], capture_output=True, text=True)

                        if pull_result.returncode == 0:
                            self.console_output.insert(tk.END, f"{app} {self.texts['safe_erfolg']} {destination_path}!\n")
                            if "base.apk" in destination_path:
                                base_apk_path = destination_path
                            else:
                                split_apk_paths.append(destination_path)
                        else:
                            self.console_output.insert(tk.END, f"{self.texts['safe_error']} {app}: {pull_result.stderr}\n")

                    # APKTool zum Zusammenführen verwenden
                    if base_apk_path:
                        base_dir = os.path.join(os.path.dirname(__file__), "base_dir")
                        os.makedirs(base_dir, exist_ok=True)

                        # Dekodieren der base.apk
                        subprocess.run(["java", "-jar", apktool_path, "d", base_apk_path, "-o", base_dir])

                        # Füge die Split-APKs in die base.apk ein
                        for split_apk in split_apk_paths:
                            subprocess.run(["java", "-jar", apktool_path, "d", split_apk, "-o", base_dir])

                            # Alle Inhalte von Split-APKs in base_dir kopieren
                            for root, dirs, files in os.walk(os.path.join(base_dir)):
                                for file in files:
                                    shutil.copy(os.path.join(root, file), os.path.join(base_dir, file))

                        # APK neu erstellen
                        merged_apk_path = os.path.join(backup_directory, f"{os.path.basename(base_apk_path).replace('base.apk', '')}_merged.apk")
                        subprocess.run(["java", "-jar", apktool_path, "b", base_dir, "-o", merged_apk_path])

                        # APK signieren
                        signed_apk_path = os.path.join(backup_directory, f"{os.path.basename(base_apk_path).replace('base.apk', '')}_signed.apk")
                        subprocess.run(["apksigner", "sign", "--ks", keystore_path, "--out", signed_apk_path, merged_apk_path])

                        self.console_output.insert(tk.END, f"{app} wurde erfolgreich zusammengeführt und signiert zu {signed_apk_path}!\n")

                    # Split-APKs löschen
                    

                else:
                    self.console_output.insert(tk.END, f"Fehler beim Suchen des APK-Pfads: {result.stderr}\n")

            except Exception as e:
                self.console_output.insert(tk.END, f"Fehler: {str(e)}\n")

    def backup_and_merge_app(self, app, backup_directory, apktool_path, keystore_path):
        """Sichert eine einzelne App, einschließlich ihrer Split-APKs, und fügt sie zu einer vollständigen APK zusammen."""
        adb_path = r"platform-tools\adb.exe"

        try:
            # ADB-Befehl zum Ermitteln des APK-Pfads der App auf dem Gerät
            command = f'"{adb_path}" shell pm path {app}'
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)

            if result.returncode == 0:
                apk_paths_on_device = result.stdout.strip().splitlines()
                apk_paths_on_device = [path.replace("package:", "").strip() for path in apk_paths_on_device]

                # Ordner für jede App erstellen
                app_backup_directory = os.path.join(backup_directory, app)
                os.makedirs(app_backup_directory, exist_ok=True)

                # Pfade zum Zusammenführen speichern
                base_apk_path = ""
                split_apk_paths = []

                for apk_path in apk_paths_on_device:
                    # Den ursprünglichen Namen der APK verwenden
                    original_apk_name = os.path.basename(apk_path)
                    destination_path = os.path.join(app_backup_directory, original_apk_name)

                    # APK vom Gerät auf den PC ziehen
                    pull_result = subprocess.run([adb_path, "pull", apk_path, destination_path], capture_output=True, text=True)

                    if pull_result.returncode == 0:
                        self.console_output.insert(tk.END, f"{app} {self.texts['safet_to']} {destination_path}!\n")
                        if "base.apk" in destination_path:
                            base_apk_path = destination_path
                        else:
                            split_apk_paths.append(destination_path)
                    else:
                        self.console_output.insert(tk.END, f"Error {app}: {pull_result.stderr}\n")

                # APKTool zum Zusammenführen der Split-APKs verwenden
                if base_apk_path and split_apk_paths:
                    base_dir = os.path.join(app_backup_directory, "base_dir")
                    split_apk_dir = os.path.join(app_backup_directory, "split_apk_dir")
                    os.makedirs(base_dir, exist_ok=True)
                    os.makedirs(split_apk_dir, exist_ok=True)

                    # Dekodieren der base.apk
                    subprocess.run(["java", "-jar", apktool_path, "d", base_apk_path, "-o", base_dir])

                    # Split-APKs einfügen
                    for split_apk in split_apk_paths:
                        subprocess.run(["java", "-jar", apktool_path, "d", split_apk, "-o", split_apk_dir])

                        for root, dirs, files in os.walk(split_apk_dir):
                            for file in files:
                                shutil.copy(os.path.join(root, file), os.path.join(base_dir, file))

                    # APK neu erstellen
                    merged_apk_path = os.path.join(app_backup_directory, f"{app}_merged.apk")
                    subprocess.run(["java", "-jar", apktool_path, "b", base_dir, "-o", merged_apk_path])

                    # APK signieren
                    signed_apk_path = os.path.join(app_backup_directory, f"{app}_signed.apk")
                    subprocess.run(["apksigner", "sign", "--ks", keystore_path, "--out", signed_apk_path, merged_apk_path])

                    self.console_output.insert(tk.END, f"{app} wurde erfolgreich zusammengeführt und signiert zu {signed_apk_path}!\n")
            else:
                self.console_output.insert(tk.END, f"Fehler beim Suchen des APK-Pfads für {app}: {result.stderr}\n")

        except Exception as e:
            self.console_output.insert(tk.END, f"Fehler: {str(e)}\n")

    def backup_selected_apps(self):
        """Sichert die ausgewählten Apps und fügt Split-APKs zusammen."""
        selected_items = self.listbox_apks.selection()  # Holen Sie sich die ausgewählten Elemente
        selected_apps = [self.listbox_apks.item(item)['values'][0] for item in selected_items]  # Paketnamen extrahieren

        if not selected_apps:
            self.console_output.insert(tk.END, "Keine Apps ausgewählt.\n")
            return

        # Speicherort für Backups auswählen
        backup_directory = filedialog.askdirectory(title="Wähle den Speicherort für die Backups")
        if not backup_directory:
            self.console_output.insert(tk.END, "Kein Speicherort ausgewählt.\n")
            return

        # Starte den Sicherungsprozess in einem neuen Thread
        threading.Thread(target=self.perform_backup1, args=(selected_apps, backup_directory), daemon=True).start()

    def perform_backup1(self, selected_apps, backup_directory):
        """Sichert die ausgewählten Apps in ein definiertes Verzeichnis."""
        
        for app in selected_apps:
            try:
                # ADB-Befehl zum Sichern der App
                command = f"adb shell pm path {app}"
                result = subprocess.run(command.split(), capture_output=True, text=True)

                if result.returncode == 0:
                    apk_path = result.stdout.strip().replace("package:", "")
                    
                    # Extrahiere den App-Namen aus dem Paketnamen (z.B. com.example.app)
                    app_name = app.split('.')[-1]  # Nehme den letzten Teil des Paketnamens
                    apk_filename = f"{app_name}.apk"  # Erstelle den Namen für die APK-Datei

                    # Kopiere die APK zur Backup-Directory mit dem App-Namen
                    adb_pull_command = f"adb pull {apk_path} {os.path.join(backup_directory, apk_filename)}"
                    pull_result = subprocess.run(adb_pull_command.split(), capture_output=True)

                    if pull_result.returncode == 0:
                        self.console_output.insert(tk.END, f"Backup von {app} erfolgreich!\n")
                    else:
                        self.console_output.insert(tk.END, f"Fehler beim Sichern von {app}: {pull_result.stderr}\n")
                else:
                    self.console_output.insert(tk.END, f"Fehler beim Ermitteln des Pfads für {app}: {result.stderr}\n")
            except Exception as e:
                self.console_output.insert(tk.END, f"Fehler: {str(e)}\n")





    
    def backup_selected_appss(self):
        """Sichert die ausgewählten Apps und fügt Split-APKs zusammen."""
        selected_items = self.listbox_apks.selection()  # Holen Sie sich die ausgewählten Elemente
        selected_apps = [self.listbox_apks.item(item)['values'][0] for item in selected_items]  # Paketnamen extrahieren

        if not selected_apps:
            self.console_output.insert(tk.END, "Keine Apps ausgewählt.\n")
            return

        # Speicherort für Backups auswählen
        backup_directory = filedialog.askdirectory(title="Wähle den Speicherort für die Backups")
        if not backup_directory:
            self.console_output.insert(tk.END, "Kein Speicherort ausgewählt.\n")
            return

        # Starte den Sicherungsprozess in einem neuen Thread
        threading.Thread(target=self.perform_backup, args=(selected_apps, backup_directory), daemon=True).start()





    def perform_backup(self, selected_apps):
        global destination_path
        adb_path = r"platform-tools\adb.exe"
        apktool_path = os.path.join(os.path.dirname(__file__), 'apktool.jar')
        keystore_path = os.path.join(os.path.dirname(__file__), 'my-release-key.jks')

        # Speicherort für das Backup auswählen (außerhalb der Schleife)
        backup_directory = filedialog.askdirectory(title="Wähle den Speicherort für die Backups")
        
        if not backup_directory:
            self.console_output.insert(tk.END, "Kein Speicherort ausgewählt. Sicherung abgebrochen.\n")
            return

        for app in selected_apps:
            try:
                # ADB-Befehl zum Ermitteln des APK-Pfads der App auf dem Gerät
                command = f'"{adb_path}" shell pm path {app}'
                result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)

                if result.returncode == 0:
                    apk_paths_on_device = result.stdout.strip().splitlines()
                    apk_paths_on_device = [path.replace("package:", "").strip() for path in apk_paths_on_device]

                    for apk_path in apk_paths_on_device:
                        # Den Namen der App ermitteln, um den Dateinamen korrekt zu sichern
                        original_apk_name = os.path.basename(apk_path)
                        package_name_command = f'"{adb_path}" shell dumpsys package {app} | grep "versionName"'
                        package_name_result = subprocess.run(package_name_command, shell=True, capture_output=True, text=True)

                        if package_name_result.returncode == 0:
                            version_name = package_name_result.stdout.strip().split("=")[-1].strip()
                            apk_file_name = f"{app}_{version_name}.apk"
                        else:
                            apk_file_name = f"{app}.apk"

                        # Speicherort mit dem originalen Namen der APK festlegen
                        destination_path = os.path.join(backup_directory, apk_file_name)

                        # APK vom Gerät auf den PC ziehen
                        pull_result = subprocess.run([adb_path, "pull", apk_path, destination_path], capture_output=True, text=True)


                        if pull_result.returncode == 0:
                            self.console_output.insert(tk.END, f"{app} {self.texts['safet_to']} {destination_path}!\n")
                            self.send_notification()

                        else:
                            self.console_output.insert(tk.END, f"Error {app}: {pull_result.stderr}\n")

                else:
                    self.console_output.insert(tk.END, f"Error: {result.stderr}\n")

            except Exception as e:
                self.console_output.insert(tk.END, f"Error: {str(e)}\n")

    def send_notification(self):
        notification.notify(
            title= self.texts['fertig'],
            message= f"{app} {self.texts['safet_to']} {destination_path}!",
            app_name="ADB GUI",
            timeout=10  # Dauer in Sekunden, wie lange die Benachrichtigung angezeigt wird
        )


    def load_installed_apps(self):
        self.console_output.insert(tk.END, "Starte ADB...\n")
        # Starte die ADB-Befehle in einem neuen Thread
        thread = Thread(target=self.run_adb_commands)
        thread.start()

    def run_adb_commands(self):
        try:
            command = [self.adb_path, 'shell', 'pm', 'list', 'packages']
            result = subprocess.run(command, capture_output=True, text=True, check=True)

            if result.returncode == 0:
                self.apps = result.stdout.splitlines()  # Alle Apps speichern
                self.displayed_apps = self.apps.copy()  # Kopiere für die Anzeige
                self.update_listbox()
            else:
                error_message = f"Fehler beim Abrufen der Apps: {result.stderr.strip()}"
                self.console_output.insert(tk.END, error_message + "\n")

        except subprocess.CalledProcessError as e:
            error_message = f"Ein Fehler ist aufgetreten: {e.stderr.strip()}"
            
        except Exception as e:
            error_message = f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"


    def search_apps(self, event=None):
        search_term = self.search_var.get().lower()
        if search_term:
            # Filtere die Apps, die den Suchbegriff enthalten
            self.displayed_apps = [app for app in self.apps if search_term in app.lower()]
        else:
            # Zeige alle Apps, wenn kein Suchbegriff eingegeben wurde
            self.displayed_apps = self.apps.copy()  # Sicherstellen, dass die gesamte Liste verwendet wird
        self.update_listbox()  # Aktualisiere die Listbox mit den gefilterten Apps




    def delete_selected_apps(self):
            # Überprüfen, welche Apps in der gefilterten Liste ausgewählt sind
            selected_indices = self.listbox_apks.selection()
            selected_apps = [self.displayed_apps[i].replace("package:", "") for i in selected_indices]

            if not selected_apps:
                messagebox.showwarning("Warnung", f"{self.texts['adb_error2']}\n")
                return

            # Starte den Deinstallationsprozess in einem neuen Thread
            threading.Thread(target=self.uninstall_apps, args=(selected_apps,)).start()

    def uninstall_apps(self, apps_to_delete):
        for app in apps_to_delete:
            try:
                # ADB-Befehl zum Löschen der App
                result = subprocess.run([adb_path, "uninstall", app], capture_output=True, text=True)

                if result.returncode == 0:
                    self.console_output.insert(tk.END, f"{app} erfolgreich deinstalliert!\n")
                    
                    self.load_apks()
                else:
                    self.console_output.insert(tk.END, f"Fehler beim Löschen von {app}: {result.stderr}\n")
                    self.load_apks()
                    
            except Exception as e:
                self.console_output.insert(tk.END, f"Ein Fehler ist aufgetreten: {str(e)}\n")
        
    
    def update_after(self):
        self.get_installed_apps
        self.update_listbox_apks

    
    def install_apk(self):
        # Dialog zum Auswählen von APK-Dateien (Einzel- oder Mehrfachauswahl)
        choice = messagebox.askyesno("APK Installation", "Möchtest du mehrere APK-Dateien installieren?")
        
        if choice:
            # Mehrere APK-Dateien auswählen
            apk_paths = filedialog.askopenfilenames(
                title="Wähle eine oder mehrere APK-Dateien",
                filetypes=[("APK Dateien", "*.apk")]  # Nur APK-Dateien zur Auswahl anzeigen
            )
        else:
            # Nur eine APK-Datei auswählen
            apk_paths = [filedialog.askopenfilename(
                title="Wähle eine APK-Datei",
                filetypes=[("APK Dateien", "*.apk")]  # Nur APK-Dateien zur Auswahl anzeigen
            )]

        # Falls eine oder mehrere Dateien ausgewählt wurden
        if apk_paths and apk_paths[0]:
            self.console_output.insert(tk.END, f"{len(apk_paths)}\n")
            # Installation in einem separaten Thread starten
            threading.Thread(target=self.run_installation, args=(apk_paths,)).start()
        else:
            self.console_output.insert(tk.END, f"{self.texts['no_file_select']}\n")

    def run_installation(self, apk_paths):
        for apk_path in apk_paths:
            try:
                self.console_output.insert(tk.END, f"{self.texts['install']} {apk_path}...\n")
                # ADB-Befehl zum Installieren der APK
                result = subprocess.run([adb_path, "install", apk_path], capture_output=True, text=True)

                if result.returncode == 0:
                    self.console_output.insert(tk.END, f"{apk_path} {self.texts['install1']}\n")
                    self.load_apks()
                else:
                    self.console_output.insert(tk.END, f"Error {apk_path}: {result.stderr}\n")
                    self.load_apks
            except FileNotFoundError:
                
                self.load_apks()
            except Exception as e:
                self.console_output.insert(tk.END, f"Error: {str(e)}\n")
                self.load_apks()

#######################################################################################################################################

    def reboot_to_OS(self):
        # Starte den Flash-Vorgang in einem separaten Thread
        threading.Thread(target=self.restart_to_OS).start()

    def restart_to_OS(self):
        result = subprocess.run([adb_path,'reboot'], capture_output=True, text=True)
        self.console_output.insert(tk.END, f"Reboot\n")  

    def restart_to_fastboot(self):
        # Starte den Flash-Vorgang in einem separaten Thread
        threading.Thread(target=self.reboot_to_fastboot).start()

    def reboot_to_fastboot(self):
        self.append_console_output("reboot Fastboot-Modus")
          
        command = [adb_path, 'reboot', 'fastboot']

        result = subprocess.run([adb_path,'reboot', 'fastboot'], capture_output=True, text=True)

        if result.returncode == 0:
            pass
        else:
            self.append_console_output(f"Error: {result.stderr}\n")

    def reboot_to_Bootloader(self):
        # Starte den Flash-Vorgang in einem separaten Thread
        threading.Thread(target=self.restart_to_Bootloader).start()

    def restart_to_Bootloader(self):
        # Befehl zum Neustarten in den Recovery-Modus
        result = subprocess.run([adb_path, 'reboot', 'bootloader'], capture_output=True, text=True)
        
        if result.returncode == 0:
            self.console_output.insert(tk.END, "Reboot\n")
        else:
            self.console_output.insert(tk.END, f"Error: {result.stderr}\n")

    def reboot_to_Recovery(self):
        # Starte den Flash-Vorgang in einem separaten Thread
        threading.Thread(target=self.restart_to_Recovery).start()

    def restart_to_Recovery(self):
        # Befehl zum Neustarten in den Recovery-Modus
        result = subprocess.run([adb_path, 'reboot', 'recovery'], capture_output=True, text=True)
        
        if result.returncode == 0:
            self.console_output.insert(tk.END, "Reboot\n")
        else:
            self.console_output.insert(tk.END, f"Error: {result.stderr}\n")

###########################################################################################################################################


    def toggle_frame_visibility(self):    
        self.backup_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.45)  # Frame öffnen
        self.master.title("Phone Controll - Backup/Restore")

    def install_frame_open(self):    
        self.install_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.45)  # Frame öffnen
        self.select_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.05)
        self.delete_apps_frame.place_forget()
        self.fastboot_frame.place_forget()
        self.settings_opti_frame.place_forget()
        self.settings_frame.place_forget()
        self.select_s_frame.place_forget()
        self.odin_frame.place_forget()
        self.settings_prop_frame.place_forget()
        self.master.title("Phone Controll - Install")

    def odin_frame_open(self):    
        self.odin_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.45)  # Frame öffnen
        self.select_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.05)
        self.delete_apps_frame.place_forget()
        self.settings_opti_frame.place_forget()
        self.install_frame.place_forget()
        self.fastboot_frame.place_forget()
        self.select_s_frame.place_forget()
        self.settings_frame.place_forget()
        self.settings_prop_frame.place_forget()
        self.master.title("Phone Controll - Odin")

    def open_settings_framed(self):    
        self.settings_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.45)  # Frame öffnen
        self.select_s_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.05)
        self.delete_apps_frame.place_forget()
        self.settings_opti_frame.place_forget()
        self.install_frame.place_forget()
        self.odin_frame.place_forget()
        self.fastboot_frame.place_forget()
        self.settings_prop_frame.place_forget()
        self.master.title("Phone Controll - Phone Settings - Lockscreen")

    def fastboot_frame_open(self):    
        self.fastboot_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.45)  # Frame öffnen
        self.select_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.05)
        self.delete_apps_frame.place_forget()
        self.install_frame.place_forget()
        self.settings_frame.place_forget()
        self.odin_frame.place_forget()
        self.settings_opti_frame.place_forget()
        self.select_s_frame.place_forget()
        self.settings_prop_frame.place_forget()
        self.master.title("Phone Controll - Fastboot") 


    def delete_frame_open(self):    
        self.delete_apps_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.45)  # Frame öffnen
        self.select_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.05)
        
        self.delete_all_frame.place(rely=0.1, relwidth=1, relheight=0.9)
        self.install_frame.place_forget()
        
        self.odin_frame.place_forget()
        self.fastboot_frame.place_forget()
        self.select_s_frame.place_forget()
        self.settings_frame.place_forget()
        self.settings_opti_frame.place_forget()
        self.settings_prop_frame.place_forget()
        self.master.title("Phone Controll - APP MANAGMENT")

    def delete_apk_open(self):    
        self.delete_apps_frame.place(relx=0.1, rely=0.001, relwidth=0.8, relheight=0.45)  # Frame öffnen
        self.select_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.05)
        self.install_frame.place_forget()
        self.odin_frame.place_forget()
        self.fastboot_frame.place_forget()
        self.select_s_frame.place_forget()
        self.settings_frame.place_forget()
        self.settings_opti_frame.place_forget()
        self.settings_prop_frame.place_forget()
        self.master.title("Phone Controll - APP MANAGMENT")

    def open_prop_frame(self):    
        self.settings_prop_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.45)  # Frame öffnen
        self.select_s_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.04)
        self.install_frame.place_forget()
        self.odin_frame.place_forget()
        self.delete_apps_frame.place_forget
        self.fastboot_frame.place_forget()
        self.settings_frame.place_forget()
        self.settings_opti_frame.place_forget()
        
        self.master.title("Phone Controll - Propertis")

    def open_opti_framed(self):    
        self.settings_opti_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.45)  # Frame öffnen
        self.select_s_frame.place(relx=0.1, rely=0.02, relwidth=0.8, relheight=0.05)
        self.install_frame.place_forget()
        self.odin_frame.place_forget()
        self.settings_prop_frame.place_forget()
        self.delete_apps_frame.place_forget
        self.fastboot_frame.place_forget()
        self.settings_frame.place_forget()
        
        self.master.title("Phone Controll - Phone Settings")

    def open_twrp(self):    
        self.backup_twrp_frame.place(relx=0.1, rely=0.15, relwidth=0.8, relheight=0.8)  # Frame öffnen
        self.backup_sel_frame.pack(side="top", fill="x")
        self.backup_dd_frame.place_forget()
        self.master.title("Phone Controll - Backup/Restore (TWRP)")

    def open_dd(self):    
        self.backup_dd_frame.place(relx=0.1, rely=0.15, relwidth=0.8, relheight=0.8)  # Frame öffnen
        self.backup_sel_frame.pack(side="top", fill="x")
        self.master.title("Phone Controll - Backup/Restore (Root)")

    def open_reboot_frame(self):
        if self.frame_visible:
            self.reboot_options_frame.place_forget()
            self.frame_visible = False
        else:
            self.reboot_options_frame.place(relx=0.75, rely=0.02, relwidth=0.2, relheight=0.45)  # Frame öffnen
            self.frame_visible = not self.frame_visible  # Zustand umschalten
            self.master.title("Phone Controll - Reboot Options")
        
    def close_all_Frames(self):
        self.backup_frame.place_forget()  # Frame schließen ------- weitere Frames hinzu fügen
        self.install_frame.place_forget()
        self.delete_all_frame.place_forget()
        self.settings_prop_frame.place_forget()
        self.settings_opti_frame.place_forget()
        self.select_s_frame.place_forget()
        self.select_frame.place_forget()
        self.delete_apps_frame.place_forget()
        self.fastboot_frame.place_forget()
        self.odin_frame.place_forget()
        self.backup_dd_frame.place_forget()
        self.settings_frame.place_forget()
        self.master.title("Phone Controll - Home")

    def set_dark_mode(self):
        dark_bg = "#2b2b2b"
        dark_fg = "#ffffff"
        self.master.configure(bg=dark_bg)

        for widget in self.master.winfo_children():
            widget.configure(bg=dark_bg, fg=dark_fg)

    def get_partitions(self):
        partitions = []
        try:
            # Stellen Sie sicher, dass der Pfad korrekt ist
            adb_path = r"platform-tools\adb.exe"
            command = [adb_path, 'shell', 'ls', '/dev/block/platform/bootdevice/by-name/']
            
            # Führen Sie den Befehl aus
            result = subprocess.run(command, capture_output=True, text=True, check=True)  # check=True wird den Fehler auslösen, wenn der Befehl fehlschlägt
            
            if result.returncode == 0:
                partitions = result.stdout.splitlines()
            else:
                self.console_output.insert(tk.END, f"Error: {result.stderr.strip()}\n")
        except subprocess.CalledProcessError as e:
            pass
        except Exception as e:
            ()
        
        return partitions


    def update_device_info(self):
        
        if self.is_countdown_running:
            return  # Countdown läuft bereits, keine weiteren Updates

        try:
            # Grundlegende Gerätedaten
# ADB-Befehle zum Abrufen von Geräteeigenschaften
            model_result = subprocess.run([adb_path, 'shell', 'getprop', 'ro.product.model'], capture_output=True, text=True)
            android_version_result = subprocess.run([adb_path, 'shell', 'getprop', 'ro.build.version.release'], capture_output=True, text=True)
            device_status_result = subprocess.run([adb_path, 'get-state'], capture_output=True, text=True)

            # Weitere Informationen
            device_storage_result = subprocess.run([adb_path, 'shell', 'df', '-h', '/data'], capture_output=True, text=True)
            ram_result = subprocess.run([adb_path, 'shell', 'free', '-h'], capture_output=True, text=True)
            cpu_info_result = subprocess.run([adb_path, 'shell', 'cat', '/proc/cpuinfo'], capture_output=True, text=True)
            kernel_version_result = subprocess.run([adb_path, 'shell', 'uname', '-r'], capture_output=True, text=True)



            if model_result.returncode == 0 and android_version_result.returncode == 0 and device_status_result.returncode == 0:
                current_device_info = f"Modell: {model_result.stdout.strip()}\n" \
                                      f"Android-Version: {android_version_result.stdout.strip()}\n" \
                                      f"Status: {device_status_result.stdout.strip()}\n" \
                                      f"Speicher: {device_storage_result.stdout.strip()}\n" \
                                      f"RAM: {ram_result.stdout.strip()}\n" \
                                      f"CPU-Informationen: {cpu_info_result.stdout.strip()}\n" \
                                      f"Kernel-Version: {kernel_version_result.stdout.strip()}"



                # Überprüfung, ob sich die Gerätedaten geändert haben
                if current_device_info != self.previous_device_info:
                    # Nur wenn sich die Informationen geändert haben, wird das Textfeld aktualisiert
                    self.device_info_text.delete(1.0, tk.END)
                    self.device_info_text.insert(tk.END, current_device_info)
                    self.device_info_text.pack_forget()
                    # Konsole nur bei Änderung aktualisieren
                    self.append_console_output("Update")

                    # Speichere die aktuellen Gerätedaten für den nächsten Vergleich
                    self.previous_device_info = current_device_info

                # Überprüfung auf Geräte-Verbindungsstatus
                if 'offline' in device_status_result.stdout or 'unauthorized' in device_status_result.stdout:
                    self.start_device_check_countdown()

        except Exception as e:
            self.append_console_output(f"Error: {e}")
            root.title("Online")
    def append_console_output(self, message):
        self.console_output.insert(tk.END, message + "\n")  # Verwendung von insert


    def start_device_check_countdown(self):
        if not self.is_countdown_running:
            self.is_countdown_running = True
            self.countdown_timer = 10
            self.append_console_output("Gerät offline oder nicht autorisiert. Versuche es in 10 Sekunden erneut.")
            root.title("Online")
            while self.countdown_timer > 0:
                time.sleep(1)
                self.countdown_timer -= 1
                self.append_console_output(f"{self.countdown_timer} Sekunden verbleibend...")

            # Nach Countdown zurücksetzen
            self.is_countdown_running = False
            self.update_device_info()



    def show_backup_options(self):
        # Speicherort für das Backup auswählen
        self.backup_folder_path = filedialog.askdirectory(title="Wähle Speicherort für Backup")
        if self.backup_folder_path:
            threading.Thread(target=self.execute_backup).start()


    def select_flash_file(self):
        # Speicherort für die zu flashende Datei auswählen
        flash_file = filedialog.askopenfilename(title="Select", filetypes=[("Image Files", "*.img")])
        if flash_file:
            self.flash_file_path = flash_file  # Speichere den Pfad zur ausgewählten Datei
            self.append_console_output(f"{self.texts['selected_file']} {self.flash_file_path}\n")
        else:
            self.append_console_output(f"{self.texts['no_file_select']}")




    def execute_flash(self):
        # Starte den Flash-Vorgang in einem separaten Thread
        threading.Thread(target=self.flash_partitions).start()


    def flash_partitions(self):
        """Flasht die ausgewählten Partitionen mit der ausgewählten Datei"""
        # Überprüfen, welche Partitionen ausgewählt wurden
        fastboot_path = r"platform-tools\fastboot.exe"
        selected_partitions = [partition for partition, var in self.partitions_vars.items() if var.get()]
        
        if not selected_partitions:
            self.append_console_output(f"{self.texts['no_partition_select']}\n")
            return

        if not self.flash_file_path:  # Überprüfen, ob der Pfad zur Flash-Datei gesetzt ist
            self.append_console_output(f"{self.texts['no_file_select']}\n")
            return  # Beende die Funktion, wenn kein Pfad vorhanden ist
        
        self.append_console_output(f"Flash {', '.join(selected_partitions)}")
        self.progress["value"] = 0
        
        # Flash-Vorgang für jede ausgewählte Partition
        for i, partition in enumerate(selected_partitions):
            flash_file_path = self.flash_file_path  # Verwende den gespeicherten Pfad zur Flash-Datei

            # Überprüfe, ob die Datei existiert
            if not os.path.isfile(flash_file_path):
                pass
                continue  # Gehe zur nächsten Partition

            command = f"{fastboot_path} flash {partition} {flash_file_path}"
            self.append_console_output(f"{command}\n")

            # subprocess.Popen hier anpassen, um die Ausgabe in Echtzeit zu zeigen
            with subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
                for line in process.stdout:  # Zeige die Ausgaben in Echtzeit an
                    self.append_console_output(line.strip())  # Ausgabe in die Konsole

                # Warten auf das Ende des Prozesses und die Fehlerausgabe lesen
                stdout, stderr = process.communicate()

            # Überprüfen des Rückgabewerts
            if process.returncode == 0:
                self.append_console_output(f"{partition} {self.texts['erfolg']}\n")
            else:
                self.append_console_output(f"Error {partition}: {stderr.strip()}")
            
            # Aktualisiere den Fortschrittsbalken
            self.progress["value"] = (i + 1) / len(selected_partitions) * 100

        self.progress["value"] = 100
        self.append_console_output(f"{self.texts['fertig']}")


    def execute_backup(self):
        selected_partitions = [partition for partition, var in self.partition_vars.items() if var.get()]
        if selected_partitions:
            self.append_console_output(f"{', '.join(selected_partitions)} {self.texts['safe_partition']}\n")
            self.progress["value"] = 0

            for i, partition in enumerate(selected_partitions):
                
                # Backup-Dateiname entspricht dem Partitionsnamen
                backup_name = partition
                backup_path = os.path.join(self.backup_folder_path, f'{backup_name}_{partition}.img')

                # Verwenden Sie den Befehl zur Sicherung
                command = f"{adb_path} shell twrp backup {partition} {backup_name}"

                self.append_console_output(f"{self.texts['safe_partition']}: {partition}...\n")
                result = subprocess.run(command.split(), capture_output=True, text=True)

                if result.returncode == 0:
                    # Pull Backup von der SD-Karte
                    pull_command = ['adb', 'pull', f'/sdcard/TWRP/{backup_name}.img', backup_path]
                    pull_result = subprocess.run(pull_command, capture_output=True, text=True)

                    if pull_result.returncode == 0:
                        pass
                    else:
                        self.append_console_output(f"Error {partition}: {pull_result.stderr.strip()}")
                else:
                    self.append_console_output(f"Error {partition}: {result.stderr.strip()}")

                # Fortschrittsbalken aktualisieren
                self.progress["value"] = (i + 1) / len(selected_partitions) * 100

            self.progress["value"] = 100
            self.append_console_output(f"{self.texts['fertig']}\n")
        else:
            self.append_console_output(f"{self.texts['no_partition_select']}\n")


    def show_restore_options(self):
        self.restore_folder_path = filedialog.askdirectory(title="Wähle Speicherort für Wiederherstellung")
        if self.restore_folder_path:
            self.populate_restore_file_list()

    def populate_restore_file_list(self):
        # Leere die Listbox vor dem Hinzufügen neuer Einträge
        self.listbox_restore_files.delete(0, tk.END)
        for file in os.listdir(self.restore_folder_path):
            if file.endswith('.win'):
                var = tk.BooleanVar()
                self.restore_files_vars[file] = var
                # Checkbox im Frame hinzufügen
                checkbox = tk.Checkbutton(self.listbox_restore_files, text=file, variable=var)
                checkbox.pack(anchor="w")

    def execute_restore(self):
        selected_files = [file for file, var in self.restore_files_vars.items() if var.get()]
        if selected_files:

            
            self.append_console_output(f"{self.texts['restor_start']} {', '.join(selected_files)}")
            for file in selected_files:
                # Das erste Wort des Dateinamens extrahieren
                first_word = file.split('_')[0]  # Angenommen, die Wörter sind durch Unterstriche getrennt

                # Datei zuerst auf das Gerät kopieren
                local_file_path = os.path.join(self.restore_folder_path)
                remote_file_path = f"/sdcard/TWRP/BACKUPS/R92X538VD9N/{first_word}"  # Verwendung des ersten Wortes für den Remote-Pfad
                create = (f"adb shell mkdir /sdcard/TWRP/BACKUPS/R92X538VD9N/")
                result = subprocess.run(create, capture_output=True, text=True)
                # Datei auf das Gerät übertragen
                push_command = f"adb push {local_file_path} {remote_file_path}"
                result = subprocess.run(push_command.split(), capture_output=True, text=True)
                if result.returncode != 0:
                    self.append_console_output(f"Error {file}: {result.stderr}")
                    continue  # Fahren Sie mit der nächsten Datei fort

                # Hier wird der Wiederherstellungsbefehl ausgeführt
                restore_command = f"adb shell twrp restore /sdcard/TWRP/BACKUPS/R92X538VD9N/"
                result = subprocess.run(restore_command.split(), capture_output=True, text=True)
                if result.returncode == 0:
                    self.append_console_output(f"{file} {self.texts['restore_erfolg']}")
                else:
                    self.append_console_output(f"Error {file}: {result.stderr}")
        else:
            self.append_console_output(f"{self.texts['no_file_select']}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = TWRPBackupRestoreApp(root)
    root.mainloop()  
    

