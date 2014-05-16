"""Parses and creates Jenkins jobs"""
import re
from os import makedirs
from os.path import basename, dirname, exists, join as path_join
import lxml.etree

class Job(object):
    """
    Abstraction layer for Jenkins jobs.
    """
    def __init__(self, path):
        self.name = basename(path)
        self.filename = path_join(path, 'config.xml')
        if exists(self.filename):
            self.fileobj = open(self.filename)
            self.filetree = lxml.etree.parse(self.fileobj)
        else:
            self.fileobj = None
            self.filetree = None

class ApplicationJob(Job):
    """
    Abstraction layer for the Jenkins application job
    """
    def __init__(self, path, board, application):
        super(ApplicationJob, self).__init__(path)
        self.board = board
        self.application = application
        re_match = re.match(r'(?P<namespace>.+)-{}-{}(-(?P<cc>.+))?'.format(
            self.board, self.application), self.name)
        if re_match:
            self.namespace = re_match.group('namespace')
            self.compiler = re_match.group('cc')
        else:
            raise ValueError("Name of application job must have the format <namespace>-<board>-<application>[-<cc>]")

    def create_from_prototype(self, prototype_job):
        """Creates a Job from a prototype"""
        prototype_board = str(prototype_job.board)
        prototype_application_name = str(prototype_job.application.name)
        prototype_application_path = str(prototype_job.application.path)
        if hasattr(prototype_job, 'compiler'):
            prototype_compiler = prototype_job.compiler
        else:
            prototype_compiler = None
        prototype_fileobj = open(prototype_job.filename)

        if (not prototype_compiler and self.compiler) or \
           (prototype_compiler and not self.compiler):
            raise ValueError("Both jobs do need a compiler or do not have any.")

        if not self.fileobj:
            makedirs(dirname(self.filename))

        self.fileobj = open(self.filename, 'w')

        for proto_line in prototype_fileobj.readlines():
            line = re.sub(prototype_board, self.board, proto_line)
            line = re.sub(prototype_application_name, self.application.name,
                          line)
            line = re.sub(prototype_application_path, self.application.path,
                          line)
            if prototype_compiler and self.compiler:
                line = re.sub(prototype_compiler, self.compiler,
                              line)
            self.fileobj.write()

        self.fileobj.close()
        self.fileobj = open(self.filename)

