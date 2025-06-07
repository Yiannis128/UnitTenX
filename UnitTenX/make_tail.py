# Copyright 2025 Claudionor N. Coelho Jr

import os
import shutil
import sys

def make_all():
    work = sys.argv[1]
    make = open(os.path.join(work, 'Makefile'), 'r').readlines()

    make_items = []
    for line in make:
        line = line.rstrip()
        if line and line.endswith(':'):
            make_items.append(line[:-1])

    makefile = open(os.path.join(work, 'Makefile'), 'r').read().split('\n')

    for i in range(len(makefile)):
        line = makefile[i]
        if line == 'all:':
            makefile = makefile[:i-1]
            break

    makefile.append('')
    makefile.append('all:')
    for item in make_items:
        makefile.append(f'\tmake -f $(WORK)/Makefile {item}')
    makefile.append('')

    with open(os.path.join(work, 'Makefile'), 'w') as fp:
        fp.write('\n'.join(makefile))


work = sys.argv[1]
make_all()
unit_ten_x = os.path.dirname(__file__)
shutil.copy(unit_ten_x + '/scripts/run_all_tests.sh', work)
shutil.copy(unit_ten_x + '/scripts/clean_all_tests.sh', work)
shutil.copy(unit_ten_x + '/scripts/check_crashes.sh', work)
shutil.copy(unit_ten_x + '/scripts/create_regression.sh', work)

