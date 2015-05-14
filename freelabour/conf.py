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


def process(data, dest_parent):
    future_projects = set()
    pool = futures.ThreadPoolExecutor(os.cpu_count() or 1)
    user_name = data['name']
    domain_mapping = data['VCS type by domain']
    # TODO: make concurrent; probably name of project with repo and then
    # groupby after fetching them all. Can keep creating projects concurrently.
    for repository in data['repositories']:
        repos = []
        urls = repository.get('urls')
        if urls is None:
            urls = [repository['url']]
        for url in urls:
            type_ = repository.get('type')
            if type_ is None:
                type_ = repo_type(domain_mapping, url)
            try:
                repos.append(repo.Repo.get(type_, url, dest_parent))
                print(url)
            except ValueError as exc:
                print('{}: {}'.format(url, str(exc)))
                continue
        if not repos:
            continue
        claimed_commits = repository.get('commits', [])
        for claimed_commit in claimed_commits:
            for r in repos:
                try:
                    r.claim_commit(user_name, claimed_commit)
                except ValueError:
                    pass
        f = pool.submit(project.Project, data['name'],
                        repository.get('name'), *repos)
        future_projects.add(f)
    return frozenset(f.result() for f in future_projects)
