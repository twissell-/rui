import qbittorrentapi
import transmissionrpc

from rui.common import config


class TransmissionTorrentClient(object):
    def __init__(self, clientConfig=config.get("torrentLoader.torrentClient")):
        super(TransmissionTorrentClient, self).__init__()
        self._client = transmissionrpc.Client(**clientConfig)

    def add(self, torrentFile, destinationPath):
        paused = config.get("torrentLoader.startPaused")
        self._client.add_torrent(
            torrentFile, download_dir=destinationPath, paused=paused
        )


class QBitTorrentClient(object):
    def __init__(self, clientConfig=config.get("torrentLoader.torrentClient")):
        super(QBitTorrentClient, self).__init__()

        conn_info = dict(
            host=clientConfig["address"],
            port=clientConfig["port"],
            username=clientConfig["user"],
            password=clientConfig["password"],
        )

        self._client = qbittorrentapi.Client(**conn_info)
        try:
            self._client.auth_log_in()
        except qbittorrentapi.LoginFailed as e:
            print(e)

    def add(self, torrentFileUrl, destinationPath, name="", category="", tags=""):
        self._client.app_setPreferences(
            prefs={
                "start_paused_enabled": config.get("torrentLoader.startPaused"),
                "create_subfolder_enabled": False,
            }
        )

        self._client.torrents_add(
            urls=torrentFileUrl,
            save_path=destinationPath,
            rename=name,
            category=category,
            tags=tags,
        )
