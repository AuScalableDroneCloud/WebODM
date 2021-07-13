# This platform connects to an ownCloud webdav server using the webdavclient3 python module
# For the AARNet CloudStor service this just predefines the server url field,
# so users only need their username and password
from plugins.cloudimport.extensions.cloud_webdav import CloudWebDAV

class Platform(CloudWebDAV):
    def __init__(self):
        super().__init__('CloudStor', 'https://cloudstor.aarnet.edu.au/plus/remote.php/webdav/{path-to-folder}')
        self.default_url = "https://cloudstor.aarnet.edu.au/plus/remote.php/webdav/"
        self.basepath = "https://cloudstor.aarnet.edu.au/plus/apps/files/?dir="

    def get_form_fields(self, user_id):
        return [self.get_server_user_field(), self.get_server_token_field(user_id)]

