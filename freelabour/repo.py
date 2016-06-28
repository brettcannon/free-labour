import abc
import datetime
import enum
import functools
import hashlib
import pathlib
import sys
import types

import hglib
import git


def create_log_entry(id_, date, author):
    return types.SimpleNamespace(id=id_, date=date, author=author)


@enum.unique
class Supported(enum.Enum):
    hg = 1
    git = 2


class Repo(metaclass=abc.ABCMeta):

    """ABC representing necessary operations on a VCS."""

    supported = {}

    type = None

    @classmethod
    def register(cls, subclass):
        cls.supported[subclass.type] = subclass

    @classmethod
    def get(cls, type_: str, remote: str, dest_parent: str, *, branch=None):
        """Get a repo based on its type, remote URL, and eventual parent directory."""
        try:
            repo_enum = Supported[type_]
            repo_class = cls.supported[repo_enum]
        except KeyError:
            raise ValueError(repr(type_) + ' is an unsupported repository type')
        return repo_class(remote, pathlib.Path(dest_parent), branch=branch)

    def __init__(self, remote: str, parent_path: pathlib.Path, *, branch=None):
        self.remote = remote
        self.branch = branch
        hashed_remote = hashlib.sha1(remote.encode('utf-8')).hexdigest()
        self.directory = parent_path / hashed_remote
        self.claimed_commits = []
        with self:
            self.commits = self.log()

    def __enter__(self):
        if not self.directory.exists():
            try:
                self.clone()
            except Exception:
                print('Exception while cloning {!r}'.format(self.remote),
                      file=sys.stderr)
                raise
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

    def claim_commit(self, name, id_):
        for commit in self.commits:
            if id_ == commit.id:
                new_id = id_ + '-author'
                cloned_commit = create_log_entry(new_id, commit.date, name)
                self.commits.append(cloned_commit)
                self.claimed_commits.append(cloned_commit)
                return
        else:
            raise ValueError('commit {!r} not found'.format(id_))


@Repo.register
class Hg(Repo):

    """Implements Mercurial repository access."""

    type = Supported.hg

    def _author_name(self, commit):
        author = commit.author.decode('utf-8')
        return author.partition('<')[0].strip()

    def clone(self):
        kwargs = {}
        if self.branch:
            kwargs['branch'] = self.branch
        self._client = hglib.clone(self.remote, str(self.directory), **kwargs)
        self._client.open()

    def update(self):
        self._client = hglib.open(str(self.directory))
        self._client.pull(update=True)

    def log(self):
        commits = self._client.log()
        return [create_log_entry(entry.node.decode('utf-8'), entry.date,
                                 self._author_name(entry))
                for entry in commits]

    def close(self):
        self._client.close()


@Repo.register
class Git(Repo):

    """Implements Git repository access."""

    type = Supported.git

    def clone(self):
        kwargs = {}
        if self.branch:
            kwargs['branch'] = self.branch
        self._repo = git.Repo.clone_from(self.remote, str(self.directory),
                                         **kwargs)

    def update(self):
        self._repo = git.Repo(str(self.directory))
        self._repo.remotes.origin.pull()

    def log(self):
        # From http://blog.lost-theory.org/post/how-to-parse-git-log-output/ .
        log_format = '%x1f'.join(['%H', '%at', '%an']) + '%x1e'
        raw_log = self._repo.git.log(format=log_format, date='short')
        commits = []
        for raw_commit in raw_log.strip('\n\x1e').split("\x1e"):
            commit_bits = raw_commit.strip().split("\x1f")
            date = datetime.datetime.fromtimestamp(int(commit_bits[1]))
            commits.append(create_log_entry(commit_bits[0], date, commit_bits[2]))
        return commits

    def close(self):
        pass
