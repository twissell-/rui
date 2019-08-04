import transmissionrpc

from core import config

class TorrentClient(object):
    def __init__(self, clientConfig=config.get('downloads.torrentClient')):
        super(TorrentClient, self).__init__()
        self._client = transmissionrpc.Client(**clientConfig)

    def add(self, torrentFile, destinationPath):
        paused = config.get('downloads.startPaused')
        self._client.add_torrent(torrentFile, download_dir=destinationPath, paused=paused)
