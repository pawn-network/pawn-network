from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
from . import pnpacket


class PNServer:
    def __init__(self, host, port):
        self._port = port
        self._host = host
        self._sock_fd = socket(AF_INET, SOCK_DGRAM)
        self._shutdown = False
        self._listening = False
        self._threadId = None

    def thread_listener(self, callback=None, **kwargs):
        while True:
            if self._shutdown:
                break
            packet, client = self._sock_fd.recvfrom(1024)
            if packet is not None:
                pnPkt = pnpacket.PNPacket.fromStr(packet.decode())
                callback(pnPkt, client, **kwargs)

    def shutdown(self):
        self._shutdown = True

    def listen(self, callback=None, **kwargs):
        if self._shutdown:
            self._shutdown = False
        if self._listening is False:
            self._sock_fd.bind((self._host, self._port))
            thread = Thread(
                target=self.thread_listener, args=(callback,), kwargs=(kwargs)
            )
            thread.start()
            self._threadId = thread
            self._listening = True