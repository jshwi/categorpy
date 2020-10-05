"""
parse
=====

Parse data files and magnet-links
"""
import os

# noinspection PyPackageRequirements
import bencodepy

from . import locate, log, textio


class Torrents:
    """Parse downloaded data for human readable categorisation"""

    logger = log.get_logger()

    def __init__(self):
        self.client_dir = locate.APPDIRS.client_dir
        self.path = os.path.join(self.client_dir, "torrents")
        self.paths = []
        self.object = {}
        self._get_torrent_paths()

    def _get_torrent_paths(self):
        """Get the torrent magnet-link files

        :return: List of torrent magnet-links
        """
        if os.path.isdir(self.path):
            self.paths.extend(
                [os.path.join(self.path, t) for t in os.listdir(self.path)]
            )

    @staticmethod
    def _read_bencode_file(fullpath):
        # read bytes to buffer from file's full path
        fullpathio = textio.TextIO(fullpath)
        fullpathio.read_bytes()
        return fullpathio.output

    @classmethod
    def parse_bencode_object(cls, bencode):
        """take bencode content (not path) and convert it to human
        readable text

        :param bencode: Bytes read from torrent file
        """
        try:
            obj = bencodepy.decode(bencode)
            try:
                # noinspection PyTypeChecker
                result = obj[b"magnet-info"][b"display-name"]
                return result.decode("utf-8").replace("+", " ")
            except KeyError as err:
                cls.logger.exception(str(err))
                return None
        except bencodepy.exceptions.BencodeDecodeError as err:
            cls.logger.exception(str(err))
            return None

    def parse_torrents(self):
        """Call to get the readable content from the bencode and create
        a dictionary object of names and their corresponding magnets
        """
        for path in self.paths:
            try:
                # get the bencode bytes from their .torrent file
                bencode = self._read_bencode_file(path)
            except IsADirectoryError as err:
                self.logger.exception(str(err))
                continue

            # parse these bytes into human readable plaintext
            decoded = self.parse_bencode_object(bencode)
            if decoded:

                # update the torrent file object with the torrent file's
                # name as the key and it's path as the value
                self.object.update({decoded: os.path.basename(path)})

    def get_decoded_names(self):
        """Return a list of decoded names

        :return: List of decoded magnet names
        """
        return list(self.object.keys())
