import socket
from tqdm import tqdm
import os

def send_file(file_path, host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()

        print(f"Server listening on {host}:{port}")

        connection, address = server_socket.accept()
        print(f"Connection from {address}")

        file_size = os.path.getsize(file_path)

        connection.send(os.path.basename(os.path.abspath(file_path)).encode())

        with open(file_path, 'rb') as file:
            progress_bar = tqdm(range(file_size), unit="B", unit_scale=True, desc="Sending Files")
            data = file.read(9216)
            while data:
                connection.send(data)
                progress_bar.update(len(data))
                data = file.read(9216)
        progress_bar.close()
        server_socket.close()
        # print("File sent successfully")

if __name__ == "__main__":
    file_path = "File.txt"
    host = "127.0.0.1"
    port = 12345

    send_file(file_path, host, port)
