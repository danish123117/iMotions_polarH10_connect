import socket
# test tcp server to act as a dummy api events monitor for iMotions
def start_tcp_server():
    TCP_IP = '127.0.0.1'
    TCP_PORT = 8089
    BUFFER_SIZE = 1024  # Buffer size for receiving data

    # Create a TCP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((TCP_IP, TCP_PORT))
        server_socket.listen(1)
        print(f"TCP server listening on {TCP_IP}:{TCP_PORT}...")

        while True:
            # Accept a connection from the client
            conn, addr = server_socket.accept()
            with conn:
                print(f"Connection established with {addr}")
                while True:
                    data = conn.recv(BUFFER_SIZE)
                    if not data:
                        print(f"Connection closed by {addr}")
                        break
                    print("Received data:", data.decode('utf-8'))

if __name__ == "__main__":
    start_tcp_server()
