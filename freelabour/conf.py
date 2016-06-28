from concurrent import futures
import operator
import os
from urllib import parse

import yaml

from . import project, repo


def read(file_path):
    with open(file_path) as file:
        return yaml.safe_load(file.read())


def repo_type(domain_mapping, url):
    domain = parse.urlparse(url).netloc
    for type, domains in domain_mapping.items():
        if domain in domains:
            return type
    raise ValueError('repo type of {!r} is unknown'.format(domain))


def _urls(repository):
    urls = repository.get('urls')
    if urls is None:
        urls = [repository['url']]
    yield from urls


def _repos(repository, repo_mapping):
    for url in _urls(repository):
        yield repo_mapping[url]


def process(data, dest_parent):
    future_projects = set()
    user_name = data['name']
    domain_mapping = data['VCS type by domain']
    with futures.ThreadPoolExecutor(os.cpu_count() or 1) as pool:
        # Clone/update all repos.
        future_repos = set()
        for repository in data['repositories']:
            for url in _urls(repository):
                type_ = repository.get('type')
                if type_ is None:
                    type_ = repo_type(domain_mapping, url)
                kwargs = {}
                if 'branch' in repository:
                    kwargs['branch'] = repository['branch']
                try:
                    f = pool.submit(repo.Repo.get, type_, url, dest_parent,
                                    **kwargs)
                    future_repos.add(f)
                    print(url +
                          (':' + kwargs['branch'] if 'branch' in kwargs else ''))
                except ValueError as exc:
                    print('{}: {}'.format(url, str(exc)))
                    continue
        repo_mapping = {future_repo.result().remote: future_repo.result()
                        for future_repo in future_repos}
        # Handle claimed commits.
        for repository in data['repositories']:
            claimed_commits = repository.get('commits', [])
            for claimed_commit in claimed_commits:
                for r in _repos(repository, repo_mapping):
                    try:
                        r.claim_commit(user_name, claimed_commit)
                    except ValueError:
                        pass
        # Create projects.
        for repository in data['repositories']:
            f = pool.submit(project.Project, data['name'],
                            repository.get('name'),
                            *_repos(repository, repo_mapping))
            future_projects.add(f)
        return frozenset(f.result() for f in future_projects)
