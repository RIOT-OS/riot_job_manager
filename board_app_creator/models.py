"""
Models for board_app_creator application.
"""
import re
from os import listdir
from os.path import join as path_join, relpath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save, post_save

from model_utils.managers import InheritanceManager

import board_app_creator.validators as validators
import vcs
import usb
import jenkins.jobs

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
            directory = re.sub(r'^.*/([^/]+)\.git$', r'\1', url)
        else:
            directory = re.sub(r'^.*/([^/]+)$', r'\1', url)
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
                           blank=False, null=False,
                           validators=[validators.validate_git_repository])
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

    def save(self, *args, **kwargs):
        if self.is_default:
            qs = Repository.objects.filter(is_default=True)
            if self.pk != None:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                self.is_default = True
        super(Repository, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('repository-detail', (self.pk,))

    @property
    def vcs_repo(self):
        """
        Object representing the actual repository
        """
        if not hasattr(self, '_vcs'):
            self._vcs = vcs.get_repository(self.path, self.vcs, self.url)
        return self._vcs

    @property
    def weblink(self):
        """
        Tries to parse weblink from URL or returns None
        """
        ssh_guess = re.match(r"(?P<username>[a-z_][a-z0-9_]+)@(?P<hostname>[^:]+):(?P<path>.+)", self.url)
        if ssh_guess == None:
            m = re.match(r"(?P<schema>[a-zA-Z,+-0-9]+)://(?P<hostname>[^/]+)/(?P<path>.+)", self.url)
        else:
            m = ssh_guess

        if m.group('hostname') != "github.com":
            return None

        path = m.group('path')
        path = re.sub(r'(.*)\.git/*', r'\1', path)

        return "https://{}/{}".format(m.group('hostname'), path)

    def has_application_trees(self):
        return self.application_trees.exists()

    def unique_application_trees(self):
        return sorted(list(set(self.application_trees.values_list('tree_name', flat=True))))

    def update_boards(self):
        for tree in self.vcs_repo.head.get_file(self.boards_tree).trees:
            board, created = Board.objects.get_or_create(riot_name=tree.name)

            if not board.no_board:
                path = path_join(self.boards_tree, tree.name)
                board.path = path
                board.repo = self
                try:
                    board.cpu_repo = Repository.objects.get(is_default=True)
                except Repository.DoesNotExist:
                    pass
                board.save()

    def update_applications(self):
        for tree_name in self.unique_application_trees():
            for app in self.vcs_repo.head.get_file(tree_name).trees:
                abs_path = path_join(tree_name, app.name)
                makefile = path_join(abs_path, 'Makefile')
                try:
                    app_name, blacklist, whitelist = Application.get_name_and_lists_from_makefile(self, makefile)
                except Application.DoesNotExist:
                    continue
                except AssertionError:
                    continue
                appobj, created = Application.objects.get_or_create(name=app_name,
                                                                    path=abs_path)
                if created or not appobj.no_application:
                    app_tree, created = ApplicationTree.objects.get_or_create(
                        tree_name=tree_name, repo=self, application=appobj)
                    for board in Board.objects.all():
                        if board.riot_name in blacklist and board not in appobj.blacklisted_boards.all():
                            appobj.blacklisted_boards.add(board)
                        if board.riot_name in whitelist and board not in appobj.blacklisted_boards.all():
                            appobj.whitelisted_boards.add(board)

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
                                 null=False, db_index=True,
                                 verbose_name="RIOT name")
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
    prototype_jobs = models.ManyToManyField('ApplicationJob',
                                            related_name='board_prototype_for', 
                                            blank=True)
    no_board = models.BooleanField(default=False, blank=False, null=False,
                                   editable=False)

    objects = BoardManager()

    class Meta:
        ordering = ['riot_name']

    def __str__(self):
        return self.riot_name

    @models.permalink
    def get_absolute_url(self):
        return ('board-detail', (self.pk,))

