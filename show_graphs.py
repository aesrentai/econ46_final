# SPDX-License-Identifier: (GPL-2.0-or-later) 

import csv

trade_data = csv.DictReader(open('data/cow/Dyadic_COW_4.0_shortened.csv', 'r'))
dispute_data = csv.DictReader(open('data/mid/MIDB_5.0.csv', 'r'))

'''
params: the conflict number according to MIDB
returns: instigatorA, instigatorB, listA, listB, start_year
'''
def parse_conflict_num(conflict_id):
    conflict_id = str(conflict_id)
    listA = []
    listB = []
    #TODO: find a way of doing this more efficient than parsing the entire csv
    for entry in dispute_data:
        if entry['dispnum'] == conflict_id:
            start_year = entry['styear']
            if entry['orig'] == '1':
                #one of the originators:
                if entry['sidea'] == '1':
                    instigatorA = entry['stabb']
                else:
                    instigatorB = entry['stabb']
            else:
                #joined one side of the conflict
                if entry['sidea'] == '1':
                    listA.append(entry['stabb'])
                else:
                    listA.append(entry['stabb'])
    return instigatorA, instigatorB, listA, listB, start_year

'''
params: a list of countries, and the year of conflict
returns: a dict of tuples, (country, dict of trade-partner and trade amount) 

parses trade values for a list of countries at a given year and returns
the amount each country traded with each other
'''
def parse_trade_data(country_list, year):
    # use trade values from year before conflict
    conflict_year = str(int(year) - 1)

    # initialize placeholder values
    trade_values = dict()
    for country in country_list:
        trade_values[country] = dict()

    # actually parse the csv and fill the dicts
    for entry in trade_data:
        if entry['importer1'] in country_list and entry['importer2'] in country_list and entry['year'] == year:
            #well, this is ugly, but it works
            trade_values[entry['importer1']][entry['importer2']] = float(entry['flow1']) + float(entry['flow2'])
            trade_values[entry['importer2']][entry['importer1']] = float(entry['flow1']) + float(entry['flow2'])
    return trade_values

if __name__ == '__main__':
    #TODO: make this interactive
    instigatorA, instigatorB, listA, listB, start_year = parse_conflict_num(12)
    trade_valuesA = parse_trade_data(listA, start_year) if len(listA) > 1 else None
    trade_valuesB = parse_trade_data(listB, start_year) if len(listA) > 1 else None

    print("actually graphing the relationships has not yet been implemented")

