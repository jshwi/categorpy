"""
print
=====

Printing with configurable colors
"""
from pygments import highlight

# noinspection PyUnresolvedReferences
from pygments.formatters import Terminal256Formatter  # pylint: disable=E0611

# noinspection PyUnresolvedReferences
from pygments.lexers import YamlLexer  # pylint: disable=E0611


def pygment_print(string):
    """Print with ``pygments``

    Read the string entered in method

    Configure syntax highlighting for either shell or ini files and
    processes

    :param string:  What is to be printed
    """
    print(
        highlight(string, YamlLexer(), Terminal256Formatter(style="monokai"))
    )
