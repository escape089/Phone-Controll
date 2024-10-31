import os
import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

class PartitionManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Partition Manager")
        self.root.geometry("500x500")
        self.adb_path = (r"ADB GUI PROGRAMM\platform-tools\adb.exe")

        # Button to refresh partitions list
        self.refresh_button = tk.Button(root, text="Partitionen anzeigen", command=self.list_partitions)
        self.refresh_button.pack(pady=10)

        # Listbox to show partitions
        self.partitions_listbox = tk.Listbox(root)
        self.partitions_listbox.pack(fill=tk.BOTH, expand=True)

        # Action buttons
        self.format_button = tk.Button(root, text="Partition formatieren", command=self.format_partition)
        self.format_button.pack(pady=5)
        
        self.resize_button = tk.Button(root, text="Partition vergrößern/verkleinern", command=self.resize_partition)
        self.resize_button.pack(pady=5)
        
        self.delete_button = tk.Button(root, text="Partition löschen", command=self.delete_partition)
        self.delete_button.pack(pady=5)
        
        self.create_button = tk.Button(root, text="Partition erstellen", command=self.create_partition)
        self.create_button.pack(pady=5)

    def run_adb_command(self, command):
        try:
            result = subprocess.check_output(command, shell=True).decode("utf-8")
            return result
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Fehler", f"Fehler bei der ADB-Ausführung: {e}")
            return None

    def get_partition_size(self, partition):
        """Retrieve the current size of a partition in GB."""
        size_output = self.run_adb_command(f"adb shell df /dev/block/by-name/{partition}")
        if size_output:
            for line in size_output.splitlines():
                if f"/dev/block/by-name/{partition}" in line:
                    parts = line.split()
                    used_space = parts[2]  # Current size
                    return float(used_space.replace('G', ''))  # Return size in GB
        return 0

    def get_free_space(self):
        """Retrieve free space on the device in GB."""
        free_space_output = self.run_adb_command("adb shell df /data")  # Check free space on data partition as an example
        if free_space_output:
            for line in free_space_output.splitlines():
                if "/data" in line:
                    # Example output: "/dev/block/bootdevice/by-name/userdata  100G  20G  80G"
                    parts = line.split()
                    available_space = parts[3]  # 80G in the example
                    return float(available_space.replace('G', ''))  # Return available space in GB
        return 0

    def list_partitions(self):
        partitions = self.run_adb_command("adb shell ls /dev/block/by-name")
        if partitions:
            self.partitions_listbox.delete(0, tk.END)
            for partition in partitions.splitlines():
                self.partitions_listbox.insert(tk.END, partition)
    
    def format_partition(self):
        selected_partition = self.partitions_listbox.get(tk.ACTIVE)
        if not selected_partition:
            messagebox.showwarning("Warnung", "Bitte wähle eine Partition aus.")
            return
        confirm = messagebox.askyesno("Bestätigen", f"Möchtest du die Partition {selected_partition} wirklich formatieren?")
        if confirm:
            format_command = f"{self.adb_path} shell mkfs.ext4 /dev/block/by-name/{selected_partition}"
            self.run_adb_command(format_command)
            messagebox.showinfo("Erfolg", f"Partition {selected_partition} formatiert.")

    def resize_partition(self):
        selected_partition = self.partitions_listbox.get(tk.ACTIVE)
        if not selected_partition:
            messagebox.showwarning("Warnung", "Bitte wähle eine Partition aus.")
            return

        # Get current partition size
        current_size = self.get_partition_size(selected_partition)
        if current_size <= 0:
            messagebox.showwarning("Warnung", "Konnte die aktuelle Partitionsgröße nicht ermitteln.")
            return

        # Get available space in GB
        available_space = self.get_free_space()
        total_space = current_size + available_space

        # Create a new window for resizing
        resize_window = tk.Toplevel(self.root)
        resize_window.title("Partition vergrößern/verkleinern")
        
        tk.Label(resize_window, text=f"Aktuelle Größe: {current_size} GB").pack(pady=5)
        tk.Label(resize_window, text=f"Maximale Größe: {total_space} GB").pack(pady=5)

        # Slider for size selection (from 1 GB to total available size)
        size_var = tk.DoubleVar(value=current_size)
        size_slider = ttk.Scale(resize_window, from_=1, to=total_space, orient=tk.HORIZONTAL, variable=size_var)
        size_slider.pack(pady=10)

        def confirm_resize():
            new_size = size_var.get()
            if new_size > total_space:
                messagebox.showerror("Fehler", "Die ausgewählte Größe überschreitet den verfügbaren Speicherplatz.")
            elif new_size < current_size:
                # Shrink the partition
                shrink_command = f"adb shell resize2fs /dev/block/by-name/{selected_partition} {int(new_size)}G"
                self.run_adb_command(shrink_command)
                messagebox.showinfo("Erfolg", f"Partition {selected_partition} auf {int(new_size)} GB verkleinert.")
            elif new_size > current_size:
                # Extend the partition
                resize_command = f"adb shell resize2fs /dev/block/by-name/{selected_partition} {int(new_size)}G"
                self.run_adb_command(resize_command)
                messagebox.showinfo("Erfolg", f"Partition {selected_partition} auf {int(new_size)} GB vergrößert.")
            resize_window.destroy()

        tk.Button(resize_window, text="Größe ändern", command=confirm_resize).pack(pady=10)

    def delete_partition(self):
        selected_partition = self.partitions_listbox.get(tk.ACTIVE)
        if not selected_partition:
            messagebox.showwarning("Warnung", "Bitte wähle eine Partition aus.")
            return
        confirm = messagebox.askyesno("Bestätigen", f"Möchtest du die Partition {selected_partition} wirklich löschen?")
        if confirm:
            delete_command = f"adb shell parted /dev/block/by-name/{selected_partition} rm"
            self.run_adb_command(delete_command)
            messagebox.showinfo("Erfolg", f"Partition {selected_partition} gelöscht.")
            self.list_partitions()  # Refresh list

    def create_partition(self):
        # Get available space in GB
        available_space = self.get_free_space()
        if available_space <= 0:
            messagebox.showwarning("Warnung", "Kein freier Speicherplatz verfügbar.")
            return

        partition_name = simpledialog.askstring("Partition erstellen", "Gib den Namen der neuen Partition an:")
        if not partition_name:
            return

        # Create a new window for partition size selection
        create_window = tk.Toplevel(self.root)
        create_window.title("Neue Partition erstellen")
        
        tk.Label(create_window, text=f"Verfügbarer Speicherplatz: {available_space} GB").pack(pady=10)

        # Slider for size selection
        size_var = tk.DoubleVar()
        size_slider = ttk.Scale(create_window, from_=1, to=available_space, orient=tk.HORIZONTAL, variable=size_var)
        size_slider.pack(pady=10)

        def confirm_create():
            partition_size = size_var.get()
            if partition_size > available_space:
                messagebox.showerror("Fehler", "Die ausgewählte Größe überschreitet den verfügbaren Speicherplatz.")
            else:
                create_command = f"adb shell parted /dev/block/mmcblk0 mkpart {partition_name} {int(partition_size)}G"
                self.run_adb_command(create_command)
                messagebox.showinfo("Erfolg", f"Partition {partition_name} mit {int(partition_size)} GB erstellt.")
                create_window.destroy()
                self.list_partitions()  # Refresh list

        tk.Button(create_window, text="Partition erstellen", command=confirm_create).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = PartitionManagerApp(root)
    root.mainloop()
