from serial.tools import list_ports
from serial import Serial
import threading
import socket

num_connected = 0

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 54321  # Port to listen on (non-privileged ports are > 1023)

active_links = []

class SerialNetworkLink():
    def __init__(self, port, socket_port_number):
        self.serial_port_name = port.device
        self.socket_port_number = socket_port_number
        self.link_name = num_connected

    def Connect(self):
        self.serial_connection = Serial(self.serial_port_name,  baudrate=115200)
        self.socket = socket.socket()
        self.socket.bind(('', self.socket_port_number))        

        self.connect_thread = threading.Thread(target=self.AwaitConnection, args=())
        self.connect_thread.start()

        if self.serial_connection.is_open:
            print(f"[{self.link_name}] Serial port:{self.serial_port_name} linked to Socket port:{self.socket_port_number}")
            print(f"[{self.link_name}] Awaiting socket connection...")

    def AwaitConnection(self):
        self.socket.listen(1)    
        self.connected, self.address = self.socket.accept()
        self.link_thread = threading.Thread(target=self.Transmit, args=())
        self.link_thread.start()

        print(f"[{self.link_name}] Connected!")

    def Transmit(self):
        while self.serial_connection.is_open:
            outgoing = self.serial_connection.read_all()
            if outgoing is not None:
                socket.send(outgoing)

            incoming = socket.recieve()
            if incoming is not None:
                self.serial_connection.write(incoming)
        print(f"Link broken:{self.serial_port_name} <-> {self.socket.host}:{self.socket.port}")

    def Close(self):
        self.socket.Close()
        self.serial_connection.close()


def main():
    serial_ports = list(list_ports.comports())
    for serial_port in serial_ports:
        print(f"Available port: {serial_port.name}, {serial_port.device}")
        connect = input("Connect? [y/n]")
        if connect.lower() == "y":
            link = SerialNetworkLink(serial_port, PORT + num_connected)
            active_links.append(link)

    for active_link in active_links:
        link.Connect()


# import argparse

# parser = argparse.ArgumentParser(description='Generate random reach task orders.')
# parser.add_argument('--pid', type=int, default=999, help='participant id')
# parser.add_argument('--rep', type=int, default=2, help='the number of repeats for each condition')

# args = parser.parse_args()
if __name__ == "__main__":
    main()
