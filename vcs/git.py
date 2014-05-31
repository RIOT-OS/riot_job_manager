"""Provides an abstraction layer to pygit2"""
from os.path import join as path_join, isdir
import pygit2
from . import Repository, Commit, Tree, Blob

class GitRepository(Repository):
    """A basic Git repository"""
    def __init__(self, directory, url=None, default_branch='master'):
        try:
            self.directory = pygit2.discover_repository(path_join(directory))
            self._repo = pygit2.Repository(directory)
        except KeyError as e:
            if url != None:
                self._repo = None
                self.url = url
            else:
                raise ValueError("Repository not found at {}".format(directory))
        if self._repo != None and not hasattr(self, 'url'):
            remote = [r for r in self._repo.remotes if r.name == 'origin']
            if len(remote) < 1:
                remote = self._repo.remotes[0]
            else:
                remote = remote[0]
            self.url = remote.url
            self.directory = self._repo.workdir
        self.default_branch = default_branch
        super(GitRepository, self).__init__(directory)

    def __str__(self):
        return str(self.url)

    @staticmethod
    def is_repository(directory):
        """Checks if the repository is a VCS repository"""
        try:
            pygit2.discover_repository(path_join(directory))
            return True
        except KeyError:
            return False


    def clone(self):
        """Clones the repository to local machine"""
        self._repo = pygit2.clone_repository(
            self.url, self.directory, bare=True, remote_name='origin',
            checkout_branch=self.default_branch)
        self.directory = self._repo.workdir

    def fetch(self, remote_name):
        """Fetches data from remote"""
        if self._repo == None or len(self._repo.remotes) == 0:
            raise ValueError("Repository has no remotes defined")

        remote = [r for r in self._repo.remotes if r.name == remote_name]

        if len(remote) < 1:
            raise KeyError("Remote {} not found in local repository",
                           remote_name)

        remote[0].fetch()

    def pull(self, branch=None):
        """Fetches data from remote and merges branch into branch"""
        if self._repo == None:
            raise ValueError("Repository not cloned")

        if branch == None:
            branch = self.default_branch

        ours = self._repo.lookup_branch(branch)

        if ours == None:
            raise KeyError(
                "Branch {} not found in local repository".format(
                    ours.branch_name))

        theirs = ours.upstream

        if theirs == None:
            raise AssertionError(
                "Branch {} has no upstream".format(ours.branch_name))

        self.fetch(theirs.remote_name)
        self._repo.head = theirs.name

    @property
    def head(self):
        return GitCommit(self._repo, self._repo.head.get_object())

class GitCommit(Commit):
    """A basic Git commit"""
    def __init__(self, repo, commit_object):
        self._repo = repo
        self._commit = commit_object
        super(GitCommit, self).__init__(commit_object.oid.hex)

    def get_file(self, path_name):
        if path_name in ['', '.']:
            return self.base_tree
        try:
            entry = self._commit.tree[path_name]
        except KeyError:
            raise ValueError("{} does not exist in commit {}".format(path_name, self))
        obj = self._repo.get(entry.oid)
        if obj.type == pygit2.GIT_OBJ_TREE:
            return GitTree(self._repo, obj, entry.name)
        if obj.type == pygit2.GIT_OBJ_BLOB:
            return GitBlob(self._repo, obj, entry.name)
        else:
            raise ValueError("Unexpected object in Tree")

    @property
    def base_tree(self):
        return GitTree(self._repo, self._commit.tree, '.')

class GitTree(Tree):
    """A basic Git tree"""
    def __init__(self, repo, tree_object, name):
        self._repo = repo
        self._tree = tree_object
        super(GitTree, self).__init__(tree_object.oid.hex, name)

    def get_file(self, path_name):
        if path_name in ['', '.']:
            return self
        try:
            entry = self._tree[path_name]
        except KeyError:
            raise ValueError("{} does not exist in commit {}".format(path_name, self))
        obj = self._repo.get(entry.oid)
        if obj.type == pygit2.GIT_OBJ_TREE:
            return GitTree(self._repo, obj, entry.name)
        if obj.type == pygit2.GIT_OBJ_BLOB:
            return GitBlob(self._repo, obj, entry.name)
        else:
            raise ValueError("Unexpected object in Tree")

    @property
    def files(self):
        for entry in self._tree:
            obj = self._repo.get(entry.oid)
            if obj.type == pygit2.GIT_OBJ_TREE:
                yield GitTree(self._repo, obj, entry.name)
            if obj.type == pygit2.GIT_OBJ_BLOB:
                yield GitBlob(self._repo, obj, entry.name)

    @property
    def trees(self):
        for entry in self._tree:
            obj = self._repo.get(entry.oid)
            if obj.type == pygit2.GIT_OBJ_TREE:
                yield GitTree(self._repo, obj, entry.name)

    @property
    def blobs(self):
        for entry in self._tree:
            obj = self._repo.get(entry.oid)
            if obj.type == pygit2.GIT_OBJ_BLOB:
                yield GitBlob(self._repo, obj, entry.name)

    def _walk(self, base_name='.'):
        """Helper method for walk()"""
        yield base_name, list(self.trees) or None, list(self.blobs) or None
        for tree in self.trees:
            for entry in tree._walk(path_join(base_name, tree.name)):
                yield entry

    def walk(self):
        for entry in self._walk():
            yield entry

class GitBlob(Blob):
    """A basic Git blob"""
    def __init__(self, repo, blob_object, name):
        self._repo = repo
        self._blob = blob_object
        super(GitBlob, self).__init__(blob_object.oid.hex, name)

    def read(self):
        return self._blob.data

    def is_binary(self):
        return self._blob.is_binary
