#compdef github-issue-cli

local ret=1 state

local args=(
    {-t,--title}'[Title]:title:' \
    {-l,--label}'[Add Label]:label:' \
    {-a,--assignee}'[Add Assigneed]:assignee:' \
    {-b,--body}'[Body of the issue if you specify @ it will include it]:' \
    '--output-file[Set output file]:output file:_files' \
    {-i,--input-file}'[Set input file]:input file:_files' \
    '--help[Show help]' \
    '--token[Set github token]' \
    '--editor[Set editor path]:editor:_files' \
    '--me[Set owner as yourself]' \
    {-n,--noeditor}'[Do not start an editor]' \
    '*:githubrepo:->githubrepo'
)

_arguments -S -C $args && ret=0

case $state in
    githubrepo)
        files=($GOPATH/src/github.com/*/*(/));
        files=(${${(M)files%/*/*}#/})
        _describe 'github repos' files && ret=0
        ;;
    *)

esac

return ret
