# Copyright 2025 Claudionor N. Coelho Jr

from fire import Fire
import json
import yaml
import os
import sys

# generates an yaml file from a json file

def main(filename):

    basename = os.path.basename(filename)

    js = json.load(open(filename))

    del js[0]['source_files']

    yamlfile = os.path.splitext(basename)[0] + '.yaml'

    with open(yamlfile, 'w') as fp:
        fp.write(yaml.dump(js))


if __name__ == '__main__':
    Fire(main)

