# SPDX-License-Identifier: (GPL-2.0-or-later) 

import csv
import networkx as nx
import matplotlib.pyplot as plt
'''
params: the conflict number according to MIDB, the dispute database
returns: instigatorsA, instigatorsB, listA, listB, start_year
'''
def parse_conflict_num(dispute_data, conflict_id):
    instigatorsA = []
    instigatorsB = []
    listA = []
    listB = []
    for entry in dispute_data:
        dispute_num = int(entry['dispnum'])
        if dispute_num > conflict_id:
            #we've already parsed the conflict we want
            break
        elif dispute_num == conflict_id:
            start_year = entry['styear']
            if entry['orig'] == '1':
                #one of the originators:
                if entry['sidea'] == '1':
                    instigatorsA.append(entry['stabb'])
                else:
                    instigatorsB.append(entry['stabb'])
            if entry['sidea'] == '1':
                listA.append(entry['stabb'])
            else:
                listB.append(entry['stabb'])

    return instigatorsA, instigatorsB, listA, listB, start_year

'''
params: a list of countries, and the year of conflict
returns: a dict of tuples, (country, dict of trade-partner and trade amount) 

parses trade values for a list of countries at a given year and returns
the amount each country traded with each other
'''
def parse_trade_data(trade_data, country_list, year):
    # use trade values from year before conflict
    year = str(int(year) - 1)

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

