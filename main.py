import customtkinter as ctk
import PIL.Image
import time
import os
import threading
from tkinter import filedialog
import tempfile
import zipfile
import socket
import shutil
import tkinter.messagebox
from pathlib import Path
import subprocess

def splash(root: ctk.CTk):
    splash_image = ctk.CTkLabel(root, text="", image=ctk.CTkImage(PIL.Image.open("./Assets/Logo Light.png"), PIL.Image.open("./Assets/Logo Dark.png"), (100, 100)))
    splash_image.place(x=200, y=20)
    splash_text = ctk.CTkLabel(root, text="WiFileShare", font=("Segoe UI", 40, "bold"))
    splash_text.place(x=145, y=120)
    return splash_image, splash_text

def send_window(window: ctk.CTk):
    class ListFrame(ctk.CTkScrollableFrame):
        def __init__(self, master, **kwargs):
            self.list = []
            super().__init__(master, **kwargs)
    
        def _delete(self, frame, path):
            if len(self.winfo_children()) == 1:
                share_button.place_forget()
            self.list.remove(path)
            frame.destroy()

        def add_path(self, message):
            f = ctk.CTkFrame(self, border_width=2, fg_color="transparent", corner_radius=10)
            m = ctk.CTkLabel(f, text=message, wraplength=225, justify="left", font=("Sogue UI", 12, "bold"), fg_color="transparent", bg_color="transparent", corner_radius=100)
            m.pack(anchor="w", padx=5, pady=2, side="left")
            d = ctk.CTkButton(f, text="Delete", width=50, font=("Segoe UI", 13), fg_color=("#de0202", "#8B0000"), hover_color=("#8B0000", "#de0202"), border_color=("#FF0000", "#8B0000"), border_width=1, corner_radius=10, command=lambda f=f, p=message: self._delete(f, p))
            d.pack(anchor="e", padx=5, pady=2, side="right")
            f.pack(anchor="w", fill=ctk.BOTH, side="top", padx=10, pady=2)
            self.list.append(message)
            share_button.place(x=350, y=320)
            self.after(10, self._parent_canvas.yview_moveto, 1.0)
        
    def open_file_dialog(frame: ListFrame):
        file_paths = filedialog.askopenfilenames(title="Select files", filetypes=[("All files", "*.*")])
        if file_paths:
            for i in file_paths:
                frame.add_path(i)

    def open_folder_dialog(frame):
        folder_path = filedialog.askdirectory(title="Select a folder")
        if folder_path:
            frame.add_path(folder_path)

    window.destroy()
    root = ctk.CTk()
    root.iconbitmap("./Assets/Icon.ico")
    root.title("WiFileShare: Send")
    positionRight = int(root.winfo_screenwidth()/2 - 500/2)
    positionDown = int(root.winfo_screenheight()/2 - 360/2)
    root.geometry(f"500x360+{positionRight}+{positionDown - 50}")
    root.resizable(0, 0)

    title = ctk.CTkLabel(root, text="WiFileShare", font=("Segoe UI", 40, "bold"))
    title.place(x=145, y=10)

    selectionFrame = ctk.CTkFrame(root, width=480, height=235, corner_radius=10, border_width=2, fg_color="transparent")
    selectionFrame.place(x=10, y=80)
    selectionFrameLabel = ctk.CTkLabel(root, text="Add Item", font=("Segoe UI", 14, "bold"), padx=4)
    selectionFrameLabel.place(x=20, y=67)
    selectionFrame.pack_propagate(False)

    listFrame = ListFrame(selectionFrame, height=50, width=350, fg_color="transparent", border_width=1)
    listFrame.place(x=10, y=15)

    add_file_button = ctk.CTkButton(selectionFrame, text="Add File(s)", width=20, font=("Segoe UI", 13, "bold"), command=lambda: open_file_dialog(listFrame))
    add_file_button.place(x=390, y=80)
    add_directory_button = ctk.CTkButton(selectionFrame, text="Add Folder(s)", width=19, font=("Segoe UI", 12, "bold"), command=lambda: open_folder_dialog(listFrame))
    add_directory_button.place(x=390, y=115)

    share_button = ctk.CTkButton(root, text="Share", font=("Segoe UI", 16, "bold"), command=lambda: shareWindow(root, listFrame.list))

    root.mainloop()

