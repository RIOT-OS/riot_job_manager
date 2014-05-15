"""
Models for board_app_creator application.
"""
from os.path import join as path_join
from re import sub as re_sub

from django.conf import settings
from django.db import models

import board_app_creator.fields as fields

import vcs

class RepositoryManager(models.Manager):
    """
    Model manager for Repository
    """
    def get_or_create_from_path(self, path):
        """
        Get or create a repo from path
        """
        vcs_repo = vcs.get_repository(path)
        return self.get_or_create(url=vcs_repo.url, path=vcs_repo.directory)

    def get_or_create_from_url(self, url, vcs_type='git'):
        """
        Get or create a repo from URL
        """
        if url[-4:] == ".git":
            directory = re_sub(r'^.*/([^/]+)\.git$', r'\1', url)
        else:
            print(url[-4:])
            directory = re_sub(r'^.*/([^/]+)$', r'\1', url)
        path = path_join(settings.RIOT_REPO_BASE_PATH, directory)
        vcs_repo = vcs.get_repository(path, url=url, vcs=vcs_type)
        return self.get_or_create(url=vcs_repo.url, path=vcs_repo.directory)

class Repository(models.Model):
    """
    A RIOT related repository
    """
    url = models.URLField(unique=True, blank=False, null=False)
    path = models.CharField(max_length=256,
                            default=settings.RIOT_REPO_BASE_PATH)
    default_branch = models.CharField(max_length=32, blank=False, null=False,
                                      default='master')
    vcs = models.CharField(max_length=8, blank=False, null=False, default='git')
    has_boards_tree = models.BooleanField(default=False, null=False)
    boards_tree = models.CharField(max_length=256, default=None, null=True,
                                   blank=True)
    has_cpu_tree = models.BooleanField(default=False, null=False)
    cpu_tree = models.CharField(max_length=256, default=None, null=True,
                                blank=True)
    is_default = models.BooleanField(default=False, null=False)

    objects = RepositoryManager()

    def __str__(self):
        return self.url

    @property
    def vcs_repo(self):
        """
        Object representing the actual repository
        """
        if not hasattr(self, '_vcs'):
            self._vcs = vcs.get_repository(self.path, self.vcs, self.url)
        return self._vcs

class Board(models.Model):
    """
    A board in one of the RIOT repositories.
    """
    riot_name = models.CharField(max_length=16, unique=True, blank=False,
                                 null=False)
    repo = models.ForeignKey('Repository', related_name='boards',
                             limit_choices_to={'has_boards_tree': True},
                             verbose_name='repository')
    cpu_repo = models.ForeignKey('Repository', related_name='cpus',
                                 limit_choices_to={'has_cpu_tree': True},
                                 verbose_name='cpu_repository')
    usb_vid = fields.SmallHexField()
    usb_pid = fields.SmallHexField()

    def __str__(self):
        return self.riot_name
