import socket
from tqdm import tqdm

def receive_file(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        name = client_socket.recv(9216)
        with open(name.decode(), 'wb') as file:
            data = client_socket.recv(9216)
            while data:
                file.write(data)
                data = client_socket.recv(9216)
    
        print("File received successfully")

if __name__ == "__main__":
    host = "127.0.0.1"  # Replace with the IP address of the server
    port = 12345

    receive_file(host, port)
