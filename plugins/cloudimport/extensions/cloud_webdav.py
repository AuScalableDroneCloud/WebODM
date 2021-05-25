from abc import abstractmethod
from django import forms
from rest_framework.response import Response
from rest_framework import status
from app.plugins import get_current_plugin, logger
from app.plugins.views import TaskView
from ..platform_helper import get_platform_by_name
from ..platform_extension import PlatformExtension, StringField, EncryptedStringField
from plugins.cloudimport.extensions.cloud_library import CloudLibrary, GetAllFoldersTaskView
from plugins.cloudimport.cloud_platform import File, Folder, VALID_IMAGE_EXTENSIONS
import urllib

from webdav3.client import Client
from webdav3.exceptions import WebDavException
import pathlib

class CloudWebDAV(CloudLibrary):
    """As CloudLibrary but for WebDAV server

    This attempts to work within the framework set by CloudLibrary but adds the functionality to
    connect with a username and password to the server

    Files can not be accessed purely with a URL as for previous impolementations (Piwigo), the connection needs
    to be made first or all the connection details passed
    """

    def __init__(self, name, folder_url_example):
        self._client = None
        self.default_url = ""
        self.basepath = ""
        super().__init__(name, folder_url_example)

    def get_form_fields(self, user_id):
        return [self.get_server_url_field(), self.get_server_user_field(), self.get_server_token_field(user_id)]

    def serialize(self, **kwargs):
        base_payload = {'name': self.name, 'folder_url_example': self.folder_url_example}
        if kwargs['user'] != None:
            ds = get_current_plugin().get_user_data_store(kwargs['user'])
            server_url_field = self.get_server_url_field()
            server_url = server_url_field.get_stored_value(ds)
            server_user_field = self.get_server_user_field()
            server_user = server_user_field.get_stored_value(ds)
            server_token_field = self.get_server_token_field(kwargs['user'].id)
            server_token = server_token_field.get_stored_value(ds)
            base_payload['type'] = 'library'
            base_payload[server_url_field.key] = server_url
            base_payload[server_user_field.key] = server_user
            base_payload[server_token_field.key] = server_token
            return base_payload

        base_payload['type'] = 'platform'
        return base_payload

    def get_server_url_field(self):
        return ServerURLField(self.name, self.default_url)

    def get_server_user_field(self):
        return ServerUserField(self.name)

    def get_server_token_field(self, user_id):
        return ServerTokenField(self.name, user_id)

    # Cloud Platform
    def parse_url(self, url):
        #No parsing necessary
        return url

    def build_folder_api_url(self, information):
        return 'folder_api:' + information

    def parse_payload_into_folder(self, original_url, payload):
        #Just return the first entry
        return payload[0]

    def build_list_files_in_folder_api_url(self, information):
        return 'files_in_folder_api:' + information

    def library_folder_processing(self, files):
        """This method does nothing, but each platform might want to do some processing of the folders and they can, by overriding this method"""
        return files

    def get_credentials(self, ds, user_id):
        """Return dict with all data required for WebDAV connection
        """
        server_url_field = self.get_server_url_field()
        server_url = server_url_field.get_stored_value(ds)
        server_user_field = self.get_server_user_field()
        server_user = server_user_field.get_stored_value(ds)
        server_token_field = self.get_server_token_field(user_id)
        #server_token = server_token_field.get_stored_value(ds)
        #Save the encrypted data, decrypt at last minute before use
        server_token = server_token_field.get_encrypted_value(ds)
        connection_data = {
            'type' : 'webdav',
            'webdav_hostname': server_url,
            'webdav_login':    server_user,
            'webdav_password': server_token
        }
        return connection_data

    def connect(self, ds, user_id):
        """Connect to the server if necessary, the connection can be re-used by other methods
        (not required if each request is self-contained)

        This method takes the user_data_store and gets connection details from there
        """
        options = self.get_credentials(ds, user_id)
        self.connect_dict(options, user_id)

    def connect_dict(self, options, user_id):
        """Connect to the server if necessary, the connection can be re-used by other methods
        (not required if each request is self-contained)

        This method takes a dict containing connection details:
        "webdav_hostname", "webdav_login", "webdav_password"
        """
        if self._client:
            try:
                self._client.info("/")
            except (WebDavException) as e:
                logger.info("WebDAV client exception, re-connecting:" + str(e))
                self._client = None

        if self._client is None and options:
            #Dummy field for decryption
            es = ServerTokenField(self.name, user_id)
            options['webdav_password'] = es.decrypt_value(options['webdav_password'])
            self._client = Client(options)

    def download(self, url, filepath):
        #Use webdav connection to download file
        self._client.download_sync(remote_path=url, local_path=filepath)

    def _get_files(self, path):
        files = self._client.list(path)
        if len(files) == 0:
            return []

        #Skip the first entry if it is current path
        #(for some %*&#$ reason not all webdav servers do this)
        name = pathlib.Path(path).name
        first = files[0]
        if first[-1] == '/' and (name == first or name == first[0:-1] or first == 'webdav/'):
            return files[1:]
        return files

    #Recurse and return folders with number of image files/subfolders
    def _read_folder(self, path, recursive=0, extensions=None):
        if len(path) == 0 or path[-1] != '/': path = path + '/' 
        logger.info(" read folder:" + path)
        name = pathlib.Path(path).name
        #files = self._client.list(path)
        files = self._get_files(path)

        alldirs = []
        if recursive != 0 and path != '/':
            parent = str(pathlib.Path(path).parent)
            #print("PATH:",path,"PARENT:",parent)
            alldirs += [Folder('[/..] ' + parent, parent, 0)]

        if len(files) == 0:
            return alldirs

        contents = []
        folders = []
        for f in files:
            if f[0] == '.': continue
            if f[-1] == '/':
                #Include subfolders?
                if recursive > 0:
                    #print(path + f)
                    alldirs += self._read_folder(path + f, recursive-1, extensions=extensions)
                elif recursive < 0:
                    #Add the folders without counting their images, unknown image count
                    alldirs += [Folder(f[0:-1], path + f, -1)]
                else:
                    #Just add folders to list if not going into them
                    folders += [f]
            else:
                ext = pathlib.Path(f).suffix.lower()
                if extensions is None or ext in extensions:
                    contents += [f]

        #Skip current if no images or subfolders
        if len(contents) or len(folders):
            #Remove trailing slash for name
            #alldirs += [Folder(name[0:-1], path, len(contents))]
            alldirs += [Folder(name, path, len(contents))]
        logger.info(" read folder entries: " + str(len(alldirs)))
        return alldirs

    def _read_files(self, path, extensions=None):
        logger.info(" read files in folder:" + path)
        files = self._get_files(path)
        contents = []
        for f in files:
            if f[0] == '.' or f[-1] == '/': continue
            ext = pathlib.Path(f).suffix.lower()
            if extensions is None or ext in extensions:
                contents += [File(f, path + f)]

        logger.info(" read file entries" + str(len(contents)))
        return contents

    def call_api(self, api_url):
        if self._client is None:
            logger.info("WebDAV: No client, please connect first")
            return []

        #File filter for images and ground control points (.txt)
        ext_list = VALID_IMAGE_EXTENSIONS + ['.txt']

        #Get the type of request from the prefix
        req_type, url = api_url.split(':', maxsplit=1)
        #Decode url (spaces etc)
        url = urllib.parse.unquote(url)
        logger.info("CALLING API:" + req_type + "," + url)
        if req_type.startswith('folder_list_api'):
            #Returns all folders and sub-folders with number of images within
            #return self._read_folder(url, recursive=1, extensions=ext_list)
            return self._read_folder(url, recursive=-1, extensions=ext_list)

        if req_type == 'folder_api':
            #Returns info about a folder, including number of images
            return self._read_folder(url, recursive=0, extensions=ext_list)

        if req_type == 'files_in_folder_api':
            #Returns list of images in a folder
            return self._read_files(url, extensions=ext_list)

    def parse_payload_into_files(self, payload):
        return payload

    # Cloud Library
    def build_folder_list_api_url(self, server_url, root):
        #return 'folder_list_api:' + server_url
        return 'folder_list_api:' + root

    def parse_payload_into_folders(self, payload):
        #Already in Folders()
        return payload

