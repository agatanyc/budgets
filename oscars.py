#!/usr/bin/env python3

"""Prints the year, title, and budget of Best Picture Oscar-winning movies.
Data are obtained by scraping Wikipedia; in particular, the list of movies
comes from: http://en.wikipedia.org/wiki/Academy_Award_for_Best_Picture#1920s
"""

import bs4
import io
import os
import urllib.request

from sys import argv, exit, stderr, stdout

def fetch(base, path):
    """(str, str) -> bs4.BeautifulSoup

    Fetch and parse the HTML document at the specified base + path URL.  Return
    a BeautifulSoup object representing the document.
    """
    with urllib.request.urlopen(base + path) as source:
        return bs4.BeautifulSoup(source.read())

def format_budget(budget, width=14, prefix='$ '):
    """(float or None) -> str

    Return a representation of the specified `budget` suitable for printing.
    The `width` should be enough to accomodate the `prefix` and a commified
    representation of the nearest integer to `budget`.
    """
    wide = prefix + '{:>' + str(width - len(prefix)) + '}'  # e.g., '$ {:>12}'
    thin = '{:,}'.format(round(budget)) if budget else '-'
    return wide.format(thin)

def get_budget(page):
    """(bs4.Tag) -> str or None

    Return the budget of the movie described by the specified `page`.
    """
    ths = [th for th in page.find_all('th')
            if 'Budget' in (th.find(text=True) or '')]
    if not ths:
        return ''
    td = ths[0].parent.find('td')
    return ' '.join(td.find_all(text=True))

def get_link(td):
    """(bs4.Tag) -> str

    Return the link to the movie page referenced in the specified `td` tag.
    """
    return td.find('a').attrs['href']

def get_title(td):
    """(bs4.Tag) -> str

    Return the movie title from the specified `td` tag.
    """
    return str(td.find(text=True))

def get_year(big):
    """(bs4.Tag) -> str

    Return a formatted representation of the year represented by the specified
    BeautifulSoup `big` tag.
    """

    # Wikipedia's '<big>' tags contain textual elements that are either just
    # the year (['YYYY']), or else the year, a slash, and the last two digits
    # of the following year (['YYYY', '/', 'YY']) -- either being optionally
    # followed by a footnote ('[A]').

    texts = big.find_all(text=True)
    multi = len(texts) > 1 and texts[1] == '/'
    return ''.join(texts[:3]) if multi else str(texts[0])

def parse_big(big):
    """(bs4.Tag) -> (str, str, str)

    Return the year from the specified `big` tag, followed by the title of the
    first movie named in the big's (grand)parent table, and the relative link
    for details of that movie.
    """
    table = big.parent.parent
    td = table.find('td')
    return get_year(big), get_title(td), get_link(td)

def parse_budget(text):
    """(str) -> float or None

    Return the US dollar amount represented by the specified `text`, or None if
    `text` cannot be parsed.  The format of `text` must be:

    1. Optional non-'$' leading characters
    2. A '$' followed by optional space
    3. A floating point number, including optional '.' and/or commas
    4. Optionally, space followed by the word 'million'
    5. Optionally, any trailing characters
    """
    i = text.find('$')
    if i == -1:
        return None
    parts = text[i + 1:].split()
    value = parse_number(parts[0])
    if len(parts) > 1 and parts[1].startswith('million'):
        return value * 1000000
    return value

def parse_number(text):
    """(str) -> float

    Return the number represented by `text`.  The number may contain an
    optional '.' and commas.
    """
    return float(''.join(c for c in text if c in '0123456789.'))

def main(out=stdout, base='http://en.wikipedia.org'):

    path = '/wiki/Academy_Award_for_Best_Picture'

    soup = fetch(base, path)
    bigs = soup.find_all('big')

    count = 0
    total = 0

    for big in bigs:
        year, title, link = parse_big(big)
        page = fetch(base, link)
        budget = parse_budget(get_budget(page))
        if budget:
            count += 1
            total += budget
        print('{:8} {:50} {}'.format(year, title, format_budget(budget)),
                file=out)

    print('----\nAverage: $ {:,.0f}'.format(total / count), file=out)

def test():

    # Get the expected output from a local file.

    with open('expected.txt') as source:
        expected = source.read()

    # Get the actual output by having `main` print to a string stream.

    out = io.StringIO()
    main(out, "file://" + os.path.dirname(os.path.realpath(__file__)))
    actual = out.getvalue()

    assert expected == actual

if __name__ == '__main__':

    if len(argv) == 1:
        main()
    elif len(argv) == 2 and argv[1] in ['-t', '--test']:
        test()
    else:
        print("usage: python3 oscars.py [-t|--test]", file=stderr)
        exit(1)
