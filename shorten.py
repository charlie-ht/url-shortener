#!/usr/bin/env python

# array index by a 64-bit integer
# 18446744073709551615 slots
# 18 quintillion 446 quadrillion 744 trillion 73 billion 709 million 551 thousand 615
# ≈ 0.43 × the number of arrangements of a 3×3×3 Rubik's cube ( 4.3×10^19)
# plenty of space for personal
# encode the index as a 62-base integer for short-ish links

import pickle
import os
from flask import Flask, redirect, url_for
from flask import request
import string


try:
    OUR_PATH = os.path.dirname(__file__)
except NameError:
    OUR_PATH = '.'

DB_PATH = os.path.join(OUR_PATH, 'db.pickle')
REDIRECTS: list[int] = []

app = Flask(__name__)


def log(msg, *args):
    print(msg % args)


try:
    statinfo = os.stat(DB_PATH)
except FileNotFoundError:
    log('creating an empty database')
    with open(DB_PATH, 'wb') as f:
        pickle.dump(REDIRECTS, f)


def read_db():
    db = None
    with open(DB_PATH, 'rb') as f:
        db = pickle.load(f)
        log('loaded redirects table with %d entries', len(db))
        for i, r in enumerate(db):
            log(' %s -> %s ', number_to_base(i, 62), r)
    return db


def write_db():
    with open(DB_PATH, 'wb') as f:
        pickle.dump(REDIRECTS, f)
        log('saved redirects table with %d entries', len(REDIRECTS))


BASE_MAP = list(map(str, range(10))) + list(string.ascii_letters)


def number_to_base(n: int, b: int) -> str:
    if n == 0:
        return '0'
    digits: list[str] = []
    while n:
        ndigit = int(n % b)
        if ndigit < len(BASE_MAP):
            digits.append(BASE_MAP[ndigit])
        else:
            digits.append(str(ndigit))
        n //= b

    return ''.join(digits[::-1])


def number_from_base(n: str, base: int) -> int:
    base_10 = 0

    for i, v in enumerate(reversed(n)):
        try:
            multiplicand = BASE_MAP.index(v)
            if multiplicand >= base:
                raise ValueError('%s is not a valid base-%d number' % (n, base))
        except ValueError:
            raise ValueError('%s is not a valid input' % n)
        base_10 += multiplicand * (base ** i)

    return base_10


def shorten(url):
    try:
        index = REDIRECTS.index(url)
    except ValueError:
        index = len(REDIRECTS)
        REDIRECTS.append(url)
        write_db()

    shortened = number_to_base(index, 62)
    return '%s://%s%s\r\n' % (
        request.scheme,
        request.host,
        url_for('redirect_endpoint', name=shortened)), 200


@app.route("/r/<name>")
def redirect_endpoint(name):
    index = number_from_base(name, 62)
    return redirect(REDIRECTS[index], code=302)


@app.route("/shorten/<path:url>")
def shorten_endpoint(url):
    print(request.headers)
    print(url)

    return shorten(url)


def test():
    assert number_to_base(number_from_base('abc', 16), 16) == 'abc'
    assert number_to_base(number_from_base('', 16), 16) == 'ERROR'
    try:
        number_to_base(number_from_base('sdsldklkl', 16), 16)
    except ValueError:
        assert True
    else:
        assert False
    try:
        number_to_base(number_from_base('!{}{wdsldklkl', 62), 62)
    except ValueError:
        assert True
    else:
        assert False
    assert number_to_base(number_from_base('12342', 16), 16) == '12342'
    assert number_to_base(number_from_base('14', 10), 10) == '14'
    assert number_to_base(number_from_base('21411289748917238934', 62), 62) == '21411289748917238934'


if __name__ == '__main__':
    REDIRECTS = read_db()

    app.config.update({
        'DATA_ROOT': 'testing',
    })
    app.run(host='127.0.0.1', port=8082)
