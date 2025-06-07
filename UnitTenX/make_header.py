# Copyright 2025 Claudionor N. Coelho Jr

import argparse
import os


def parse_args(arg_list: list[str] | None):
    '''
        Reads parameters passed to invokation.


        :return: map containing values for all parameters read.

    '''


    model_name = os.getenv('MODEL_NAME', 'openai')
    password = os.getenv('REMOTE_PASSWORD', '')

    parser = argparse.ArgumentParser()

    parser.add_argument('--agent-remote-version', default='10')
    parser.add_argument('--user', default='coelho')
    parser.add_argument('--password', default=password)
    parser.add_argument('--ip', default='`python virtualbox.py ip`')
    parser.add_argument('--model-name', default='openai')
    parser.add_argument('--max-number-of-iterations', default=3, type=int)
    parser.add_argument('--work', default='.')

    args = parser.parse_args(arg_list)

    return args


def main(arg_list: list[str] | None=None):
    args = parse_args(arg_list)

    assert args.password

    with open(os.path.join(args.work, 'makefile.header'), 'w') as fp:
        header = (
            f'AGENT_REMOTE_VERSION = {args.agent_remote_version}\n'
            f'USER = {args.user}\n'
            f'REMOTE_PASSWORD = {args.password}\n'
            f'IP = {args.ip}\n'
            f'MODEL_NAME = {args.model_name}\n'
            f'MAX_RETRIES = {args.max_number_of_iterations}\n\n'
        )
        fp.write(header)


if __name__ == '__main__':
    main()
