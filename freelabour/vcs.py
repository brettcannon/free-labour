import abc
import types

import hglib


def create_log_entry(id_, date, author):
    return types.SimpleNamespace(id=id_, date=date, author=author)


class BaseVCS(metaclass=abc.ABCMeta):

    """ABC representing necessary operations on a VCS."""

    @abc.abstractmethod
    def __init__(self, path):
        raise ValueError('not implemented')

    @abc.abstractmethod
    def log(self, name):
        raise RuntimeError('not implemented')


class Hg(BaseVCS):

    def __init__(self, path):
        self.client = hglib.open(str(path.resolve()))

    def _author_name(self, commit):
        author = commit.author.decode('utf-8')
        return author.partition('<')[0].strip()

    def log(self):
        return [create_log_entry(entry.rev, entry.date, self._author_name(entry))
                for entry in self.client.log()]