class Application(models.Model):
    """
    A representarion of a RIOT application.
    """
    name = models.CharField(max_length=16, blank=False, null=False,
                            db_index=True)
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
    prototype_jobs = models.ManyToManyField('ApplicationJob', 
                                            related_name='app_prototype_for', 
                                            blank=True)

    objects = ApplicationManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('application-detail', (self.pk,))

    @staticmethod
    def get_name_and_lists_from_makefile(repository, makefile_path):
        try:
            makefile_blob = repository.vcs_repo.head.get_file(makefile_path)
        except KeyError:
            raise Application.DoesNotExist("Application's Makefile does not exist")
        if not isinstance(makefile_blob, vcs.Blob):
            raise Application.DoesNotExist("Application's Makefile is no file")
        makefile_content = makefile_blob.read()
        app_name = ''
        blacklist = []
        whitelist = []
        next_line_blacklist = False
        next_line_whitelist = False
        for line in makefile_content.splitlines():
            if next_line_blacklist:
                blacklist.extend(re.sub(r"\s*(.+)\s*\\?$", r'\1', line).split(' '))
                if not line.endswith('\\'):
                    next_line_blacklist = False
            if next_line_whitelist:
                whitelist.extend(re.sub(r"\s*(.+)\s*\\?$", r'\1', line).split(' '))
                if not line.endswith('\\'):
                    next_line_whitelist = False
            if re.match(r".*APPLICATION\s*[:?]?=\s*([^\s]+).*", line):
                app_name = re.sub(r".*APPLICATION\s*=\s*([^\s]+).*", r'\1', line)
            if re.match(r".*BOARD_BLACKLIST\s*[:?]?=\s*([^\\]+)\s*\\?$", line):
                blacklist.extend(re.sub(r".*BOARD_BLACKLIST\s*[:?]?=\s*([^\\]+)\s*\\?$", r'\1', line).split(' '))
                if line.endswith('\\'):
                    blacklist.pop(-1)
                    next_line_blacklist = True
            if re.match(r".*BOARD_INSUFFICIENT_RAM\s*[:?]?=\s*([^\\]+)\s*\\?$", line):
                blacklist.extend(re.sub(r".*BOARD_INSUFFICIENT_RAM\s*[:?]?=\s*([^\\]+)\s*\\?$", r'\1', line).split(' '))
                if line.endswith('\\'):
                    blacklist.pop(-1)
                    next_line_blacklist = True
            if re.match(r".*BOARD_WHITELIST\s*[:?]?=\s*([^\\]+)\s*\\?$", line):
                whitelist.extend(re.sub(r".*BOARD_WHITELIST\s*[:?]?=\s*([^\\]+)\s*\\?$", r'\1', line).split(' '))
                if line.endswith('\\'):
                    whitelist.pop(-1)
                    next_line_whitelist = True
        if app_name == '':
            raise AssertionError("Application name not in Makefile.")
        return app_name, blacklist, whitelist

    def update_from_makefile(self):
        if self.no_application:
            makefile_path = path_join(self.path, 'Makefile')
            app_name, blacklist, whitelist = Application.get_name_and_lists_from_makefile(self.repository, makefile_path)
            self.name = app_name
            for board in models.Board.objects.all():
                if board.riot_name in blacklist and board not in self.blacklisted_boards.all():
                    self.blacklisted_boards.add(board)
                if board.riot_name in whitelist and board not in self.blacklisted_boards.all():
                    self.whitelisted_boards.add(board)
            self.save()

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

class JobNamespace(models.Model):
    name = models.CharField(max_length=64, unique=True)
    repository = models.OneToOneField('Repository', related_name='job_namespace')

    def __str__(self):
        return self.name

