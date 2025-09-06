import socket

#sockets are endpoints that receives data
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((socket.gethostname(),1234))

full = ''
while True:
    msg = s.recv(2)  #buffer, how much data you wanna receive
    if len(msg) <= 0:
        break
    full = msg.decode("utf-8")

