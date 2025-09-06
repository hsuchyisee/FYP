import socket

#sockets are endpoints that receives data
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(), 1234))
s.listen(5) #queue of 5

#listen
while True:
    # clientsocket is from sender, address is where it comes from
    clientsocket, address = s.accept()
    print(f"Connection from {address} is established")
    clientsocket.send(bytes("Welcome","utf-8"))