from socket import socket, AF_INET, SOCK_DGRAM
from . import pnpacket


class PNClient:
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._sock_fd = socket(AF_INET, SOCK_DGRAM)

    def send(self, pnPacket: pnpacket.PNPacket):
        strPkt = pnPacket.stringfy()
        self._sock_fd.sendto(strPkt.encode(), (self._host, self._port))