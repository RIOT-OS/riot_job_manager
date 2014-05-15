"""
Models for board_app_creator application.
"""
from os.path import join as path_join
from re import sub as re_sub

from django.conf import settings
from django.db import models

import vcs
import usb

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

class USBDeviceManager(models.Manager):
    """
    Model manager for USBDevice
    """
    def update_from_system(self):
        """
        Get all currently connected USB devices and update data base
        accordingly
        """
        Port.objects.update(usb_device=None)
        for dev in usb.get_device_list():
            device, _ = self.get_or_create(usb_id=dev.usb_id, tag=dev.tag)
            device.ports.get_or_create(path=dev.device)

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

class USBDevice(models.Model):
    """
    Representation of USB devices.
    """
    tag = models.CharField(max_length=60, blank=True, null=True)
    usb_id = models.CharField(max_length=9, blank=False, null=False,
                              unique=True)

    objects = USBDeviceManager()

    def __str__(self):
        return self.usb_id

class Port(models.Model):
    """
    Ports a board is connected on to this system.
    """
    path = models.CharField(max_length=20, unique=True, blank=False, null=False)
    usb_device = models.ForeignKey('USBDevice', related_name='ports')

    def __str__(self):
        return self.path

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
    usb_device= models.OneToOneField('USBDevice', related_name='board')
    prototype_jobs = models.ManyToManyField('Jobs', related_name='+')

    def __str__(self):
        return self.riot_name

class Application(models.Model):
    """
    A representarion of a RIOT application.
    """
    name = models.CharField(max_length=16, unique=True, blank=False,
                            null=False)
    path = models.CharField(max_length=256, default=None, null=True,
                            blank=True)
    repository = models.ManyToManyField('Repository', related_name='applications',
                                        through='ApplicationTree')

class ApplicationTree(models.Model):
    """
    Transit class between Application and Repository.
    """
    repo = models.ForeignKey('Repository', related_name='application_trees')
    tree_name = models.CharField(max_length=256, unique=True, null=False,
                                 blank=False)
    application = models.ForeignKey('Application', related_name='applications',
                                    unique=True, blank=False, null=False)

class Job(models.Model):
    """
    A representation of a Jenkins job.
    """
    namespace = models.IntegerField(choices=((0, 'RIOT'), (1, 'Thirdparty')),
                                    blank=False, null=False, default=0)
    name = models.CharField(max_length=64, unique=True, blank=False, null=False)
    board = models.ForeignKey('Board', related_name='boards')

    def __str__(self):
        return self.name

    @property
    def path(self):
        """
        The path to the application.
        """
        return path_join(settings.JENKINS_JOBS_PATH, self.name)