def shareWindow(window: ctk.CTk, paths: list):
    global tempPath, zip_path, hostSocket, dot_animate

    window.destroy()

    def create_zip(paths):
        global tempPath, zip_path

        tempPath = tempfile.mkdtemp(prefix="WiFileShare_")
        zip_path = os.path.join(tempPath, "Items.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for path in paths:
                if os.path.isfile(path):
                    zipf.write(path, os.path.basename(path))
                elif os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculate the relative path of the file with respect to the base directory
                            relative_path = os.path.relpath(file_path, path)
                            zipf.write(file_path, os.path.join(os.path.basename(path), relative_path))
                        
            empty_dirs = [path for path in paths if os.path.isdir(path) and not os.listdir(path)]
            for empty_dir in empty_dirs:
                zipf.write(empty_dir, os.path.join(os.path.basename(empty_dir), ''))
        pause.set(True)

    hostSocket = None
    root = ctk.CTk()
    root.iconbitmap("./Assets/Icon.ico")
    root.title("WiFileShare: Send")
    positionRight = int(root.winfo_screenwidth()/2 - 500/2)
    positionDown = int(root.winfo_screenheight()/2 - 235/2)
    root.geometry(f"500x235+{positionRight}+{positionDown - 50}")
    root.resizable(0, 0)

    title = ctk.CTkLabel(root, text="WiFileShare", font=("Segoe UI", 40, "bold"))
    title.place(x=145, y=10)

    dot_animate = True
    def animate(l: ctk.CTkLabel):
        while dot_animate:
            if l.cget("text").endswith("..."):
                l.configure(text=str(l.cget("text")).replace("...", ""))
            else:
                l.configure(text=str(l.cget("text"))+".")
            time.sleep(0.75)
    
    connection_text = ctk.CTkLabel(root, text="Processing", font=("Segoe UI", 15, "bold"))
    connection_text.place(x=200, y=80)
    threading.Thread(target=animate, args=(connection_text, ), daemon=True).start()
    pause = ctk.BooleanVar(value=False)
    threading.Thread(target=create_zip, args=(paths, ), daemon=True).start()
    tempPath, zip_path = "", ""

    def send(tempPath, zipPath, label, iptext, iplabel):
        global hostSocket, dot_animate, finished, sent_data, transfered, cancelled, tobeexit
        cancelled = False
        tobeexit = False

        try:
            clientSocket, clientAddress = hostSocket.accept()
        except OSError as e:
            if str(e) == "[WinError 10038] An operation was attempted on something that is not a socket":
                pass 
            else:
                raise e

        def on_closing():
            global cancelled, tobeexit

            if not finished:
                if tkinter.messagebox.askyesno("Are you sure?", "Are you sure you want to stop the transfer?"):
                    clientSocket.send("||--||-@#%#(&*@#-||Stop||-@!^%^#$&-||--||".encode())
                    cancelled = True
                    tobeexit = True
                else:
                    pass
            else:
                root.destroy()
                
        root.protocol("WM_DELETE_WINDOW", on_closing)

        iptext.destroy()
        iplabel.destroy()
        label.destroy()

        inFrame = ctk.CTkFrame(root, width=480, height=120, corner_radius=10, border_width=2, fg_color="transparent")
        inFrame.place(x=10, y=80)
        inFrameLabel = ctk.CTkLabel(root, text="Sharing Insight", font=("Segoe UI", 14, "bold"), padx=4)
        inFrameLabel.place(x=20, y=67)
        inFrame.pack_propagate(False)

        dot_animate = False
        progressLabel = ctk.CTkLabel(inFrame, text="Progress:", font=("Segoe UI", 13, "bold"))
        progressLabel.place(x=10, y=10)
        progressbar = ctk.CTkProgressBar(inFrame)
        progressbar.place(x=80, y=21)
        progressindecatorlabel = ctk.CTkLabel(inFrame, text="50%", font=("Segoe UI", 13))
        progressindecatorlabel.place(x=285, y=10)

        statusLabel = ctk.CTkLabel(inFrame, text="Status: ", font=("Segoe UI", 13, "bold"))
        statusLabel.place(x=10, y=35)
        statusValueLabel = ctk.CTkLabel(inFrame, text="", font=("Consolas", 13, "bold"))
        statusValueLabel.place(x=60, y=36)

        transferSpeedLabel = ctk.CTkLabel(inFrame, text="Transfer Speed: ", font=("Segoe UI", 13, "bold"))
        transferSpeedLabel.place(x=10, y=60)
        transferSpeedValueLabel = ctk.CTkLabel(inFrame, text="", font=("Consolas", 13, "bold"))
        transferSpeedValueLabel.place(x=110, y=61)

        elapsedTimeLabel = ctk.CTkLabel(inFrame, text="Elapsed Time: ", font=("Segoe UI", 13, "bold"))
        elapsedTimeLabel.place(x=10, y=85)

        elapsedTimeValueLabel = ctk.CTkLabel(inFrame, text="", font=("Consolas", 13, "bold"))
        elapsedTimeValueLabel.place(x=110, y=86)

        total_size = os.path.getsize(zipPath)
        clientSocket.send(f"Received_{int(time.time())}.zip".encode())
        clientSocket.send(str(total_size).encode())
        def show_other_values():
            global finished, sent_data

            def format_time(seconds):
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                return "%d:%02d:%02d" % (h, m, s)

            def get_speed_with_unit(size_in_kb):
                if size_in_kb < 1024:
                    return f"{size_in_kb:.2f} KB/s"
                elif size_in_kb < 1024 * 1024:
                    size_in_mb = size_in_kb / 1024.0
                    return f"{size_in_mb:.2f} MB/s"
                else:
                    size_in_gb = size_in_kb / (1024.0 * 1024.0)
                    return f"{size_in_gb:.2f} GB/s"
            
            while not finished:
                if not transfered:
                    elapsed_time = time.time() - start_time
                    transfer_speed = (sent_data / elapsed_time) / 1024
                    elapsedTimeValueLabel.configure(text=format_time(elapsed_time))
                    transferSpeedValueLabel.configure(text=get_speed_with_unit(transfer_speed))
                if "!" not in statusValueLabel.cget("text"):
                    if statusValueLabel.cget("text").endswith("..."):
                        statusValueLabel.configure(text=str(statusValueLabel.cget("text")).replace("...", ""))
                    else:
                        statusValueLabel.configure(text=str(statusValueLabel.cget("text"))+".")
                time.sleep(1)

        finished = False
        transfered = False

        with open(zipPath, "rb") as file:
            statusValueLabel.configure(text="Transfering")
            data = file.read(153600)
            sent_data = 0
            start_time = int(time.time())
            threading.Thread(target=show_other_values, daemon=True).start()
            while data:
                if not cancelled:
                    try:
                        clientSocket.send(data)
                    except ConnectionResetError as e:
                        if cancelled:
                            break
                        else:
                            cancelled = True
                    sent_data += len(data)
                    progressbar.set(sent_data / total_size)
                    prcntge = (sent_data * 100) / total_size
                    progressindecatorlabel.configure(text=f"{prcntge:.2f}%")
                    data = file.read(153600)
                else:
                    break
        if not cancelled:
            transfered = True
            statusValueLabel.configure(text="Finalizing")
            progressbar.configure(mode="indeterminate")
            shutil.rmtree(tempPath)
            clientSocket.close()
            hostSocket.close()
            progressbar.configure(mode="determinate")
            finished = True
            statusValueLabel.configure(text="Transfer Completed!")
            ctk.CTkButton(root, text="Home", font=("Seoge UI", 15, "bold"), height=20, command=lambda: [root.destroy(), main(True)]).place(x=350, y=205)
        else:
            transfered = True
            statusValueLabel.configure(text="Cleaning up")
            progressbar.configure(mode="indeterminate")
            shutil.rmtree(tempPath)
            finished = True
            statusValueLabel.configure(text="Transfer was cancelled from receiver end!")
            if tobeexit:
                root.destroy()
                exit(1)
            ctk.CTkButton(root, text="Home", font=("Seoge UI", 15, "bold"), height=20, command=lambda: [root.destroy(), main(True)]).place(x=350, y=205)


    
    def wait_for_connection(tempPath, zipPath):
        global dot_animate, hostSocket

        def cleanup():
            global dot_animate

            if os.path.exists(tempPath):
                shutil.rmtree(tempPath)
            dot_animate = False

            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", cleanup)

        dot_animate = True
        hostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hostSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        addr = socket.gethostbyname(socket.gethostname())
        hostSocket.bind((addr, 0))
        connection_text = ctk.CTkLabel(root, text="Waiting for Connection", font=("Segoe UI", 15, "bold"))
        connection_text.place(x=170, y=80)
        threading.Thread(target=animate, args=(connection_text, ), daemon=True).start()
        ipText = ctk.CTkLabel(root, text=f"IP: ", font=("Segoe UI", 13, "bold"))
        ipText.place(x=170, y=110)
        ipAddText = ctk.CTkLabel(root, text=f"{hostSocket.getsockname()[0]}:{hostSocket.getsockname()[1]}", font=("Consolas", 14, "bold"))
        ipAddText.place(x=190, y=111)
        hostSocket.listen()
        threading.Thread(target=send, args=(tempPath, zipPath, connection_text, ipText, ipAddText)).start()

    def check_if_finished():
        global dot_animate

        if pause.get():
            dot_animate = False
            connection_text.destroy()
            wait_for_connection(tempPath, zip_path)
        else:
            root.after(1000, check_if_finished)
    
    root.after(1000, check_if_finished)
    root.mainloop()


def receive_window(window: ctk.CTk):
    global portEntryLabel, portEntry, port_added, connectButton

    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except socket.error as e:
            return None
    
    def validate_ip(text):
        if all(c.isdigit() or c in [".", ""] for c in text):
            segments = text.split(".")
            if text.count(".") <= 3 and all(0 <= int(segment) <= 255 for segment in segments if segment.isdigit()):
                if len(segments) == 4:
                    if segments[3] != "" and len(segments[3]) == 1:
                        on_first_digit_added()
                    elif segments[3] == "":
                        on_first_digit_removed()
                return True
        return False
    
    def validate_port(text):
        global connectButton

        if text.isdigit() or text == "":
            if len(text) > 5:
                return False
            if len(text) == 3:
                connectButton.place(x=350, y=200)
                ipEntry.bind("<Return>", lambda e: receiver_window(root, ipEntry.get(), portEntry.get()))
            elif len(text) == 2:
                connectButton.place_forget()
                ipEntry.unbind_all("<Return>")
            return True
        
        else:
            return False

    def on_first_digit_added():
        global portEntryLabel, portEntry, port_added

        if not port_added:
            portEntryLabel = ctk.CTkLabel(detailsFrame, text="Port: ", font=("Segoe UI", 13, "bold"))
            portEntryLabel.place(x=10, y=40)
            portEntry = ctk.CTkEntry(detailsFrame, height=13, width=50, font=("Consolas", 12), validate="key", validatecommand=(root.register(validate_port), "%P"))
            portEntry.place(x=45, y=45)
            port_added = True


    def on_first_digit_removed():
        global portEntry, portEntryLabel, port_added

        if port_added:
            portEntry.destroy()
            portEntryLabel.destroy()
            port_added = False

    port_added = False
    portEntryLabel = None
    portEntry = None

    if window:
        window.destroy()
    root = ctk.CTk()
    root.iconbitmap("./Assets/Icon.ico")
    root.title("WiFileShare: Receiver")
    positionRight = int(root.winfo_screenwidth()/2 - 500/2)
    positionDown = int(root.winfo_screenheight()/2 - 235/2)
    root.geometry(f"500x235+{positionRight}+{positionDown - 50}")
    root.resizable(0, 0)

    title = ctk.CTkLabel(root, text="WiFileShare", font=("Segoe UI", 40, "bold"))
    title.place(x=145, y=10)

    detailsFrame = ctk.CTkFrame(root, width=480, height=100, corner_radius=10, border_width=2, fg_color="transparent")
    detailsFrame.place(x=10, y=80)
    detailsFrameLabel = ctk.CTkLabel(root, text="Enter the following details", font=("Segoe UI", 14, "bold"), padx=4)
    detailsFrameLabel.place(x=20, y=67)
    detailsFrame.pack_propagate(False)

    placeholder = get_local_ip()
    ipEntryLabel = ctk.CTkLabel(detailsFrame, text="IP: ", font=("Segoe UI", 13, "bold"))
    ipEntryLabel.place(x=10, y=15)
    ipEntry = ctk.CTkEntry(detailsFrame, height=13, width=150, font=("Consolas", 12), placeholder_text=placeholder if placeholder is not None else "192.168.0.101", validate="key", validatecommand=(root.register(validate_ip), "%P"))
    ipEntry.place(x=30, y=20)
    ipEntry.bind("<Return>", lambda e: ipEntry.focus_force() if port_added else None)

    connectButton = ctk.CTkButton(root, text="Connect", font=("Segoe UI", 16, "bold"), command=lambda: receiver_window(root, ipEntry.get(), portEntry.get()))


    root.mainloop()


def receiver_window(window, ip, port):
    global finished, sent_data

    window.destroy()
    root = ctk.CTk()
    root.iconbitmap("./Assets/Icon.ico")
    root.title("WiFileShare: Receive")
    positionRight = int(root.winfo_screenwidth()/2 - 500/2)
    positionDown = int(root.winfo_screenheight()/2 - 235/2)
    root.geometry(f"500x235+{positionRight}+{positionDown - 50}")
    root.resizable(0, 0)

    title = ctk.CTkLabel(root, text="WiFileShare", font=("Segoe UI", 40, "bold"))
    title.place(x=145, y=10)

    def receive(ip, port):
        global finished, cancelled, tobeexit

        def on_closing():
            global cancelled, tobeexit
            
            if not finished:
                if tkinter.messagebox.askyesno("Are you sure?", "Are you sure you want to stop the receiving?"):
                    cancelled = True
                    tobeexit = True
                else:
                    pass
            else:
                root.destroy()
                
        root.protocol("WM_DELETE_WINDOW", on_closing)

        inFrame = ctk.CTkFrame(root, width=480, height=120, corner_radius=10, border_width=2, fg_color="transparent")
        inFrame.place(x=10, y=80)
        inFrameLabel = ctk.CTkLabel(root, text="Sharing Insight", font=("Segoe UI", 14, "bold"), padx=4)
        inFrameLabel.place(x=20, y=67)
        inFrame.pack_propagate(False)

        progressLabel = ctk.CTkLabel(inFrame, text="Progress:", font=("Segoe UI", 13, "bold"))
        progressLabel.place(x=10, y=10)
        progressbar = ctk.CTkProgressBar(inFrame)
        progressbar.place(x=80, y=21)
        progressbar.set(0)
        progressindecatorlabel = ctk.CTkLabel(inFrame, text="", font=("Segoe UI", 13))
        progressindecatorlabel.place(x=285, y=10)

        statusLabel = ctk.CTkLabel(inFrame, text="Status: ", font=("Segoe UI", 13, "bold"))
        statusLabel.place(x=10, y=35)
        statusValueLabel = ctk.CTkLabel(inFrame, text="", font=("Consolas", 13, "bold"))
        statusValueLabel.place(x=60, y=36)

        transferSpeedLabel = ctk.CTkLabel(inFrame, text="Transfer Speed: ", font=("Segoe UI", 13, "bold"))
        transferSpeedLabel.place(x=10, y=60)
        transferSpeedValueLabel = ctk.CTkLabel(inFrame, text="", font=("Consolas", 13, "bold"))
        transferSpeedValueLabel.place(x=110, y=61)

        elapsedTimeLabel = ctk.CTkLabel(inFrame, text="Elapsed Time: ", font=("Segoe UI", 13, "bold"))
        elapsedTimeLabel.place(x=10, y=85)

        elapsedTimeValueLabel = ctk.CTkLabel(inFrame, text="", font=("Consolas", 13, "bold"))
        elapsedTimeValueLabel.place(x=110, y=86)

        def show_other_values():
            global finished

            def format_time(seconds):
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                return "%d:%02d:%02d" % (h, m, s)

            def get_speed_with_unit(size_in_kb):
                if size_in_kb < 1024:
                    return f"{size_in_kb:.2f} KB/s"
                elif size_in_kb < 1024 * 1024:
                    size_in_mb = size_in_kb / 1024.0
                    return f"{size_in_mb:.2f} MB/s"
                else:
                    size_in_gb = size_in_kb / (1024.0 * 1024.0)
                    return f"{size_in_gb:.2f} GB/s"
            
            while not finished:
                if not transfered:
                    elapsed_time = time.time() - start_time
                    transfer_speed = (sent_data / elapsed_time) / 1024
                    elapsedTimeValueLabel.configure(text=format_time(elapsed_time))
                    transferSpeedValueLabel.configure(text=get_speed_with_unit(transfer_speed))
                if "!" not in statusValueLabel.cget("text"):
                    if statusValueLabel.cget("text").endswith("..."):
                        statusValueLabel.configure(text=str(statusValueLabel.cget("text")).replace("...", ""))
                    else:
                        statusValueLabel.configure(text=str(statusValueLabel.cget("text"))+".")
                time.sleep(1)
        home_directory = Path.home()
        save_path = home_directory / "Documents"
        finished = False
        transfered = False
        cancelled = False
        tobeexit = False
        def delete():
            global transfered, finished
            transfered = True
            statusValueLabel.configure(text="Cleaning up")
            progressbar.configure(mode="indeterminate")
            shutil.rmtree(tempPath)
            progressbar.set(1)
            progressbar.configure(mode="determined")
            progressbar.set(progressbar.get())
            finished = True
            if tobeexit:
                root.destroy()
            else:
                statusValueLabel.configure(text="Transfer aborted from Host Server!")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect((ip, int(port)))
            except ConnectionRefusedError:
                tkinter.messagebox.showerror("Connection Failed!", "Unable to connect with the server! Please input the correct IP and Port.")
                root.after(10, lambda: [root.destroy(), receive_window(None)])
            except TimeoutError:
                tkinter.messagebox.showerror("Connection Failed!", "Unable to connect with the server! Please input the correct IP and Port.")
                root.after(10, lambda: [root.destroy(), receive_window(None)])
            statusValueLabel.configure(text="Transfering")
            name = client_socket.recv(9216)
            total_size = int(client_socket.recv(9216))
            tempPath = tempfile.mkdtemp(prefix="WiFileShare_")
            zip_path = os.path.join(tempPath, name.decode())
            sent_data = 0
            with open(zip_path, 'wb') as file:
                data = client_socket.recv(153600)
                start_time = int(time.time())
                threading.Thread(target=show_other_values, daemon=True).start()
                while data:
                    if cancelled:
                        break
                    if b"||--||-@#%#(&*@#-||Stop||-@!^%^#$&-||--||" in data:
                        cancelled = True
                        break
                    file.write(data)
                    data = client_socket.recv(153600)
                    sent_data += len(data)
                    progressbar.set(sent_data / total_size)
                    prcntge = (sent_data * 100) / total_size
                    progressindecatorlabel.configure(text=f"{prcntge:.2f}%")
        if not cancelled:
            progressbar.set(1)
            progressindecatorlabel.configure(text=f"{100:.2f}%")
            transfered = True
            statusValueLabel.configure(text="Finalizing")
            progressbar.configure(mode="indeterminate")
            save_path = save_path / "WiFileShare" / f"Received_{int(time.time())}"
            save_path.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(str(save_path))
            shutil.rmtree(tempPath)
            finished = True
            progressbar.configure(mode="determinate")
            statusValueLabel.configure(text="Transfer Completed!")
            ctk.CTkButton(root, text="Open", font=("Seoge UI", 15, "bold"), height=20, command=lambda: subprocess.Popen(f"explorer \"{save_path}\"")).place(x=200, y=205)
        if cancelled:
            delete()
        ctk.CTkButton(root, text="Home", font=("Seoge UI", 15, "bold"), height=20, command=lambda: [root.destroy(), main(True)]).place(x=350, y=205)
    threading.Thread(target=receive, args=(ip, port, ), daemon=True).start()
    root.mainloop()


def main(boot: bool=True):
    root = ctk.CTk()
    ctk.set_appearance_mode("system")

    root.title("WiFileShare")
    root.iconbitmap("./Assets/Icon.ico")
    positionRight = int(root.winfo_screenwidth()/2 - 500/2)
    positionDown = int(root.winfo_screenheight()/2 - 200/2)
    root.geometry(f"500x200+{positionRight}+{positionDown - 50}")
    root.resizable(0, 0)

    def arrange(icon: ctk.CTkLabel = None, title: ctk.CTkLabel = None, arrange: bool=False):
        if icon:
            icon.destroy()
        def move_title(l):
            c = [i for i in range(10, 120)]
            c.reverse()
            for i, y in enumerate(c):
                l.place(y=y)
                if i%5 == 0:
                    time.sleep(0.0000009)
        
        def move_send_button(l):
            c = [i for i in range(-173, 75)]
            for i, x in enumerate(c):
                l.place(x=x)
                if i%9 == 0:
                    time.sleep(0.0000009)
        
        def move_receive_button(l):
            c = [i for i in range(283, 500)]
            c.reverse()
            for i, x in enumerate(c):
                l.place(x=x)
                if i%9 == 0:
                    time.sleep(0.0000009)
    
        if not arrange:
            title = ctk.CTkLabel(root, text="WiFileShare", font=("Segoe UI", 40, "bold"))
            title.place(x=145, y=10)

        send = ctk.CTkLabel(root, text="", image=ctk.CTkImage(PIL.Image.open("./Assets/Send.png"), PIL.Image.open("./Assets/Send.png"), (140, 45)))
        send.bind("<Button-1>", lambda e: send_window(root))
        send.bind("<Enter>", lambda e: root.configure(cursor="hand2"))
        send.bind("<Leave>", lambda e: root.configure(cursor=""))
        send.place(x=75, y=120)

        receive = ctk.CTkLabel(root, text="", image=ctk.CTkImage(PIL.Image.open("./Assets/Receive.png"), PIL.Image.open("./Assets/Receive.png"), (140, 45)))
        receive.bind("<Button-1>", lambda e: receive_window(root))
        receive.bind("<Enter>", lambda e: root.configure(cursor="hand2"))
        receive.bind("<Leave>", lambda e: root.configure(cursor=""))
        receive.place(x=283, y=120)

        if arrange:
            threading.Thread(target=move_title, daemon=True, args=(title, )).start()
            threading.Thread(target=move_send_button, daemon=True, args=(send, )).start()
            threading.Thread(target=move_receive_button, daemon=True, args=(receive, )).start()


    if boot:
        si, st = splash(root)
        root.after(750, lambda: arrange(si, st, True))
    else:
        root.after(0, lambda: arrange(arrange=False))
    root.mainloop()

if __name__ == "__main__":
    main()
