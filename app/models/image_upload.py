import logging
logger = logging.getLogger('app.logger')
from .task import Task, assets_directory_path
from django.db import models
from django.utils.translation import gettext_lazy as _
from urllib.parse import urlparse

def image_directory_path(image_upload, filename):
    return assets_directory_path(image_upload.task.id, image_upload.task.project.id, filename)


class ImageUpload(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, help_text=_("Task this image belongs to"), verbose_name=_("Task"))
    image = models.ImageField(upload_to=image_directory_path, help_text=_("File uploaded by a user"), max_length=512, verbose_name=_("Image"))

    def __str__(self):
        return self.image.name

    def path(self):
        try:
            logger.info("PATH:" + str(self.image.path))
            return self.image.path
        except:
            #Get the filepath from the url
            url = self.url()
            p = urlparse(url)
            logger.info("URLPATH:" + p.path)
            return p.path

    def url(self):
        logger.info("URL:" + str(self.image.url))
        #This generates a url for private S3 buckets with expiry of ~1hr
        return self.image.url

    class Meta:
        verbose_name = _("Image Upload")
        verbose_name_plural = _("Image Uploads")
