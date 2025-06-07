# Copyright 2025 Claudionor N. Coelho Jr

plain_c_test = "plain C++ test instantiating C code to run with gcov"
plain_cxx_test = "plain C++ test to run with gcov"
google_test = "Google Test"

language_interfaces = {
    "c++": plain_cxx_test,
    "cxx": plain_cxx_test,
    "cc": plain_cxx_test,
    "cpp": plain_cxx_test,
    "c": plain_c_test,
    "python": "pytest"
}

def is_c(language):

    '''
        Check if language is C++ type.

        :param filename: language specified by the user.

        :return: True or False

    '''

    return language in ["c", ".c"]


def is_cxx(language):

    '''
        Check if language is C type.

        :param filename: language specified by the user.

        :return: True or False

    '''

    return language in [
        "c++", "cxx", "cc", "cpp", ".cxx", ".cc", ".cpp"]


def is_c_cxx(language):

    '''
        Check if language is C/CXX type.

        :param filename: language specified by the user.

        :return: True or False

    '''

    return is_c(language) or is_cxx(language)


def is_python(language):
    '''
        Check if language is python type.

        :param filename: language specified by the user.

        :return: True or False

    '''

    return language in ["python", "py", ".py"]
