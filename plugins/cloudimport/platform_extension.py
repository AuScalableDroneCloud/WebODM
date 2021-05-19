from abc import ABC, abstractmethod
from app.plugins import get_current_plugin
from .cloud_platform import CloudPlatform
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from webodm import settings
from django.utils.encoding import force_bytes, force_text
from app.plugins import logger
import base64
import random

class PlatformExtension(CloudPlatform):
    """A platform extension is a platform with extra capacities. It may require extra configuration, or it might provide new features."""

    def __init__(self, name, folder_url_example):
         super().__init__(name, folder_url_example)
    
    def get_form_fields(self, user_id):
        """Return a list of Field instances so that configuration can be set"""
        return []
    
    def get_api_views(self):
        """Return a lists of APIViews to mount"""
        return []  
        

class FormField(ABC):
    def __init__(self, key, platform_name, default_value):
        self.key = key
        self.field_id = "{}_{}".format(platform_name, key)
        self.default_value = default_value
        
    @abstractmethod
    def get_django_field(self, user_data_store):
        """Return a django field"""
    
    @abstractmethod    
    def get_stored_value(self, user_data_store):    
        """Retrieve the value from the data store"""
    
    @abstractmethod    
    def save_value(self, user_data_store, form):    
        """Save the value in the form to the data store"""

class StringField(FormField):
    def __init__(self, key, platform_name, default_value):
        super().__init__(key, platform_name, default_value)
    
    def get_stored_value(self, user_data_store):
        return user_data_store.get_string(self.field_id, default=self.default_value)
    
    def save_value(self, user_data_store, form):
        value = form.cleaned_data[self.field_id]
        user_data_store.set_string(self.field_id, value)

class EncryptedStringField(FormField):
    """
    Enter/edit/store an encrypted string field

    initially tried django-encrypted-model-fields and django-fernet-fields
    but there are compaibility issues, and we wanted the ability
    to pass around the encrypted value and decrypt later

    https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet
    https://stackoverflow.com/a/66191826/866759
    """

    def __init__(self, key, platform_name, default_value):
        super().__init__(key, platform_name, default_value)
        #Salt should ideally be from os.urandom, requires storing salt values somewhere
        #using a salt generated from user_id is less secure, but better than a constant
        self.f = None
        self.gen_salt(1234) #Start with a constant

    def gen_salt(self, seed=0, length=16):
        """Call this to generate a salt based on a provided seed integer"""
        random.seed(seed)
        salt = bytes([random.getrandbits(8) for i in range(length)])
        self.setup(salt)

    def setup(self, salt):
        """Init the encryption using provided salt data (bytes)"""
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=salt,
                         iterations=100000,
                         backend=default_backend())

        #Our key is defined in settings.py from an environment var
        #(Using settings.SECRET_KEY fails in production because worker/webapp have differing values)
        key = base64.urlsafe_b64encode(kdf.derive(settings.ENCRYPTION_KEY.encode('utf-8')))
        self.f = Fernet(key)

    def decrypt_value(self, value):
        """Decrypts a provided string using the active salt/key"""
        value = force_bytes(value)
        try:
            return force_text(self.f.decrypt(value))
        except (InvalidToken) as e:
            logger.info("Invalid encrypted data!")
            return ""

    def get_encrypted_value(self, user_data_store):
        """Get the data without decryption, can use decrypt_value() later to 
        decrypt when/as needed rather than passing around plaintext"""
        return user_data_store.get_string(self.field_id, default=self.default_value)

    def get_stored_value(self, user_data_store):
        encrypted = self.get_encrypted_value(user_data_store)
        if not encrypted:
            return None
        return self.decrypt_value(encrypted)

    def save_value(self, user_data_store, form):
        value = form.cleaned_data[self.field_id]
        encrypted = self.f.encrypt(bytes(value, 'utf-8'))
        user_data_store.set_string(self.field_id, force_text(encrypted))

