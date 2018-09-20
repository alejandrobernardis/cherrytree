#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import os
import webbrowser
import delegator
from yaspin import yaspin

from pyhocon import ConfigFactory
from clint.arguments import Args
from clint.textui import puts, colored, indent

sys.path.insert(0, os.path.abspath('..'))

args = Args()

# TODO: Change this into class (Code as configuration)
# TODO: Fix mergeConflicts on you local instance of superset and push it to lyft/incubator-superset
# TODO: keep track of versioning and tag internal to the branch name this can be written to a file or tag in general


def os_system(cmd, raise_on_error=True):
    p = delegator.run(cmd)
    if raise_on_error and p.return_code != 0:
        puts(p.err)
        raise Exception("Command failed: {}".format(cmd))


def update_spinner_txt(spinner, txt):
    spinner.text = txt


REMOTES = ['lyft', 'apache', 'hughhhh']

with yaspin(text="Loading", color="yellow") as spinner:
    conf = ConfigFactory.parse_file('scripts/build.conf')

    target = conf.get('target')

    try:
        deploy_branch = args.all[0]
        commit_msg = args.all[1] if len(args.all) > 1 else '🍒'
    except IndexError:
        puts(colored.red('You must enter a branch name e.g. `python scripts/git_build.py {branch_name}`'))
        os._exit(1)

    update_spinner_txt(spinner, 'Checking out changes')

    os_system('git submodule update --checkout')

    os.chdir('upstream')
    for remote in REMOTES:
        update_spinner_txt(spinner, 'Adding remote {}'.format(remote))
        os_system('git remote add {} git@github.com:{}/incubator-superset.git'.format(remote, remote), raise_on_error=False)

    update_spinner_txt(spinner, 'Fetching all branches...')
    os_system('git fetch --all')

    update_spinner_txt(spinner, 'Checking out base branch...')
    os_system('git checkout {}'.format(target))

    os_system('git branch -D {}'.format('temp-branch'), raise_on_error=False)
    os_system('git checkout -b {}'.format('temp-branch'))

    for SHA_, cherry in conf.get('cherries'):
        update_spinner_txt(spinner, 'Placing 🍒 : {}'.format(cherry))
        os_system('git cherry-pick -x {}'.format(SHA_))

    num_of_cherries = len(conf.get('cherries'))
    os_system('git reset --soft HEAD~{}'.format(num_of_cherries))
    os_system('git commit -m \'{}\''.format(conf.get('version')))

    # TODO:(hugh) randomly generate a scientist name just like docker
    update_spinner_txt(spinner, 'Delete deploy branch if already exist')
    os_system('git branch -D {}'.format(deploy_branch), False)

    update_spinner_txt(spinner, 'checking out fresh branch...')
    os_system('git checkout -b {}'.format(deploy_branch))

    update_spinner_txt(spinner, 'Push branch up to github 🚀')
    os_system('git push -f lyft {}'.format(deploy_branch))

    version = conf.get_string('version')
    bumped_version = int(version.split('.')[-1]) + 1

    os.chdir('..')
    current_superset_private_branch = os.popen('git rev-parse --abbrev-ref HEAD').read().split('\n')[0]
    os_system('git add .')
    os_system('git commit -m \'{}\''.format(commit_msg))
    os_system('git push origin {}'.format(current_superset_private_branch))
    update_spinner_txt(spinner, 'Redirecting you to github for PR creation 🚢')
    webbrowser.open_new('https://github.com/lyft/superset-private/compare/{}'
                        .format(current_superset_private_branch))