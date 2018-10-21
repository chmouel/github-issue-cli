*Note: there is other scripts in this repo you may or may not be interested with, only GitHub Issue CLI is generic enough to use*
*Note: sorry for the horrible code but this came out from a couple of curl commands to shell script to python code and never got to clean this up, but works at least*

Github Issue CLI
================

Simple CLI to create issues on the Command Line,

Created it because I could not find any that was doign the job the way I wanted,

Installation
============

* Install Python3
* Install PyGithub
  `pip3 install pygithub`
* Copy script somewhere in your path.
* Set your `oauth.token` in the `github` in your gitconfig to your personal token, this should be
  setup by default by [hub](https://github.com/defunkt/hub) with easy.

Usage
=====

Basic usage :

```bash
% github-issue-cli org/repo
```

This is will open your editor (whatever you specified in **$EDITOR** or vim if not)
where the first line would be the title and the third line will be the body of
the issue.

If you are in vim or emacs the buffer/file will be setup with the markdown
mode. Note that the first line is the title and it start from the third line.
Every lines that starts with a # and a space will be ignored

You can add labels in there separated by comma like so :

```
Labels: bug, urgent, critical
```

which will add all of those to the newly created issue if it exists.

Same goes for assignee if you fill this up with github username and they have
access to this repo then it will be assigned to them.

```
Assignee: user1, user2
```

The special variable `me` will be expander to your username.

There is various command line switch to override those, where some of the
options like `label` and `assignee` can be specified multiple time on the
command line, i.e:

```bash
% github-issue-cli -a user1 -a user2 -l label1 -l label2 org/repo
```

This will show when editing in the template tags,

One niceties is with the `-b` option which allows you to set the body, you can
feed a file name into it when prefixing the `@` character, for example :

```bash
% github-issue-cli -b@/tmp/commit_message org/repo
```

will insert /tmp/commit_message as the body of your commit message.

Tokens are get from the gitconfig section github variable oauth-token, for example like this :

```ini
[github]
	user = me
	oauth-token = token
```

you can override this with the `--token` option or with the `GITHUB_TOKEN` environment variable.

See `--help` for more options.

SEE ALSO
========
hub issue -- https://hub.github.com/hub-issue.1.html

AUTHORS
=======
Chmouel Boudjnah -- <chmouel@chmouel.com>

LICENSE
=======
Apache License 2.0
