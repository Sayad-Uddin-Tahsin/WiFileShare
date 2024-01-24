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
                share_button.configure(state="disabled")
            self.list.remove(path)
            print(self.list)
            frame.destroy()

        def add_path(self, message):
            f = ctk.CTkFrame(self, border_width=2, fg_color="transparent", corner_radius=10)
            m = ctk.CTkLabel(f, text=message, wraplength=225, justify="left", font=("Sogue UI", 12, "bold"), fg_color="transparent", bg_color="transparent", corner_radius=100)
            m.pack(anchor="w", padx=5, pady=2, side="left")
            d = ctk.CTkButton(f, text="Delete", width=50, font=("Segoe UI", 13), fg_color=("#de0202", "#8B0000"), hover_color=("#8B0000", "#de0202"), border_color=("#FF0000", "#8B0000"), border_width=1, corner_radius=10, command=lambda f=f, p=message: self._delete(f, p))
            d.pack(anchor="e", padx=5, pady=2, side="right")
            f.pack(anchor="w", fill=ctk.BOTH, side="top", padx=10, pady=2)
            share_button.configure(state="normal")
            self.list.append(message)
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

    share_button = ctk.CTkButton(root, text="Share", font=("Segoe UI", 16, "bold"), state="disabled", command=lambda: shareWindow(root, listFrame.list))
    share_button.place(x=350, y=320)

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

    def send(window, tempPath, zipPath, label, iptext, iplabel):
        global hostSocket, dot_animate, finished, sent_data, transfered

        try:
            clientSocket, clientAddress = hostSocket.accept()
        except OSError as e:
            if str(e) == "[WinError 10038] An operation was attempted on something that is not a socket":
                pass 
            else:
                raise e
        
        def on_closing():
            if not finished:
                if tkinter.messagebox.askyesno("Are you sure?", "Are you sure you want to stop the transfer?"):
                    clientSocket.send("||--||-@#%#(&*@#-||Stop||-@!^%^#$&-||--||".encode())
                    clientSocket.close()
                    hostSocket.close()
                    root.destroy()
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

        def show_other_values():
            global finished, sent_data

            def format_time(seconds):
                # Format seconds into HH:MM:SS
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                return "%d:%02d:%02d" % (h, m, s)

            def get_speed_with_unit(size_in_kb):
                if size_in_kb < 1024:
                    return f"{size_in_kb} KB/s"
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
                clientSocket.send(data)
                sent_data += len(data)
                progressbar.set(sent_data / total_size)
                prcntge = (sent_data * 100) / total_size
                progressindecatorlabel.configure(text=f"{prcntge:.2f}%")
                data = file.read(153600)
        statusValueLabel.configure(text="Finalizing")
        progressbar.configure(mode="indeterminate")
        finished = True
        shutil.rmtree(tempPath)
        clientSocket.close()
        hostSocket.close()
        progressbar.configure(mode="determinate")
        transfered = True
        statusValueLabel.configure(text="Transfer Completed!")
        ctk.CTkButton(root, text="Home", font=("Seoge UI", 15, "bold"), height=20, command=lambda: [root.destroy(), main(True)]).place(x=350, y=205)

    
    def wait_for_connection(tempPath, zipPath):
        global dot_animate, hostSocket

        dot_animate = True
        hostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hostSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        addr = socket.gethostbyname(socket.gethostname())
        hostSocket.bind((addr, 0))
        print(f"{hostSocket.getsockname()[0]}:{hostSocket.getsockname()[1]}")
        connection_text = ctk.CTkLabel(root, text="Waiting for Connection", font=("Segoe UI", 15, "bold"))
        connection_text.place(x=170, y=80)
        threading.Thread(target=animate, args=(connection_text, ), daemon=True).start()
        ipText = ctk.CTkLabel(root, text=f"IP: ", font=("Segoe UI", 13, "bold"))
        ipText.place(x=170, y=110)
        ipAddText = ctk.CTkLabel(root, text=f"{hostSocket.getsockname()[0]}:{hostSocket.getsockname()[1]}", font=("Consolas", 14, "bold"))
        ipAddText.place(x=190, y=111)
        hostSocket.listen()
        threading.Thread(target=send, args=(root, tempPath, zipPath, connection_text, ipText, ipAddText)).start()

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
        receive.bind("<Button-1>", lambda e: print("Receive Click"))
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
