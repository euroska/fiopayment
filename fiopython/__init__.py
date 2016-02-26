# -*- coding: utf-8 -*-
from fio import Fio
from fio import FioAccount
from fio import FioPayment
from fio import FioResult

error_codes = {
    0: u'ok - příkaz byl přijat',
    1: u'nalezené chyby při kontrole příkazů',
    2: u'varování kontrol - chybně vyplněné hodnoty',
    11:u'syntaktická chyba',
    12:u'prázdný import - v souboru nejsou žádné příkazy',
    13:u'příliš dlouhý soubor - soubor je delší než 2 MB',
    14:u'prázdný soubor - soubor neobsahuje příkazy',
}

statuses = {
    'ok': u'příkaz přijat',
    'error': u'chyba v příkazu',
    'warning': u'varování, některý z údajů je nesprávně vyplněn (např. datum)',
    'fatal': u'chyba na straně bankovního systému banky',
}

payment_types = {
    431001: u'standardní',
    431004: u'zrychlená',
    431005: u'prioritní',
    431022: u'příkaz k inkasu',
}

country_codes = {
    'CZ': u'Česká republika',
    'SK': u'Slovensko',
}

payment_titles = {
    110: u'Vývoz zboží',
    112: u'Finanční pronájem (leasing) - vývoz',
}
