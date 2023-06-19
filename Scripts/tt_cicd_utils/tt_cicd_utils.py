#!/usr/bin/env python3

from enum import Enum
import requests
import json
import re
import subprocess
import sys

__all__ = ['HTTPBearerAuth', 'PullRequestState', 'SemanticVersion', 'add_labels_to_pull_request', 'get_latest_version_tag', 'get_last_commit_sha', 'push_tag', 'fetch_latest_pull_request']

github_headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

class HTTPBearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer ' + self.token
        return r

class PullRequestState(Enum):
    OPEN = 'open'
    CLOSED = 'closed'
    ALL = 'all'
    def __str__(self):
        return self.value

class SemanticVersion:
    def __init__(self, version: str):
        regex = re.compile(r'v(\d+)\.(\d+)\.(\d+)')
        match = regex.fullmatch(version)
        if match is None:
            raise Exception(f"Unable to parse version: {version}")
        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = int(match.group(3))

    def __str__(self):
        return f"v{self.major}.{self.minor}.{self.patch}"

def fetch_pull_requests(repo: str, pull_request_state: PullRequestState, auth: requests.auth.AuthBase) -> [dict]:
    url = f"https://api.github.com/repos/{repo}/pulls"
    params = { 'state': pull_request_state.value }
    response = requests.get(url, params = params, headers = github_headers, auth = auth)
    response.raise_for_status()
    pull_requests = response.json()
    return pull_requests

def filter(pull_requests: [dict], base_ref_pattern: str = None, head_ref_pattern: str = None) -> [dict]:
    base_ref_regex = re.compile(base_ref_pattern) if base_ref_pattern else None
    head_ref_regex = re.compile(head_ref_pattern) if head_ref_pattern else None
    pull_requests = [pull_request for pull_request in pull_requests if (base_ref_regex is None or base_ref_regex.fullmatch(pull_request['base']['ref'])) and (head_ref_regex is None or head_ref_regex.fullmatch(pull_request['head']['ref']))]
    return pull_requests

def find_latest_pull_request(pull_requests: [dict]) -> dict:
    latest_pull_request = None
    for pull_request in pull_requests:
        if 'number' in pull_request and (latest_pull_request is None or pull_request['number'] > latest_pull_request['number']):
            latest_pull_request = pull_request
    return latest_pull_request

def add_labels_to_pull_request(repo: str, pull_request_number: int, labels: [], auth: requests.auth.AuthBase):
    url = f"https://api.github.com/repos/{repo}/issues/{pull_request_number}/labels"
    payload = { "labels": labels }
    response = requests.post(url, headers = github_headers, json = payload, auth = auth)
    response.raise_for_status()

def get_latest_version_tag(branch: str, pattern: str = 'v[0-9]*.[0-9]*.[0-9]*') -> str:
    command = ['git', 'describe', f"--match={pattern}", '--abbrev=0', '--tags', branch]
    result = subprocess.run(command, capture_output = True, text = True, check = True)
    latest_version_tag = result.stdout.strip()
    return latest_version_tag

def get_last_commit_sha(branch: str) -> str:
    command = ['git', 'rev-parse', branch]
    result = subprocess.run(command, capture_output = True, text = True, check = True)
    sha = result.stdout.strip()
    return sha

def find_tag(repo: str, tag_pattern: str, commit_sha: str, auth: requests.auth.AuthBase) -> str:
    url = f'https://api.github.com/repos/{repo}/tags'
    response = requests.get(url, headers = github_headers, auth = auth)
    response.raise_for_status()
    tag_regex = re.compile(tag_pattern)
    tags = response.json()
    for tag in tags:
        if tag['commit']['sha'] == commit_sha and tag_regex.match(tag['name']):
            return tag['name']
    return None

def push_tag(repo: str, tag: str, commit_sha: str, auth: requests.auth.AuthBase):
    url = f"https://api.github.com/repos/{repo}/git/refs"
    payload = {
        "ref": f"refs/tags/{tag}",
        "sha": commit_sha
    }
    response = requests.post(url, headers = github_headers, json = payload, auth = auth)
    response.raise_for_status()

def fetch_latest_pull_request(repo: str,
                              pull_request_state: PullRequestState,
                              head_branch: str,
                              release_branch_pattern: str,
                              main_branch_pattern: str,
                              auth: requests.auth.AuthBase) -> dict:
    pull_requests = fetch_pull_requests(repo = repo, pull_request_state = pull_request_state, auth = auth)
    pull_requests = filter(pull_requests = pull_requests, head_ref_pattern = head_branch)
    # Find pull requests that target a release branch
    target_pull_requests = filter(pull_requests = pull_requests, base_ref_pattern = release_branch_pattern)
    if not target_pull_requests:
        # Find pull requests that target the main branch
        target_pull_requests = filter(pull_requests = pull_requests, base_ref_pattern = main_branch_pattern)
    pull_request = find_latest_pull_request(target_pull_requests)
    if pull_request is None:
        raise Exception('No pull requests found')
    return pull_request
