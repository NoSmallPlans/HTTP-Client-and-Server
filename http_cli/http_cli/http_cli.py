# Echo client program
import socket

HOST = '127.0.0.1'    # The remote host
PORT = 80              # The same port as used by the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Another one')
    data = s.recv(1024)
print('Received', repr(data))
input("hit any key")
