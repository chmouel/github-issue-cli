#!/usr/bin/env python3
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
#
# WIP: we mostly only able to create a card in a column for now, will improve
# on the go.
#
import argparse
import github as gh
import os
import subprocess

from lib.common import TerminalColors as C

class Project(object):
    default_base_url = "https://api.github.com"
    default_timeout = 10
    default_per_page = 30

    def __init__(self, token):
        self.client = gh.Requester.Requester(
            token, password=None, base_url=self.default_base_url,
            timeout=self.default_timeout, client_id=None,
            client_secret=None, user_agent='PyGithub/Python',
            verify=True,
            per_page=self.default_per_page, api_preview=False)
        self.headers = {'Accept':
                        'application/vnd.github.inertia-preview+json'}

    def get_projects_org(self, org):
        headers, data = self.client.requestJsonAndCheck(
            "GET",
            "/orgs/" + org + "/projects",
            headers=self.headers,
        )
        return(headers, data)

    def get_projects_repo(self, repo):
        headers, data = self.client.requestJsonAndCheck(
            "GET",
            "/repos/" + repo + "/projects",
            headers=self.headers,
        )
        return(headers, data)

    def get_project_by_desc(self, repo_org, desc):
        if len(repo_org.split('/')) == 2:
            h, d = self.get_projects_repo(repo_org)
        elif len(repo_org.split('/')) == 1:
            h, d = self.get_projects_org(repo_org)
        else:
            raise Exception("Invalid repo or org: %s" % (repo_org))

        for l in d:
            if l['name'].lower() == desc.lower():
                return l

    def get_columns_projectid(self, project_id):
        headers, data = self.client.requestJsonAndCheck(
            "GET",
            "/projects/" + str(project_id) + "/columns",
            headers=self.headers,
        )
        return(headers, data)

    def get_cards_board_project(self, project_id, name):
        h, d = self.get_columns_projectid(project_id)

        for l in d:
            if l['name'].lower() == name.lower():
                return l

    def list_card_column(self, column_id):
        headers, data = self.client.requestJsonAndCheck(
            "GET",
            "/projects/columns/" + str(column_id) + "/cards",
            headers=self.headers,
        )
        return(headers, data)

    def add_to_card_to_column(self, column_id, url):
        data = {
            'note': url
        }

        headers, data = self.client.requestJsonAndCheck(
            "POST",
            "/projects/columns/" + str(column_id) + "/cards",
            headers=self.headers,
            input=data
        )
        return (headers, data)


def create(args, token, parser):
    if not all([args.project_repo,
                args.board, args.column, args.issuepr]):
        print("ERROR: Missing argument for create action.\n")
        parser.print_help()
        return

    g = Project(token)
    project = g.get_project_by_desc(args.project_repo,
                                    args.board)
    if not project:
        raise Exception("Cannot find project board: %s in %s" %
                        (args.board, args.project_repo))
    column_id_of_backlog = g.get_cards_board_project(
        project['id'], args.column)
    column_id_of_backlog = column_id_of_backlog['id']
    h, d = g.add_to_card_to_column(
        column_id_of_backlog,
        args.issuepr
    )

    # Can't get f-string to work here :()
    return ("Issue has been moved to project "
            "%s%s%s in "
            "%s\"%s\"%s "
            "column URL: %s%s%s" %
            (C.YELLOW, project['name'], C.END,
             C.GREEN, args.column, C.END,
             C.RED, project['html_url'], C.END))


def main(arguments):
    parser = parse_args(arguments)
    args = parser.parse_args(arguments)

    if args.token:
        token = args.token
    else:
        token = subprocess.Popen(
            ["git", "config", "--get", "github.oauth-token"],
            stdout=subprocess.PIPE
        ).communicate()[0].strip().decode()

    if args.action == "create":
        return create(args, token, parser)
    elif args.action == "move":
        pass


def parse_args(args):
    parser = argparse.ArgumentParser(description='GitHhub Project CLI.')
    parser.add_argument('-o', '--project-repo', type=str,
                        help='Repo or Organisation where the board is located')
    parser.add_argument('-b', '--board', type=str,
                        help='Board by name')
    parser.add_argument('-c', '--column', type=str,
                        help='Column name')

    parser.add_argument('-dc', '--destination-column', type=str,
                        help='Destination column when moving')

    parser.add_argument('--card', type=str,
                        help='Card name when moving.')

    parser.add_argument('-i', '--issuepr', type=str,
                        help='Issue or PR to add')

    parser.add_argument("--token", type=str,
                        default=os.environ.get("GITHUB_TOKEN"),
                        help="GitHub Oauth Token. It will try the GITHUB_TOKEN"
                        " env or from `git config --get github.oauth-token`")

    parser.add_argument("action", type=str, metavar="ACTION",
                        choices=["create", "move"])

    return parser
