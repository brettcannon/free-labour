import datetime
import operator
import pathlib
import types
from urllib import parse

class Project:

    """Represent an overall project.

    Attributes:
    - name
    - repositories
    - analysis
      - all
        - date_range
          - first
          - last
        - counts
          - me
          - everyone
        - rank
          - me
          - everyone
      - past_year (attributes same as 'all')
    """

    def __init__(self, person, name, *repos):
        if name is None:
            if len(repos) > 1:
                msg = 'project name not specified but more than one repository'
                raise ValueError(msg)
            name = pathlib.Path(parse.urlparse(repos[0].remote).path).name
        self.name = name
        self.repositories = repos
        commits = []
        for repo in self.repositories:
            with repo:
                commits.extend(repo.log())
        self.analysis = types.SimpleNamespace(all=None, past_year=None)
        self._analyze(person, commits)

    def _analyze(self, name, commits):
        author_commits = self._commits_by_author(commits)
        try:
            my_commits = author_commits[name]
        except KeyError:
            my_commits = []
        author_order = list(self._authors_by_commit_count(author_commits))
        sorted_commits = self._sort_by_date(my_commits)
        ranking = 0
        try:
            ranking = author_order.index(name) + 1
        except ValueError:
            pass
        first_commit = sorted_commits[0] if my_commits else None
        last_commit = sorted_commits[-1] if my_commits else None
        self.analysis.all = self._create_stats(
                (first_commit.date, last_commit.date)
                    if last_commit is not None else None,
                (len(my_commits), len(commits)),
                (ranking, len(author_order)))

        now = datetime.datetime.now()
        year_ago = datetime.datetime(now.year - 1, now.month, now.day, now.hour,
                                     now.minute, now.second, now.microsecond)
        # XXX if no author commits since a year ago, skip everything below.
        past_year = list(filter(lambda commit: commit.date > year_ago, commits))
        past_year_author_commits = self._commits_by_author(past_year)
        try:
            past_year_my_commits = past_year_author_commits[name]
        except KeyError:
            past_year_my_commits = []
        author_order = list(self._authors_by_commit_count(past_year_author_commits))
        ranking = 0
        try:
            ranking = author_order.index(name) + 1
        except ValueError:
            pass
        self.analysis.past_year = self._create_stats(
                None,
                (len(past_year_my_commits), len(past_year)),
                (ranking, len(author_order)))

    def _create_stats(self, date_range, commit_count, ranking):
        if date_range is not None:
            dates = types.SimpleNamespace(first=date_range[0], last=date_range[1])
        else:
            dates = None
        counts = types.SimpleNamespace(me=commit_count[0],
                                       everyone=commit_count[1])
        rank = types.SimpleNamespace(me=ranking[0], everyone=ranking[1])
        return types.SimpleNamespace(date_range=dates,
                                     commit_count=counts, ranking=rank)

    def _commits_by_author(self, commits):
        """Bucket commits by author."""
        author_commits = {}
        for commit in commits:
            author_commits.setdefault(commit.author, []).append(commit)
        return author_commits

    def _authors_by_commit_count(self, author_commits):
        """Create an iterator of authors sorted by commit count (descending)."""
        return sorted(author_commits.keys(),
                      key=lambda name: len(author_commits[name]), reverse=True)

    def _sort_by_date(self, commits):
        """Return an iterator consisting of the commits in ascending date order."""
        return sorted(commits, key=operator.attrgetter('date'))
