# Copyright 2025 Claudionor N. Coelho Jr

import tiktoken

def num_tokens_from_string(string: str, encoding_name: str="cl100k_base") -> int:
    '''
        Estimate number of tokens in string so that we do not run out of tokens.

        :param string: string to estimate tokens
        :param encoding_name: name of model to use to encode string.

        :return: number of tokens estimated.
    '''
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


