import datetime
import operator
import types


class Statistics:

    def __init__(self, name, commits):
        author_commits = self._commits_by_author(commits)
        my_commits = author_commits[name]
        author_order = list(self._authors_by_commit_count(author_commits))
        sorted_commits = self._sort_by_date(commits)
        self.all = self._create_stats(
                (sorted_commits[0].date, sorted_commits[-1].date),
                (len(my_commits), len(commits)),
                (author_order.index(name)+1, len(author_commits)))

        now = datetime.datetime.now()
        year_ago = datetime.datetime(now.year - 1, now.month, now.day, now.hour,
                                     now.minute, now.second, now.microsecond)
        past_year = list(filter(lambda commit: commit.date > year_ago, commits))
        past_year_author_commits = self._commits_by_author(past_year)
        past_year_my_commits = author_commits[name]
        author_order = list(self._authors_by_commit_count(past_year_author_commits))
        self.past_year = self._create_stats(
                None,
                (len(past_year_my_commits), len(past_year)),
                (author_order.index(name)+1, len(author_commits)))

    def _create_stats(self, date_range, commit_count, ranking):
        return types.SimpleNamespace(date_range=date_range,
                                     commit_count=commit_count, ranking=ranking)

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