class Job(models.Model):
    """
    A representation of a Jenkins job.
    """
    namespace = models.ForeignKey('JobNamespace', blank=True, null=True,
                                  default=0, related_name='jobs')
    name = models.CharField(max_length=64, unique=True, blank=False, null=False,
                            editable=False)
    upstream_job = models.ForeignKey('Job', related_name='downstream_jobs',
                                     null=True, blank=True, default=None,
                                     on_delete=models.SET_NULL)
    manual = models.BooleanField(default=False)
    always_update = models.BooleanField(default=False)

    objects = InheritanceManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('job-detail', (self.pk,))

    @property
    def path(self):
        """
        The path to the application.
        """
        return path_join(settings.JENKINS_JOBS_PATH, self.name)

    @property
    def xml(self):
        """
        XML representation of the application
        """
        if not hasattr(self, '_xml'):
            try:
                self._xml = jenkins.jobs.MultiJob(self.path)
            except ValueError:
                self._xml = jenkins.jobs.Job(self.path)

        return self._xml

    def is_application_job(self):
        return isinstance(self, ApplicationJob)

    def get_subclass(self):
        try:
            return self._default_manager.get_subclass(pk=self.pk)
        except ValueError:
            return self._default_manager.get(pk=self.pk)

    def update_from_jenkins_xml(self):
        if isinstance(self.xml, jenkins.jobs.MultiJob):
            for jobname in self.xml:
                if not self.downstream_jobs.filter(name=jobname).exists():
                    self.downstream_jobs.add(*Job.objects.filter(name=jobname))

        for multijob in Job.get_multijobs():
            if self.name in multijob.xml:
                self.upstream_job = multijob

        boards = Board.objects.all()
        apps = Application.objects.all()

        if any(board.riot_name in self.name for board in boards) or \
           any(app.name in self.name for app in apps):
            for board in [b for b in boards if b.riot_name in self.name]:
                for app in [a for a in apps if a.name in self.name]:
                    self.__class__ = ApplicationJob
                    self.board = board
                    self.application = app
                    self.namespace = board.repo.job_namespace

    @staticmethod
    def create_from_jenkins_xml():
        for job in listdir(settings.JENKINS_JOBS_PATH):
            if Job.objects.filter(name=job).exists():
                continue
            obj, created = Job.objects.get_or_create(name=job)

            if created:
                try:
                    obj.namespace = Repository.objects.get(is_default=True).job_namespace
                except Repository.DoesNotExist:
                    pass

            obj.update_from_jenkins_xml()

            obj.save()

            if created and obj.is_application_job():
                if (obj.application.name in settings.RIOT_DEFAULT_APPLICATIONS):
                    obj.app_prototype_for.add(*Application.objects.exclude(name=obj.application.name))
                if (obj.board.riot_name in settings.RIOT_DEFAULT_BOARDS):
                    obj.board_prototype_for.add(*Board.objects.exclude(riot_name=obj.board.riot_name))
                obj.save()


    @staticmethod
    def get_multijobs():
        return [j for j in Job.objects.all() if isinstance(j, jenkins.jobs.MultiJob)]

class ApplicationJob(Job):
    """
    A representation of a Jenkins job for a RIOT application
    """
    board = models.ForeignKey('Board', related_name='jobs', null=True,
                              blank=True)
    application = models.ForeignKey('application', related_name='jobs',
                                    null=True, blank=True)

    @property
    def xml(self):
        if not hasattr(self, '_xml') or isinstance(self._xml, jenkins.jobs.ApplicationJob):
            self._xml = jenkins.jobs.ApplicationJob(self.path, self.board.name,
                                                    self.application.name,
                                                    self.application.path)
        return super(ApplicationManager, self).xml


class ApplicationJobDeletionProxy(models.Model):
    """
    A representation of a Jenkins job for removal of RIOT application property
    """
    job_ptr_id = models.PositiveIntegerField(primary_key=True)
    board_id = models.PositiveIntegerField()
    application_id = models.PositiveIntegerField()

    class Meta:
        app_label = ApplicationJob._meta.app_label
        db_table = ApplicationJob._meta.db_table
        managed = False

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
            instance.update_boards()

    if created:
        namespace_name = re.sub(r'^.*/([^/]+(.git)?)$', r'\1', instance.url).replace('_', '-').replace('.git', '')
        input_name = namespace_name[0].upper() + namespace_name[1:]
        c = 1
        while JobNamespace.objects.filter(name=input_name).exists():
            input_name = namespace_name + str(c)
            c += 1

        JobNamespace.objects.create(name=input_name, repository=instance)

def application_job_post_save(sender, instance, created, *args, **kwargs):
    if instance.board == None and instance.application == None:
        ApplicationJobDeletionProxy.objects.filter(pk=instance.pk).delete()

pre_save.connect(repository_pre_save, sender=Repository)
post_save.connect(repository_post_save, sender=Repository)
post_save.connect(application_job_post_save, sender=ApplicationJob)
