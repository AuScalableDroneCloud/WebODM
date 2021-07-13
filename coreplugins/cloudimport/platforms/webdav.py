# This platform connects to a webdav server using the webdavclient3 python module
# Currently only tested on the AARNet CloudStor service, but should work on any webdav interface
from os import path
from plugins.cloudimport.cloud_platform import File, Folder
from plugins.cloudimport.extensions.cloud_webdav import CloudWebDAV
from app.plugins import get_current_plugin, logger

class Platform(CloudWebDAV):
    def __init__(self):
        super().__init__('WebDAV', 'https://{server-url}/{path-to-folder}')

