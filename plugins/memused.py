from .plugin import Plugin
import logging
import shutil

logging = logging.getLogger(__name__)

class MemUsed(Plugin):

    name = "MEMORY USED"

    def __init__(self, position):
        Plugin.__init__(self, position)

    def update(self):
        total, used, free = shutil.disk_usage(__file__)
        return [f"{int(used / total * 100)}% - {int(free / (2**30))}Gb"], None
