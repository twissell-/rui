import transmissionrpc
import qbittorrent

from core import config

class TorrentClient(object):
    def __init__(self, clientConfig=config.get('downloads.torrentClient')):
        super(TorrentClient, self).__init__()
        self._client = transmissionrpc.Client(**clientConfig)

    def add(self, torrentFile, destinationPath):
        paused = config.get('downloads.startPaused')
        self._client.add_torrent(torrentFile, download_dir=destinationPath, paused=paused)


class QBitTorrentClient(object):
    def __init__(self, clientConfig=config.get('downloads.torrentClient')):
        super(QBitTorrentClient, self).__init__()
        self._client = qbittorrent.Client('http://%s:%s' % (clientConfig['address'], clientConfig['port']))
        self._client.login(clientConfig['user'], clientConfig['password'])

    def add(self, torrentFile, destinationPath, name='', category='', tags=''):
        self._client.set_preferences(
            start_paused_enabled=config.get('downloads.startPaused'), content_layout='NoSubfolder')
        self._client.download_from_link(torrentFile, savepath=destinationPath, rename=name, category=category, tags=tags)