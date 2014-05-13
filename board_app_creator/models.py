"""
Models for board_app_creator application.
"""
from django.db import models
import board_app_creator.fields as fields

class Board(models.Model):
    """
    A board in the RIOT repository.
    """
    riot_name = models.CharField(max_length=16, unique=True, blank=False,
                                 null=False)
    repository = models.URLField(blank=False, null=False)
    repository_tree = models.CharField(max_length=32, blank=False, null=False)
    cpu_repository = models.URLField()
    cpu_repository_tree = models.CharField(max_length=32, blank=False,
                                           null=False)
    usb_vid = fields.SmallHexField()
    usb_pid = fields.SmallHexField()

    def __str__(self):
        return self.riot_name
