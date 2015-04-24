import collections
import datetime
import operator
import pathlib
import sys

from . import vcs, analysis

name = sys.argv[1]
path = pathlib.Path(sys.argv[2]).resolve()
repo = vcs.Hg(path)
commits = repo.log()

results = analysis.Statistics(name, commits)

print(path)
print('  Lifetime')
count_percentage = (results.all.commit_count[0] / results.all.commit_count[1] *
                    100)
commit_stats = '{:,} out of {:,} ({:.2f}%)'.format(results.all.commit_count[0],
                                                   results.all.commit_count[1],
                                                   count_percentage)
print('    Commits:', commit_stats)
print('    Ranking: {} out of {}'.format(results.all.ranking[0],
                                            results.all.ranking[1]))

print('  Last 12 months')
count_percentage = (results.past_year.commit_count[0] /
                    results.past_year.commit_count[1] * 100)
commit_stats = '{:,} out of {:,} ({:.2f}%)'.format(
        results.past_year.commit_count[0],
        results.past_year.commit_count[1],
        count_percentage)
print('    Commits:', commit_stats)
print('    Ranking: {} out of {}'.format(results.past_year.ranking[0],
                                            results.past_year.ranking[1]))

print('  First commit:', results.all.date_range[0].strftime('%Y-%m-%d'))
print('  Latest commit:', results.all.date_range[1].strftime('%Y-%m-%d'))
