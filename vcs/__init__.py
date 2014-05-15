"""Provides abstract layer to version control systems"""
from os.path import isdir, exists, join as path_join

from ._vcs import Repository, Commit, Tree, Blob
import vcs.git as git

__REPO_IMPL = {
    'git': git.GitRepository,
}

def get_repository(directory, vcs='git', url=None):
    """Get the implementation of a Repository based on its actual VCS"""
    if exists(directory) and not isdir(directory):
        raise ValueError("{} is not a directory".format(directory))
    if url == None:
        return __REPO_IMPL[vcs](directory)
    else:
        return __REPO_IMPL[vcs](directory, url)
