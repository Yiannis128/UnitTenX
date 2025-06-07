# Copyright 2025 Claudionor N. Coelho Jr

import argparse
import json
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
import os
import pprint

def get_parameters():

    '''
        Reads parameters passed to invokation.


        :return: map containing values for all parameters read.

    '''

    model_name = os.getenv('MODEL_NAME', 'openai')

    parser = argparse.ArgumentParser()

    parser.add_argument('filenames', nargs='+')
    parser.add_argument('-w', '--work', default='.')
    parser.add_argument('-m', '--model', default=model_name)
    parser.add_argument('--debug', default=False, action="store_true")
    parser.add_argument('--header', default=model_name)

    args = parser.parse_args()

    return args

def cxx2c(filename, work, model, optional_header=None, debug=False):
    src = open(filename, 'r').read()

    if model == "azure":
        model = AzureChatOpenAI(
            azure_deployment="gpt-4o",
            api_version="2024-02-15-preview",
            azure_endpoint=(
                "https://ml-dev.openai.azure.com/openai/"
                "deployments/gpt-4o/chat/completions?"
                "api-version=2024-02-15-preview"),
            openai_api_key=os.environ.get("AZURE_OPENAI_KEY", ""),
            temperature=0,
            max_retries=2)

    elif model == "openai":
        llm = ChatOpenAI(temperature=0, model_name="gpt-4o")

    else:
        llm = ChatOpenAI(
            base_url="http://localhost:11434/v1",
            temperature=0,
            model_name=model,
            api_key="ollama")

    if optional_header:
        headers = {}
        for header in optional_header.split(':'):
            if header not in filename:
                headers[header] = open(header, "r").read()

        header_source = (
            '\n\n'.join([
                f'HEADER FILE FOR: {header}\n\n{headers[header]}'
                for header in headers]))
    else:
        optional_header = None
        header_source = "" 

    sys_prompt = '''
    You are an expert software engineer that gets a program in C++
    and translates it to C so that you can test it using C infrastructure.

    You MUST ONLY output the translation for the following program in JSON
    containing only `{ "code": <translated-code>, "map": <dictionary-of-
    translated-c++-names-to-c> }`. In the "map", if a class name is called
    Cat, and the action is a constructor, you must use Cat::Cat, for example.

    If a function or method in `SOURCE CODE` has only an external definition,
    you MUST ONLY create a corresponding external definition.

    You MUST ALWAYS perform a straight translation of functions and statements
    that exist in your original `SOURCE CODE`.

    All functions that are translated from C++ to C MUST be listed in "map",
    like `main` functions.

    If you are translating a header file, you MUST define exactly what is 
    defined in the header file, such as the Abstract Data Type that will be
    used elsewhere.

    For example, the class `class Point { private: int x, y; };` needs to
    be translated to the ADT `typedef struct { int x, y; } Point;`

    Comments should use C convention.

    '''

    if optional_header:
        sys_prompt += (
            "You MUST use the definitions of the following header files\n"
            "in your translation in the following way:\n"
            "- Use the same external function definition signature and data\n"
            "definitions.\n"
            "- Do not re-define data structures contained in header files.\n"
        ) + header_source

    prompt = sys_prompt + f'\n\nFILENAME: {filename}\n\nSOURCE CODE:\n\n{src}'

    if debug:
        print(prompt)
        input('continue:')

    result = llm.invoke(prompt)

    if model == 'openai':
        result = result.content

    result = result.split('\n')

    if result[0][:3] == '```':
        result = result[1:]

    if result[-1][:3] == '```':
        result = result[:-1]

    result = '\n'.join(result)

    js = json.loads(result)

    if not os.path.exists(work):
        os.makedirs(work)

    root, ext = os.path.splitext(os.path.basename(filename))
    ext = ext[1:]

    if ext != 'h':
        new_ext = 'c'
    else:
        new_ext = 'h'


    with open(work + '/' + root + f'.{new_ext}', 'w') as f:
        f.write(js['code'])

    with open(work + '/' + root + f'_{ext}_map.py', 'w') as f:
        pp = pprint.PrettyPrinter(indent=4)
        pretty_string = root + ' = ' + pp.pformat(js['map'])
        f.write(pretty_string)

    return js

def run(filename, 
        work='.', 
        model='dolphincoder:15b', 
        optional_header=None, 
        debug=False):

    print(f'... translating {filename}')

    js = cxx2c(
        filename=filename, 
        work=work, 
        model=model, 
        optional_header=optional_header, 
        debug=debug)

    if debug:
        print(js['code'])
        input('continue:')

    return


if __name__ == '__main__':
    args = get_parameters()
    for filename in args.filenames:
        run(filename=filename,
            work=args.work,
            model=args.model,
            optional_header=args.header,
            debug=args.debug)
