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
        self.claimed_commits = False
        for repo in self.repositories:
            commits.extend(repo.commits)
            if repo.claimed_commits:
                self.claimed_commits = True
        self.analysis = types.SimpleNamespace(all=None, past_year=None)
        self._analyze(person, commits)

    def _analyze(self, name, commits):
        author_commits = self._commits_by_author(commits)
        my_commits = self._coalesce_author(name, author_commits)
        sorted_commits = self._sort_by_date(my_commits)
        first_commit = sorted_commits[0] if my_commits else None
        last_commit = sorted_commits[-1] if my_commits else None
        self.analysis.all = self._create_stats(
                (first_commit.date, last_commit.date)
                    if last_commit is not None else None,
                (len(my_commits), len(commits)))

        now = datetime.datetime.now()
        year_ago = datetime.datetime(now.year - 1, now.month, now.day, now.hour,
                                     now.minute, now.second, now.microsecond)
        if last_commit is not None and last_commit.date < year_ago:
            self.analysis.past_year = None
        else:
            past_year = list(filter(lambda commit: commit.date > year_ago, commits))
            past_year_author_commits = self._commits_by_author(past_year)
            past_year_my_commits = past_year_author_commits.get(name, [])
            self.analysis.past_year = self._create_stats(
                    None,
                    (len(past_year_my_commits), len(past_year)))

    def _create_stats(self, date_range, commit_count):
        if date_range is not None:
            dates = types.SimpleNamespace(first=date_range[0], last=date_range[1])
        else:
            dates = None
        counts = types.SimpleNamespace(me=commit_count[0],
                                       everyone=commit_count[1])
        return types.SimpleNamespace(date_range=dates,
                                     commit_count=counts)

    def _commits_by_author(self, commits):
        """Bucket commits by author."""
        author_commits = {}
        for commit in commits:
            author_commits.setdefault(commit.author, []).append(commit)
        return author_commits

    def _coalesce_author(self, name, commits_by_author):
        """Find all the commits by an author using some name coelescing."""
        name_variants = {name}
        name_parts = name.split()
        name_variants.add(''.join(name_parts))
        name_variants.add(name_parts[0][0] + ''.join(name_parts[1:]))
        for variant in list(name_variants):
            name_variants.add(variant.lower())
        found_names = set()
        for author_name in commits_by_author:
            if any(variant in author_name for variant in name_variants):
                found_names.add(author_name)
        self.found_names = found_names
        for found_name in found_names:
            if found_name == name:
                continue
            found_commits = commits_by_author[found_name]
            commits_by_author.setdefault(name, []).extend(found_commits)
            del commits_by_author[found_name]
        return commits_by_author.get(name, [])

    def _sort_by_date(self, commits):
        """Return an iterator consisting of the commits in ascending date order."""
        return sorted(commits, key=operator.attrgetter('date'))
