# -*- coding: utf-8 -*-
# Author: Chmouel Boudjnah <chmouel@chmouel.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import subprocess
import github as gh
import requests
import os

ZHUB_URL = 'https://api.zenhub.io'


def get_a_token(env, gitgetkey):
    if os.environ.get(env):
        return os.environ.get(env)

    _token = subprocess.Popen(
        ["git", "config", "--get", gitgetkey],
        stdout=subprocess.PIPE).communicate()[0].strip().decode()
    if _token:
        return _token
    else:
        raise Exception(
            f"Cannot find a token in env {env} or git config key {gitgetkey} ")


class ZHub(object):
    # We store most of the stuff, even if not used, perhaps one day we can
    # pickle this
    github_repos_id = {}
    zenhub_board_info = {}

    def __init__(self, token=None, github_token=None):
        self.github_token = github_token
        self.token = token

        if not self.github_token:
            self.github_token = get_a_token("GITHUB_TOKEN",
                                            "github.oauth-token")
        if not self.token:
            self.token = get_a_token("ZENHUB_TOKEN", "zenhub.oauth-token")

    def _request(self, method, url, data=None):
        headers = {'X-Authentication-Token': self.token}
        r = requests.request(
            method, ZHUB_URL + url, data=data, headers=headers)
        r.raise_for_status()
        return method == "GET" and r.json() or r

    def github_get_repo_id(self, repo):
        if repo in self.github_repos_id:
            return self.github_repos_id[repo]
        ghcnx = gh.Github(self.github_token)
        grepo = ghcnx.get_repo(repo)
        self.github_repos_id[repo] = grepo.id
        return grepo.id

    # https://github.com/ZenHubIO/API#get-the-zenhub-board-data-for-a-repository
    def board_data_for_repo(self, repo_id):
        if repo_id in self.zenhub_board_info:
            return self.zenhub_board_info[repo_id]

        info = self._request("GET", f"/p1/repositories/{repo_id}/board")
        processed = {x['name']: x['id'] for x in info['pipelines']}
        self.zenhub_board_info[repo_id] = processed
        return processed

    # https://github.com/ZenHubIO/API#move-an-issue-between-pipelines
    def move_issue_to_pipeline(self,
                               repo_id,
                               issue_number,
                               pipeline_id,
                               position="top"):
        url = f"/p1/repositories/{repo_id}/issues/{issue_number}/moves"
        data = {
            "pipeline_id": str(pipeline_id),
            "position": position,
        }
        return self._request("POST", url, data=data)
