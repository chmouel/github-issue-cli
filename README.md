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
* Set your oauth.token in your gitconfig to your personal token, this should be
  setup by default by [hub](https://github.com/defunkt/hub)


Usage
=====

Basic usage :
```
% github-issue-cli chmouel/space3
```

This is will open vim where the first line would be the title and the third line
will be the body of the issue. (gitcommit style and uses the same filetype mode).

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

```
github-issue-cli -a user1 -a user2 -l label1 -l label2 chmouel/space3
```

This will show when editing in the template tags,

One niceties is with the `-b` option which allows you to set the body, you can
feed a file name into it when prefixing character, for example :

```
github-issue-cli -b@/tmp/commit_message chmouel/space3
```

will insert /tmp/commit_message as the body of your commit message.

See `--help` for more options.

AUTHORS
=======
Chmouel Boudjnah <chmouel@chmouel.com>

LICENSE
=======
Apache License 2.0
