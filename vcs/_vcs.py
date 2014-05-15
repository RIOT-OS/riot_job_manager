"""Provides abstract layer to version control systems"""

class Repository(object):
    """Abstract VCS repository"""
    def __init__(self, directory):
        self.directory = directory
        if not hasattr(self, 'url'):
            self.url = None

        if type(self).is_repository(directory):
            self.pull()
        else:
            self.clone()

    def __str__(self):
        return str(self.directory)

    def __repr__(self):
        t = type(self)
        return "<{}.{}: {}>".format(t.__module__, t.__name__, str(self))

    @staticmethod
    def is_repository(directory):
        """Checks if the repository is a VCS repository"""
        raise NotImplementedError

    def clone(self):
        """Clones the repository to local machine"""
        raise NotImplementedError

    def pull(self):
        """Updates repository on local machine"""
        raise NotImplementedError

    @property
    def head(self):
        """Returns the commit the repository is currently on"""
        raise NotImplementedError

class Commit(object):
    """Abstract VCS commit/patch"""
    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return str(self.identifier)

    def __repr__(self):
        t = type(self)
        return "<{}.{}: {}>".format(t.__module__, t.__name__, str(self))

    def get_file(self, path_name):
        """Get a either Tree or Blob object in the commit by path name."""
        raise NotImplementedError

    @property
    def base_tree(self):
        """
        Get the base Tree object in the commit (aka self.get_file('.'))
        """
        return self.get_file('.')

class Tree(object):
    """Abstract VCS tree/repository"""
    def __init__(self, identifier, name):
        self.identifier = identifier
        self.name = name

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        t = type(self)
        return "<{}.{}: {}>".format(t.__module__, t.__name__, str(self))

    def get_file(self, path_name):
        """Get a either Tree or Blob object in the tree by path name."""
        raise NotImplementedError

    @property
    def files(self):
        """Lists all Tree and Blob objects in the tree."""
        raise NotImplementedError

    @property
    def trees(self):
        """Lists all Tree objects in the tree."""
        raise NotImplementedError

    @property
    def blobs(self):
        """Lists all Blob objects in the tree."""
        raise NotImplementedError

    def walk(self):
        """
        Generate the objects in the tree by walking the tree either 
        top-down. (see pythons os.walk())
        """

class Blob(object):
    """Abstract VCS blob/file"""
    def __init__(self, identifier, name):
        self.identifier = identifier
        self.name = name

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        t = type(self)
        return "<{}.{}: {}>".format(t.__module__, t.__name__, str(self))

    def read(self):
        """Reads data of Blob object into string"""
        raise NotImplementedError

    def is_binary(self):
        """Checks if file is binary or a text file"""
        raise NotImplementedError
