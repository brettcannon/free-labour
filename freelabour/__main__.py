import collections
import datetime
import operator
import pathlib
import sys

from . import vcs, analysis


def main(name, repo_path):
    path = pathlib.Path(repo_path).resolve()
    repo = vcs.Hg(path)
    commits = repo.log()

    results = analysis.Statistics(name, commits)

    print(path)
    print('  Lifetime')
    commit_stats = '{:,} out of {:,} ({})'.format(
            results.all.commit_count.me,
            results.all.commit_count.everyone,
            results.percentage_str(results.all.commit_count))
    print('    Commits:', commit_stats)
    print('    Ranking: {} out of {} (top {})'.format(
            results.all.ranking.me,
            results.all.ranking.everyone,
            results.percentage_str(results.all.ranking)))

    print('  Last 12 months')
    commit_stats = '{:,} out of {:,} ({})'.format(
            results.past_year.commit_count.me,
            results.past_year.commit_count.everyone,
            results.percentage_str(results.past_year.commit_count))
    print('    Commits:', commit_stats)
    print('    Ranking: {} out of {} (top {})'.format(
            results.past_year.ranking.me,
            results.past_year.ranking.everyone,
            results.percentage_str(results.past_year.ranking)))

    print('  First commit:', results.all.date_range.first.strftime('%Y-%m-%d'))
    print('  Latest commit:', results.all.date_range.last.strftime('%Y-%m-%d'))


if __name__ == '__main__':
    main(sys.argv[0], sys.argv[1])
