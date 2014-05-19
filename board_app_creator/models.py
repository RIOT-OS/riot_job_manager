"""
Models for board_app_creator application.
"""
from os.path import join as path_join, relpath
from re import sub as re_sub

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save, post_save

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
        return self.get_or_create(url=vcs_repo.url,
                                  path=relpath(vcs_repo.directory,
                                               settings.RIOT_REPO_BASE_PATH))

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
            try:
                port = Port.objects.get(path=dev.device)
                port.usb_device = device
            except Port.DoesNotExist:
                port = Port(path=dev.device)
            port.save()

class BoardManager(models.Manager):
    """
    Model manager for Board
    """
    def all_real(self):
        """
        All boards that do not have the no_board flag set.
        """
        return self.filter(no_board=False)

    def hidden_shown(self):
        return self.filter(no_board=True).exists()

class ApplicationManager(models.Manager):
    """
    Model manager for Application
    """
    def all_real(self):
        """
        All applications that do not have the no_application flag set.
        """
        return self.filter(no_application=False)

    def hidden_shown(self):
        return self.filter(no_application=True).exists()

class Repository(models.Model):
    """
    A RIOT related repository
    """
    url = models.CharField(max_length=256, verbose_name="URL", unique=True,
                           blank=False, null=False)
    path = models.CharField(max_length=256, unique=True)
    default_branch = models.CharField(max_length=32, blank=False, null=False,
                                      default='master')
    vcs = models.CharField(max_length=8, choices=[('git', 'Git')], blank=False,
                           null=False, default='git', verbose_name="VCS")
    has_boards_tree = models.BooleanField(default=False, null=False,
                                       verbose_name="Has Boards tree")
    boards_tree = models.CharField(max_length=256, default=None, null=True,
                                   blank=True)
    has_cpu_tree = models.BooleanField(default=False, null=False,
                                       verbose_name="Has CPU tree")
    cpu_tree = models.CharField(max_length=256, default=None, null=True,
                                blank=True, verbose_name="CPU tree")
    is_default = models.BooleanField(default=False, null=False)

    objects = RepositoryManager()

    class Meta:
        ordering = ['-is_default', 'path']

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

    def has_application_trees(self):
        return self.application_trees.exists()

    def unique_application_trees(self):
        return sorted(list(set(self.application_trees.values_list('tree_name', flat=True))))

class USBDevice(models.Model):
    """
    Representation of USB devices.
    """
    tag = models.CharField(max_length=60, blank=True, null=True)
    usb_id = models.CharField(max_length=9, blank=False, null=False,
                              unique=True)

    objects = USBDeviceManager()

    def __str__(self):
        connected = " [not connected]" if not self.ports.exists() else ""
        if self.tag:
            return "{} ({}){}".format(self.usb_id, self.tag, connected)
        else:
            return "{}{}".format(self.usb_id)

class Port(models.Model):
    """
    Ports a board is connected on to this system.
    """
    path = models.CharField(max_length=20, unique=True, blank=False, null=False)
    usb_device = models.ForeignKey('USBDevice', related_name='ports', blank=True,
                                   null=True)

    def __str__(self):
        return self.path

class Board(models.Model):
    """
    A board in one of the RIOT repositories.
    """
    riot_name = models.CharField(max_length=16, unique=True, blank=False,
                                 null=False, verbose_name="RIOT name")
    repo = models.ForeignKey('Repository', related_name='boards',
                             limit_choices_to={'has_boards_tree': True},
                             verbose_name='repository', blank=True, null=True)
    cpu_repo = models.ForeignKey('Repository', related_name='cpus',
                                 limit_choices_to={'has_cpu_tree': True},
                                 verbose_name='CPU Repository', blank=True,
                                 null=True)
    usb_device= models.OneToOneField('USBDevice', related_name='board',
                                     blank=True, null=True,
                                     verbose_name="USB Device")
    prototype_jobs = models.ManyToManyField('Job', related_name='+', blank=True)
    no_board = models.BooleanField(default=False, blank=False, null=False,
                                   editable=False)

    objects = BoardManager()

    def __str__(self):
        return self.riot_name

    class Meta:
        ordering = ['riot_name']

class Application(models.Model):
    """
    A representarion of a RIOT application.
    """
    name = models.CharField(max_length=16, blank=False, null=False)
    path = models.CharField(max_length=256, default=None, null=True,
                            blank=True)
    repository = models.ManyToManyField('Repository', related_name='applications',
                                        through='ApplicationTree')
    blacklisted_boards = models.ManyToManyField('Board', blank=True,
        related_name='blacklisted_applications')
    whitelisted_boards = models.ManyToManyField('Board', blank=True,
        related_name='whitelisted_applications')
    no_application = models.BooleanField(default=False, blank=False, null=False,
                                         editable=False)

    objects = ApplicationManager()

    class Meta:
        ordering = ['name']

class ApplicationTree(models.Model):
    """
    Transit class between Application and Repository.
    """
    repo = models.ForeignKey('Repository', related_name='application_trees')
    tree_name = models.CharField(max_length=256, null=False, blank=False)
    application = models.ForeignKey('Application', related_name='application_tree',
                                    unique=True, blank=True, null=True)

    class Meta:
        unique_together = ("repo", "tree_name", "application")

    def __str__(self):
        return self.tree_name

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

def repository_pre_save(sender, instance, raw, using, update_fields, **kwargs):
    if instance.has_boards_tree:
        error = ValidationError("{} is no tree in the repository.".format(
            instance.boards_tree))
        try:
            if not isinstance(instance.vcs_repo.head.get_file(instance.boards_tree),
                              vcs.Tree):
                raise error
        except ValueError:
            raise error

def repository_post_save(sender, instance, created, raw, using, update_fields,
                         **kwargs):
    for tree, subtrees, _ in instance.vcs_repo.head.base_tree.walk():
        tree = tree if tree == '.' else tree[2:]
        if created and instance.has_boards_tree and tree == instance.boards_tree:
            for riot_name in subtrees:
                board, created = Board.objects.get_or_create(riot_name=riot_name)
                if created:
                    board.repo = instance
                    try:
                        board.cpu_repo = Repository.objects.get(is_default=True)
                    except Repository.DoesNotExist:
                        pass
                    board.save()
        if created and instance.has_application_trees and tree == instance.application_trees.all():
            for name in subtrees:
                app, created = Application.objects.get_or_create(name=name)
                if created:
                    app.application_tree.update(application=instance)
                    app.save()


pre_save.connect(repository_pre_save, sender=Repository)
post_save.connect(repository_post_save, sender=Repository)
