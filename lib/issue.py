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
import atexit
import argparse
import github as gh
import os
import sys
import subprocess
import tempfile

DEFAULT_TEMPLATE = """{title}

{body}

<!--
Everything inside this comment block would be ignored!.
=======================================================

Tags: commas delimited

Labels: {labels_flat}
Assignee: {assignee_flat}
Project: {args.repo}

Editors configs (you can ignore):

Local Variables:
mode: markdown
End:
vim: ft=markdown
-->
"""

DEFAULT_BODY = "Insert body here."
DEFAULT_TITLE = "Insert title here."
TMPFILE = tempfile.mktemp("github-new-issue.py.XXXXXX")
atexit.register(lambda: os.path.exists(TMPFILE) and os.remove(TMPFILE))


def main(arguments):
    parser = parse_args(arguments)
    args = parser.parse_args(arguments)

    labels = args.label or []
    labels_flat = ", ".join(labels)
    body = args.body or DEFAULT_BODY
    title = args.title or DEFAULT_TITLE
    assignee = []
    assignee_flat = ""
    if args.me:
        assignee_flat = "me"
    elif args.assign:
        assignee_flat = ", ".join(args.assign)

    if body and not title:
        print("Can't specify a body without a title")
        exit(1)

    if body and body[0] == "@":
        if not os.path.exists(body[1:]):
            print("This file %s does not exist" % (body[1:]))
            sys.exit(1)
        body = open(body[1:]).read().strip()

    if args.input_file:
        template_processed = open(args.input_file, 'r').read()
    else:
        template_processed = DEFAULT_TEMPLATE.format(**locals())
    open(TMPFILE, "w").write(template_processed)
    if not args.noeditor:
        if args.editor:
            editor = args.editor
        elif 'EDITOR' in os.environ:
            editor = os.environ['EDITOR']
        else:
            editor = 'vim'
        subprocess.call([editor, TMPFILE])

    blob = open(TMPFILE, 'r').readlines()
    if args.output_file:
        open(args.output_file, 'w').write("".join(blob))

    incomment = False
    newblob = []
    for x in blob:
        if x.strip() == "<!--":
            incomment = True
            continue
        elif x.strip() == "-->":
            incomment = False
            continue

        if not incomment:
            newblob.append(x.strip())
            continue

        if x.startswith("Labels:"):
            line = x.replace("Labels:", "").strip()
            if line == '':
                break
            sp = line.split(",")
            labels.extend(sp)
            continue
        elif x.startswith("Assignee:"):
            line = x.replace("Assignee:", "").strip()
            if line == '':
                break
            assignee = line.split(",")
            continue

    if len(newblob) == 0:
        print("No title defined")
        sys.exit(1)

    while not newblob[-1] or newblob[-1] == '':
        del newblob[-1]
    title = newblob[0]
    if newblob[1].strip():
        print("Template doesn't have a newline between title and body.. exit")
        sys.exit(1)

    body = "\n".join(newblob[2:])

    if args.token:
        token = args.token
    else:
        token = subprocess.Popen(
            ["git", "config", "--get", "github.oauth-token"],
            stdout=subprocess.PIPE
        ).communicate()[0].strip().decode()

    if not token:
        print("Cannot find a github token")
        sys.exit(1)

    if title == DEFAULT_TITLE:
        print("We still have the default title, exiting.")
        sys.exit(1)

    if body == DEFAULT_BODY:
        print("We still have the default body, exiting.")
        sys.exit(1)

    g = gh.Github(token)
    repo = g.get_repo(args.repo)
    repo_labels = repo.get_labels()
    good_labels = []
    for x in labels:
        for l in repo_labels:
            if x == l.name:
                good_labels.append(x)

    issue = repo.create_issue(
        title=title,
        body=body,
        labels=good_labels
    )
    if assignee:
        if 'me' in assignee:
            assignee.remove('me')
            assignee.append(g.get_user().login)
        issue.add_to_assignees(*assignee)
    return(issue.html_url)


def parse_args(args):
    parser = argparse.ArgumentParser(description='Create a GitHub.')
    parser.add_argument('-l', '--label', metavar='labels', type=str,
                        action='append',
                        help='labels for the created issue, '
                        'you can have multiples of them')

    parser.add_argument('-a', '--assign', metavar='assignee', type=str,
                        action='append',
                        help='Assign to those GITHUB user')

    parser.add_argument('-t', "--title", type=str,
                        help="Title of the issue")

    parser.add_argument('--output-file', type=str,
                        help="Save the output of the file to this")

    parser.add_argument('--input-file', type=str,
                        help="Use this input file")

    parser.add_argument('-b', "--body", type=str,
                        help="Body of the issue, if you specify a @ at first "
                             "it will include the file following")

    parser.add_argument("--token", type=str,
                        default=os.environ.get("GITHUB_TOKEN"),
                        help="GitHub Oauth Token. It will try the GITHUB_TOKEN"
                        " env or from `git config --get github.oauth-token`")

    parser.add_argument("repo",
                        help="Github Repository where to create the issue")

    parser.add_argument("--me", action="store_true",
                        help="Assign the issue to yourself.")

    parser.add_argument("--editor", action="store_true",
                        help="Editor to use default to $EDITOR or vim.")

    parser.add_argument("-n", "--noeditor", action="store_true",
                        help="Don't start the editor")

    return parser
