from serial.tools import list_ports
from serial import Serial
import threading
import socket
import time
import select


PING_DELAY = 100
HOST = '' # Standard loopback interface address (localhost)
PORT = 54321  # Port to listen on (non-privileged ports are > 1023)

active_links = []

class SerialNetworkLink():
    def __init__(self, index, port, socket_port_number):
        self.link_name = index
        self.serial_port_name = port.device
        self.socket_port_number = socket_port_number
        self.last_ping = time.time()

    def Connect(self):
        self.serial_connection = Serial(self.serial_port_name,  baudrate=115200, write_timeout=10)
        print(f'[{self.link_name}] Serial port:{self.serial_port_name} linked to Socket port:{self.socket_port_number}')

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(self.socket_port_number)
        self.socket.bind((HOST, self.socket_port_number))
        #self.socket = socket.create_server((HOST, self.socket_port_number))
        self.connect_thread = threading.Thread(target=self.AwaitConnection, args=())
        self.connect_thread.start()


    def AwaitConnection(self):
        self.socket.listen(1)
        print(f'[{self.link_name}] Awaiting socket connection...')

        self.connected, self.address = self.socket.accept()

        self.link_thread = threading.Thread(target=self.Transmit, args=())
        self.link_thread.start()

        print(f'[{self.link_name}] Connected!')

    def Transmit(self):
        while self.serial_connection.is_open:
            if time.time() - self.last_ping > PING_DELAY:
               print(f'[{self.link_name}] Alive!')
               self.last_ping = time.time()
            outgoing = self.serial_connection.read_all()
            if len(outgoing) > 0:
                #print(f'Transmitting: {outgoing}')
                try:
                    self.connected.send(outgoing)
                except:
                    self.Reopen()
                    break
            try:
                r,_,_ = select.select([self.socket],[],[],0.01)

                if r:
                    incoming = self.connected.recv(1024)
                    if len(incoming) > 0:
                        #print(f'Recieved: {incoming}')
                        self.serial_connection.write(incoming)
            except:
                self.Reopen()
                break


    def Close(self):
        self.connected.close()
        self.socket.close()
        self.serial_connection.close()
        print(f'[{self.link_name}] Closed')

    def Reopen(self):
        self.Close()
        time.sleep(5)
        self.Connect()


def main():
    connected = 0
    serial_ports = list(list_ports.comports())
    i = 0
    for serial_port in serial_ports:
        print(f'Available port: {serial_port.name}, {serial_port.device}')
        connect = input('Connect [y/n]? ')
        if connect.lower() == 'y':
            active_links.append(SerialNetworkLink(i, serial_port, PORT + i))
        i = i + 1

    for link in active_links:
        link.Connect()


# import argparse
# args = parser.parse_args()
if __name__ == '__main__':
    main()
