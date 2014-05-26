"""Parses and creates Jenkins jobs"""
import copy
import re
from os import makedirs
from os.path import basename, dirname, exists, join as path_join
from lxml import etree

class Job(object):
    """
    Abstraction layer for Jenkins jobs.
    """
    def __init__(self, path):
        path = re.sub('/*$', '', path)
        self.name = basename(path)
        self.filename = path_join(path, 'config.xml')
        if exists(self.filename):
            self.fileobj = open(self.filename)
            self.filetree = etree.parse(self.fileobj)
        else:
            self.fileobj = None
            self.filetree = None

    def __getitem__(self, key):
        raise KeyError(key)

class ApplicationJob(Job):
    """
    Abstraction layer for the Jenkins application job
    """
    def __init__(self, path, board, application_name, application_path):
        super(ApplicationJob, self).__init__(path)
        self.board = board
        self.application_name = application_name
        self.application_path = application_path
        re_match = re.match(r'(?P<repository_tag>.+)-(?P<board>{})-(?P<application>{})(-(?P<cc>.+))?'.format(
            self.board, self.application_name), self.name)
        if re_match:
            self.repository_tag = re_match.group('repository_tag')
            self.compiler = re_match.group('cc')
        else:
            raise ValueError("Name of application job must have the format <repository_tag>-<board>-<application>[-<cc>]")

    def create_from_prototype(self, prototype_job):
        """Creates a Job from a prototype"""
        prototype_board = str(prototype_job.board)
        prototype_application_name = str(prototype_job.application_name)
        prototype_application_path = str(prototype_job.application_path)
        if hasattr(prototype_job, 'compiler'):
            prototype_compiler = prototype_job.compiler
        else:
            prototype_compiler = None
        prototype_fileobj = prototype_job.fileobj

        if (not prototype_compiler and self.compiler) or \
           (prototype_compiler and not self.compiler):
            raise ValueError("Both jobs do need a compiler or do not have any.")

        if not self.fileobj:
            makedirs(dirname(self.filename))

        self.fileobj = open(self.filename, 'w')

        for proto_line in prototype_fileobj.readlines():
            line = re.sub(prototype_board, self.board, proto_line)
            line = re.sub(prototype_application_name, self.application_name,
                          line)
            line = re.sub(prototype_application_path, self.application_path,
                          line)
            if prototype_compiler and self.compiler:
                line = re.sub(prototype_compiler, self.compiler,
                              line)
            self.fileobj.write(line)

        self.fileobj.close()
        self.fileobj = open(self.filename)

class MultiJob(Job):
    def __init__(self, path):
        super(MultiJob, self).__init__(path)
        if (self.filetree == None):
            raise ValueError("{} does not exist".format(path))
        if (self.filetree.getroot().tag != "com.tikal.jenkins.plugins.multijob.MultiJobProject"):
            raise ValueError("{} is not a MultiJob".format(path))

    def __getitem__(self, job_name):
        if self.filetree:
            try:
                return self.filetree.xpath('//jobName[text()=$text]', text=job_name)[0].getparent()
            except IndexError:
                raise KeyError(job_name)
        return super(MultiJob, self).__getitem__(job_name)

    def update_job_by_prototype(self, job, prototype_job):
        entry = self[prototype_job.name]
        try:
            new_entry = self[job]
            parent = new_entry.getparent()
            parent.remove(new_entry)
        except KeyError:
            new_entry = copy.deepcopy(entry)
            parent = new_entry.getparent()

        new_entry.find('jobName').text = job.name
        # look if phase is the right one.
        unique_list = {}
        unique_list[job.name] = new_entry
        for e in parent:
            job_name = e.find('jobName').text
            if job_name not in unique_list:
                unique_list[job.name] = e

        parent[:] = sorted(unique_list.values(), key=lambda x: x.find('jobName').text)
        self.filetree.write(self.fileobj, pretty_print=True)
