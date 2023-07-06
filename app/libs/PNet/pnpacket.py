import json

class PNPacket:
    def __init__(self, packetId, JSON=None, useJSON=False, **kwargs):
        self._packetId = packetId
        self._jData: dict = {}
        if useJSON:
            self._jData = JSON
        else:
            for k, v in kwargs.items():
                self._jData[k] = v

    @classmethod
    def fromStr(cls, string):
        jsonData: dict = json.loads(string)
        pktId = jsonData.get("packetId")
        jsonData.pop("packetId", None)
        return cls(pktId, jsonData, True)

    def getPacketId(self) -> int:
        return self._packetId

    def getJSONData(self) -> dict | None:
        return self._jData

    def stringfy(self) -> str:
        JSONData = self._jData
        JSONData["packetId"] = self._packetId
        return json.dumps(self._jData)


PACKET_ID_SHUTDOWN = 1