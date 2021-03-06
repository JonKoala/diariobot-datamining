#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inout
from db import Dbinterface
from db.models import Publicacao, Predicao_Classificacao, Predicao_Regex

import argparse
import os
import re
from decimal import Decimal


##
# Command line arguments

parser = argparse.ArgumentParser()
parser.add_argument('--full', help='Extract patterns for the whole database', action='store_true')

reset_base = parser.parse_args().full


##
# Utils

# regex patterns
re_money = re.compile('\$:*\s*[1-9][\d\.,]*\d')
re_fractional_part = re.compile('[\.,]\d{1,2}$')

def to_decimal(match):
    treated = ''.join(match.group(0).split()).replace('$', '').replace(':', '')

    integer_match = re.split(re_fractional_part, treated)
    integer_part = re.sub('[\.,]', '', integer_match[0])

    fractional_match = re.search(re_fractional_part, treated)
    fractional_part = re.sub('[\.,]', '', fractional_match.group(0)) if fractional_match else '00'

    return Decimal('{}.{}'.format(integer_part, fractional_part))


##
# Get resources

dbi = Dbinterface(os.environ['DIARIOBOT_DATABASE_CONNECTIONSTRING'])
with dbi.opensession() as session:
    to_extract = session.query(Predicao_Classificacao).join(Predicao_Classificacao.publicacao)
    if not reset_base:
        already_extracted = session.query(Predicao_Regex.publicacao_id)
        to_extract = to_extract.filter(Predicao_Classificacao.publicacao_id.notin_(already_extracted))

    data = [(predicao.publicacao.id, predicao.publicacao.corpo) for predicao in to_extract]


##
# Find Regex patterns (for now, just biggest value)

results = []
for index, publicacao in enumerate(data):

    # get values from publicacao
    iter_matches = re.finditer(re_money, publicacao[1])
    values = [to_decimal(match) for match in iter_matches]

    # get biggest value
    values.sort(reverse=True)
    biggest = next(iter(values), None)

    results += [(publicacao[0], biggest)]


##
# Persist patterns on database

with dbi.opensession() as session:

    # clean old entries
    if reset_base:
        session.query(Predicao_Regex).delete()
        session.flush()

    # insert new patterns
    for result in results:
        predicao_regex = Predicao_Regex(publicacao_id=result[0], valor=result[1])
        session.add(predicao_regex)

    session.commit()
