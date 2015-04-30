import pathlib
import sys

from . import conf


def percentage_str(stat):
    try:
        percent = stat.me / stat.everyone * 100
    except ZeroDivisionError:
        percent = 0.0
    return '{:.2f}%'.format(percent)


def stats(project):
    print(project.name)
    print('  Lifetime')
    commit_stats = '{:,} out of {:,} ({})'.format(
            project.analysis.all.commit_count.me,
            project.analysis.all.commit_count.everyone,
            percentage_str(project.analysis.all.commit_count))
    print('    Commits:', commit_stats)
    print('    Ranking: {} out of {}'.format(
            project.analysis.all.ranking.me,
            project.analysis.all.ranking.everyone))

    print('  Last 12 months')
    commit_stats = '{:,} out of {:,} ({})'.format(
            project.analysis.past_year.commit_count.me,
            project.analysis.past_year.commit_count.everyone,
            percentage_str(project.analysis.past_year.commit_count))
    print('    Commits:', commit_stats)
    print('    Ranking: {} out of {}'.format(
            project.analysis.past_year.ranking.me,
            project.analysis.past_year.ranking.everyone))

    if project.analysis.all.date_range is not None:
        first_commit = project.analysis.all.date_range.first.strftime('%Y-%m-%d')
        print('  First commit:', first_commit)
        last_commit = project.analysis.all.date_range.last.strftime('%Y-%m-%d')
        print('  Latest commit:', last_commit)
    print()


def main(conf_path):
    data = conf.read(conf_path)
    projects = conf.process(data, pathlib.Path(conf_path).parent / 'repos')
    print()
    for project in projects:
        stats(project)
    pass


if __name__ == '__main__':
    main(sys.argv[1])
