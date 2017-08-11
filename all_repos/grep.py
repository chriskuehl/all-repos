import argparse
import os.path
import subprocess
import sys

from all_repos import cli
from all_repos.config import load_config


class GrepError(ValueError):
    pass


def grep_result(config, repo, args):
    path = os.path.join(config.output_dir, repo)
    ret = subprocess.run(
        ('git', '-C', path, 'grep', *args), stdout=subprocess.PIPE,
    )
    return repo, ret.returncode, ret.stdout


def grep(config, grep_args):
    repos = config.get_cloned_repos()
    ret = {}
    for repo in repos:
        repo, returncode, stdout = grep_result(config, repo, grep_args)
        if returncode == 0:
            ret[repo] = stdout
        elif returncode != 1:
            raise GrepError(returncode)
    return ret


def repos_matching(config, grep_args):
    return set(grep(config, ('--quiet', *grep_args)))


def repos_matching_cli(config, grep_args):
    try:
        matching = repos_matching(config, grep_args)
    except GrepError as e:
        return e.args[0]
    for repo in sorted(matching):
        print(os.path.join(config.output_dir, repo))
    return int(not matching)


def grep_cli(config, grep_args, *, color):
    if color:
        grep_args = ('--color=always', *grep_args)
        filename_fmt = b'\033[1;34m%s\033[m\033[36m:\033[m%s\n'
    else:
        filename_fmt = b'%s:%s\n'
    try:
        matching = grep(config, grep_args)
    except GrepError as e:
        return e.args[0]
    for repo, stdout in sorted(matching.items()):
        repo_b = os.path.join(config.output_dir, repo).encode()
        for line in stdout.splitlines():
            sys.stdout.buffer.write(filename_fmt % (repo_b, line))
            sys.stdout.buffer.flush()
    return int(not matching)


def main(argv=None):
    parser = argparse.ArgumentParser()
    cli.add_config_arg(parser)
    cli.add_color_arg(parser)
    parser.add_argument(
        '--repos-with-matches', action='store_true',
        help='Only print repositories with matches.',
    )
    args, rest = parser.parse_known_args(argv)

    config = load_config(args.config_filename)
    if args.repos_with_matches:
        return repos_matching_cli(config, rest)
    else:
        return grep_cli(config, rest, color=args.color)


if __name__ == '__main__':
    exit(main())