class ServerURLField(StringField):
    def __init__(self, platform_name, default_url):
        super().__init__('server_url', platform_name, default_url)
        self.platform_name = platform_name

    def get_django_field(self, user_data_store):
        return forms.URLField(
            label="Server URL",
            help_text="Please insert the URL of the server",
            required=False,
            max_length=1024,
            widget=forms.URLInput(),
            initial=self.get_stored_value(user_data_store),
            validators=[self.validate_server_url])

    def validate_server_url(self, server_url_to_validate):
        platform = get_platform_by_name(self.platform_name)
        result = platform.verify_server_url(server_url_to_validate)
        if result != "OK":
            raise forms.ValidationError(result)

class ServerUserField(StringField):
    def __init__(self, platform_name):
        super().__init__('server_user', platform_name, '')
        self.platform_name = platform_name

    def get_django_field(self, user_data_store):
        return forms.CharField(
            label="Server user",
            help_text="Please insert the username/email to access the server",
            required=False,
            max_length=1024,
            widget=forms.TextInput(),
            initial=self.get_stored_value(user_data_store),
            validators=[])

class ServerTokenField(EncryptedStringField):
    def __init__(self, platform_name, user_id):
        super().__init__('server_token', platform_name, '')
        self.platform_name = platform_name
        self.user_id = user_id
        self.gen_salt(seed=user_id)

    def get_django_field(self, user_data_store):
        return forms.CharField(
            label="Server token",
            help_text="Please insert the password/token to access the server (stored encrypted)",
            required=False,
            max_length=1024,
            #Don't use PasswordInput as it does other things we don't want, just hide the content
            widget=forms.TextInput(attrs={'type':'password'}),
            initial=self.get_stored_value(user_data_store),
            validators=[])

