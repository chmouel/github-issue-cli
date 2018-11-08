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
import re
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

    def get_card_column(self, card_id):
        headers, data = self.client.requestJsonAndCheck(
            "GET",
            "/projects/columns/cards/" + str(card_id),
            headers=self.headers,
        )
        return(headers, data)

    def move_card_to_column(self, card_id, dest_column_id):
        data = {
            'position': "top",
            "column_id": dest_column_id
        }
        headers, data = self.client.requestJsonAndCheck(
            "POST",
            "/projects/columns/cards/" + str(card_id) + "/moves",
            headers=self.headers,
            input=data
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


def add_card_to_column(args, token, parser):
    if not all([args.project_location,
                args.board, args.column, args.issuepr]):
        print("ERROR: Missing argument for create action.\n")
        parser.print_help()
        return

    g = Project(token)
    project = g.get_project_by_desc(args.project_location,
                                    args.board)
    if not project:
        raise Exception("Cannot find project board: %s in %s" %
                        (args.board, args.project_location))
    column_id_of_backlog = g.get_cards_board_project(
        project['id'], args.column)
    column_id_of_backlog = column_id_of_backlog['id']
    h, d = g.add_to_card_to_column(
        column_id_of_backlog,
        args.issuepr
    )

    # Can't get f-string to work here :()
    return ("Issue has been added to project "
            "%s%s%s in "
            "%s\"%s\"%s "
            "column URL: %s%s%s" %
            (C.YELLOW, project['name'], C.END,
             C.GREEN, args.column, C.END,
             C.RED, project['html_url'], C.END))


def move_card(args, token, parser):
    g = Project(token)
    project = g.get_project_by_desc(args.project_location,
                                    args.board)
    if not project:
        raise Exception("Cannot find project board: %s in %s" %
                        (args.board, args.project_location))

    column_orig = g.get_cards_board_project(
        project['id'], args.column)
    assert(column_orig)

    column_dest = g.get_cards_board_project(
        project['id'], args.destination_column)
    assert(column_dest)

    chosen_cards = []
    _, cards = g.list_card_column(column_orig['id'])
    # expensive but we don't have much choice,
    for card in cards:
        _, cardDetail = g.get_card_column(card['id'])

        if not cardDetail['note']:
            continue

        if re.match(args.card_content_regexp, cardDetail['note']):
            chosen_cards.append(cardDetail)

    if len(chosen_cards) == 0:
        print("Could not find your card")

    for card in chosen_cards:
        g.move_card_to_column(card['id'], column_dest['id'])

    return ("We have moved %s\"%d\"%s cards from %s\"%s\"%s to %s\"%s\"%s" % (
        C.YELLOW, len(chosen_cards), C.END,
        C.GREEN, args.column, C.END,
        C.BLUE, args.destination_column, C.END,
    ))


def move_cards_between_columns(args, token, parser):
    if not all([args.project_location, args.board,
                args.destination_column, args.column]):
        print("I need a column and a"
              " destination_column when moving all cards")
        parser.print_help()
        return

    g = Project(token)
    project = g.get_project_by_desc(args.project_location,
                                    args.board)
    if not project:
        raise Exception("Cannot find project board: %s in %s" %
                        (args.board, args.project_location))

    column_orig = g.get_cards_board_project(
        project['id'], args.column)
    assert(column_orig)

    column_dest = g.get_cards_board_project(
        project['id'], args.destination_column)
    assert(column_dest)

    _, cards = g.list_card_column(column_orig['id'])
    for card in cards:
        g.move_card_to_column(card['id'], column_dest['id'])

    return ("We have moved %s\"%d\"%s cards from %s\"%s\"%s to %s\"%s\"%s" % (
        C.YELLOW, len(cards), C.END,
        C.GREEN, args.column, C.END,
        C.BLUE, args.destination_column, C.END,
    ))


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

    if args.action == "add_card_to_column":
        return add_card_to_column(args, token, parser)
    elif args.action == "move_all_cards_between_columns":
        return move_cards_between_columns(args, token, parser)
    elif args.action == "move_card":
        return move_card(args, token, parser)
    else:
        return parser.format_help()


def parse_args(args):
    parser = argparse.ArgumentParser(description='GitHhub Project CLI.')

    mainparser = parser.add_subparsers(help='action to run', dest='action')
    parser.add_argument(
        "--token", type=str,
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub Oauth Token. It will try the GITHUB_TOKEN"
        " env or from `git config --get github.oauth-token`"
    )

    # ADD card to column
    add_card_to_column = mainparser.add_parser(
        'add_card_to_column',
        help='Add card to a column')

    add_card_to_column.add_argument(
        '-p', '--project-location',
        required=True,
        type=str,
        help='Repo or Organisation where the board is located')

    add_card_to_column.add_argument(
        '-b', '--board', type=str,
        required=True,
        help='Board by name')

    add_card_to_column.add_argument(
        '-c', '--column', type=str,
        required=True,
        help='Column name')

    add_card_to_column.add_argument(
        '-i', '--issuepr', type=str,
        required=True,
        help='Issue or PR to add')

    # Move card between columns
    move_cards_between_columns = mainparser.add_parser(
        'move_all_cards_between_columns',
        help='Move all cards between columns')

    move_cards_between_columns.add_argument(
        '-dc', '--destination-column', type=str,
        required=True,
        help='Destination column when moving')

    move_cards_between_columns.add_argument(
        '-p', '--project-location',
        required=True,
        type=str,
        help='Repo or Organisation where the board is located')

    move_cards_between_columns.add_argument(
        '-b', '--board', type=str,
        required=True,
        help='Board by name')

    move_cards_between_columns.add_argument(
        '-c', '--column', type=str,
        required=True,
        help='Column name')

    # Move card between columns
    move_card = mainparser.add_parser(
        'move_card',
        help='Move a card between column')

    move_card.add_argument(
        '-dc', '--destination-column', type=str,
        required=True,
        help='Destination column when moving')

    move_card.add_argument(
        '-p', '--project-location',
        required=True,
        type=str,
        help='Repo or Organisation where the board is located')

    move_card.add_argument(
        '-r', '--card-content-regexp',
        required=True,
        type=str,
        help='Regexp to match the card')

    move_card.add_argument(
        '-b', '--board', type=str,
        required=True,
        help='Board by name')

    move_card.add_argument(
        '-c', '--column', type=str,
        required=True,
        help='Column name')


    return parser
