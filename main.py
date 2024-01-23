import customtkinter as ctk
import PIL.Image
import time
import threading

root = ctk.CTk()
ctk.set_appearance_mode("system")

root.title("WiFileShare")
root.iconbitmap("./Assets/Icon.ico")
positionRight = int(root.winfo_screenwidth()/2 - 500/2)
positionDown = int(root.winfo_screenheight()/2 - 200/2)
root.geometry(f"500x200+{positionRight}+{positionDown - 50}")
root.resizable(0, 0)

def splash():
    splash_image = ctk.CTkLabel(root, text="", image=ctk.CTkImage(PIL.Image.open("./Assets/Logo Light.png"), PIL.Image.open("./Assets/Logo Dark.png"), (100, 100)))
    splash_image.place(x=200, y=20)
    splash_text = ctk.CTkLabel(root, text="WiFileShare", font=("Segoe UI", 40, "bold"))
    splash_text.place(x=145, y=120)
    return splash_image, splash_text

def arrange(icon: ctk.CTkLabel, title: ctk.CTkLabel):
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

    send = ctk.CTkLabel(root, text="", image=ctk.CTkImage(PIL.Image.open("./Assets/Send.png"), PIL.Image.open("./Assets/Send.png"), (140, 45)))
    send.bind("<Button-1>", lambda e: print("Send Click"))
    send.bind("<Enter>", lambda e: root.configure(cursor="hand2"))
    send.bind("<Leave>", lambda e: root.configure(cursor=""))
    send.place(x=-173, y=120)

    receive = ctk.CTkLabel(root, text="", image=ctk.CTkImage(PIL.Image.open("./Assets/Receive.png"), PIL.Image.open("./Assets/Receive.png"), (140, 45)))
    receive.bind("<Button-1>", lambda e: print("Receive Click"))
    receive.bind("<Enter>", lambda e: root.configure(cursor="hand2"))
    receive.bind("<Leave>", lambda e: root.configure(cursor=""))
    receive.place(x=500, y=120)

    threading.Thread(target=move_title, daemon=True, args=(title, )).start()
    threading.Thread(target=move_send_button, daemon=True, args=(send, )).start()
    threading.Thread(target=move_receive_button, daemon=True, args=(receive, )).start()


si, st = splash()

root.after(750, lambda: arrange(si, st))
root.mainloop()
