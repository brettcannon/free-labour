import abc
import enum
import hashlib
import pathlib
import types

import hglib


def create_log_entry(id_, date, author):
    return types.SimpleNamespace(id=id_, date=date, author=author)


@enum.unique
class Supported(enum.Enum):
    hg = 1


class Repo(metaclass=abc.ABCMeta):

    """ABC representing necessary operations on a VCS."""

    supported = {}

    type = None

    @classmethod
    def register(cls, subclass):
        cls.supported[subclass.type] = subclass

    @classmethod
    def get(cls, type_: str, remote: str, dest_parent: str):
        """Get a repo based on its type, remote URL, and eventual parent directory."""
        try:
            repo_enum = Supported[type_]
            repo_class = cls.supported[repo_enum]
        except KeyError:
            raise ValueError(repr(type_) + ' is an unsupported repository type')
        return repo_class(remote, pathlib.Path(dest_parent))

    def __init__(self, remote: str, parent_path: pathlib.Path):
        self.remote = remote
        hashed_remote = hashlib.sha1(remote.encode('utf-8')).hexdigest()
        self.directory = parent_path / hashed_remote

    def __enter__(self):
        if not self.directory.exists():
            self.clone()
        else:
            self.update()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abc.abstractmethod
    def clone(self):
        raise NotImplementedError

    @abc.abstractmethod
    def update(self):
        raise NotImplementedError

    @abc.abstractmethod
    def log(self, name):
        raise NotImplementedError

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError


@Repo.register
class Hg(Repo):

    """Implements Mercurial repository access."""

    type = Supported.hg

    def _author_name(self, commit):
        author = commit.author.decode('utf-8')
        return author.partition('<')[0].strip()

    def clone(self):
        self._client = hglib.clone(self.remote, str(self.directory))
        self._client.open()

    def update(self):
        self._client = hglib.open(str(self.directory))
        self._client.pull(update=True)

    def log(self):
        return [create_log_entry(entry.rev, entry.date, self._author_name(entry))
                for entry in self._client.log()]

    def close(self):
        self._client.close()
