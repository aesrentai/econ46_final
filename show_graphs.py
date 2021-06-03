# SPDX-License-Identifier: (GPL-2.0-or-later) 

import csv
import itertools 
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import operator

from sklearn import linear_model
'''
params: the conflict number according to MIDB, the dispute database
returns: instigatorsA, instigatorsB, listA, listB, start_year
'''
def parse_conflict_num(dispute_data, conflict_id):
    instigatorsA = []
    instigatorsB = []
    listA = []
    listB = []
    start_year = "-1"
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
params: 
    the parsed trade data
    a list of trade partners
    year of conflict
returns: a dict of tuples, (country, dict of trade-partner and trade amount) 

parses trade values for a list of countries at a given year and returns
the amount each country traded with each other
'''
def parse_trade_data(trade_data, country_list, year, ignore_unknown = True):
    # use trade values from year before conflict
    year = str(int(year) - 1)

    # initialize placeholder values
    trade_values = dict()
    for country in country_list:
        trade_values[country] = dict()

    # actually parse the csv and fill the dicts
    for entry in trade_data:
        if entry['importer1'] in country_list and entry['importer2'] in country_list and entry['year'] == year:
            trade_value = float(entry['flow1']) + float(entry['flow2'])

            #TODO: figure out why this is necessary
            #some weird nonsense where the -9 check works but some logic is wrong somewhere
            if ignore_unknown and trade_value == -18.0:
                continue

            #well, this is ugly, but it works
            trade_values[entry['importer1']][entry['importer2']] = trade_value 
            trade_values[entry['importer2']][entry['importer1']] = trade_value 
    return trade_values

'''
params: list of 3 character country codes, list of both sides, conflict year
returns: list of trade partners in a given year for both sides of the conflict
'''
def get_conflict_trade_partners(trade_data, sideA, sideB, year, ignore_unknown = True):
    #use trade values from year before conflict
    year = str(int(year) - 1)

    #include the original countries in the trade partnerships
    trade_partnersA = sideA.copy()
    trade_partnersB = sideB.copy()

    #parse the entire csv
    for entry in trade_data:
        '''
        ignore all trade relationships with unknown values, most appear to be
        insignificant anyways (ie, Germany trading with New Zealand in 1937)
        '''
        if ignore_unknown and (entry['flow1'] == '-9' or entry['flow2'] == '-9'):
            continue

        '''
        ignore all countries with no trade
        '''
        if entry['flow1'] == '0' or entry['flow2'] == '0':
            continue

        '''
        wrong year
        '''
        if year != entry['year']:
            continue

        if entry['importer1'] in sideA and not entry['importer2'] in trade_partnersA:
            trade_partnersA.append(entry['importer2'])
        if entry['importer1'] in sideB and not entry['importer2'] in trade_partnersB:
            trade_partnersB.append(entry['importer2'])
    return trade_partnersA, trade_partnersB

'''
params:
    a graph
    a country to be added to said graph
    a list of the countries in the graph
    the trade partnerships

returns: none
'''
def add_country_to_graph(G, country, included_countries, trade_partners):
    G.add_node(country)
    for trade_partner in included_countries:
        if trade_partner in trade_partners:
            G.add_edge(country, trade_partner)
    included_countries.append(country)

'''
params: 
    list of instigators
    list of combatants
    dict of dicts (country: trade partners: amounts)
    which side of the conflict: A or B
returns: none

draws a graph of the given network weighted by magnitude of trade
'''
def draw_trade_war_graphs(instigators, combatants, countries, side):
    #TODO: weight the network, use sigmoid smoothing 

    G = nx.Graph()
    included_countries = []
    color_map = []
    #trade_combat_edge_list = [] #to track trade only amongst combatants
    for country, trade_partners in countries.items():
        add_country_to_graph(G, country, included_countries, trade_partners)
        if country in instigators:
            color_map.append('red')
        else:
            color_map.append('green')
    for combatant in combatants:
        if not combatant in countries:
            #no trade with any instigator but still fought
            add_country_to_graph(G, combatant, included_countries, dict())

    pos = nx.circular_layout(G)
    
    ax = plt.gca()
    ax.set_title('Trade Graph for Side ' + side)
    nx.draw_networkx(G, pos, node_color=color_map, with_labels=True, ax=ax)
    plt.show()

    #remove all the noncombatants
    edges_to_remove = []
    for edge in G.edges():
        if not edge[0] in combatants or not edge[1] in combatants:
            edges_to_remove.append(edge)
    for edge in edges_to_remove:
        G.remove_edge(edge[0], edge[1])
    countries_to_remove = []
    for country, _ in countries.items():
        if not country in combatants:
            countries_to_remove.append(country)
    for country in countries_to_remove:
        G.remove_node(country)

    ax2 = plt.gca()
    ax2.set_title('Combatant Graph for Side ' + side)
    nx.draw_networkx(G, pos, node_color = 'r', ax=ax2, nodelist=combatants)
    plt.show()

'''
params: a dict, mapping each country to a dict of its trade partners and amounts
returns: a dict, with the same format as the input, except with percentages
'''
def calculate_trade_percentages(trade_values):
    trade_percentages = dict()
    for country, partners in trade_values.items():
        trade_volume = sum(map(abs, partners.values()))
        if trade_volume == 0:
            #no trade, joined anyways
            trade_percentages[country] = {} 
            continue
        trade_percentages[country] = {k: v / trade_volume for k, v in partners.items()} 
    return trade_percentages

'''
params: the combatants on one side, the instigators of that side, and the parsed trade percentages 
returns: a list of (trade % with instigator[index], 0 if did not join, 1 if join)

used to check the likelihood trade partners joined one side of a conflict
'''
def create_trade_join_statistics(side, instigators, trade_percentages, index=0): 
    trade_join_pairs = []
    for country, amounts in trade_percentages.items():
        if country in instigators:
            #don't check if an instigator joined themself
            continue

        joined = 1 if country in side else 0
        try:
            entry = list((trade_percentages[country][instigators[index]], joined))
        except KeyError:
            #no trade with instigator 
            entry = list((0, joined)) 
        trade_join_pairs.append(entry)
    return trade_join_pairs

'''
params: the trade percenages, the combatants on one side, the instigators on one side
returns: the slope and intercept of the regression model

performs a linear regression on the trade percentages and likelihood of joining one side
'''
def regression_models(percentages, side, instigators):
    linear_data = np.array(create_trade_join_statistics(side, instigators, percentages)) 
    X = linear_data[:, 0].reshape(-1, 1)
    y = linear_data[:, 1].reshape(-1, 1)
    lin_reg = linear_model.LinearRegression().fit(X, y)
    try:
        log_reg = linear_model.LogisticRegression().fit(X, y.ravel())
    except ValueError:
        #Logistic Regression fails if all y values are 0, so return error 
        return lin_reg.coef_, lin_reg.intercept_, -1, -1
    return lin_reg.coef_, lin_reg.intercept_, log_reg.coef_, lin_reg.intercept_

'''
params: the trade percenages, the combatants on one side, the instigators on one side
returns: none

shows a summary of the data for one side
'''
def show_summary(percentages, side, instigators):
    print("Instigators: " + str(instigators))
    print("Combatants: " + str(side))

    if side == instigators:
        print("No models available: no one joined instigators") 
        return

    if percentages is None:
        print("No models available: instigators had no trade")
        return

    slope, intercept, exponent, log_intercept = regression_models(percentages, side, instigators) 

    print("Linear Regression: y = {0}x + {1}".format(slope[0][0], intercept[0]))
    if exponent != -1:
        print("Logistic Regression: y = 1/(1+e^-({0} + {1}x))".format(log_intercept[0], exponent[0][0]))
    else:
        print("Logistic Regression model not available")

if __name__ == '__main__':
    print("Importing Data.  This may take a while.")
    trade_data = csv.DictReader(open('data/cow/Dyadic_COW_4.0_shortened.csv', 'r'))
    trade_data = list(trade_data)
    dispute_data = csv.DictReader(open('data/mid/MIDB_5.0.csv', 'r'))
    dispute_data = list(dispute_data)

    while True:
        conflict_num = input("Enter a conflict number.  Type \"exit\" without the quotes to leave\n")
        if conflict_num == "exit":
            print("Goodbye")
            exit(0)
        try:
            conflict_num = int(conflict_num)
        except ValueError:
            print("Invalid conflict number")
            continue

        print("Parsing conflict number.")
        instigatorsA, instigatorsB, sideA, sideB, start_year = parse_conflict_num(dispute_data, conflict_num)
        
        if int(start_year) == -1:
            print("Conflict number {0} does not exist".format(str(conflict_num)))
            continue

        print("Retrieving trade partners")
        instigatorsA_trade_partners, instigatorsB_trade_partners = get_conflict_trade_partners(
                trade_data,
                instigatorsA, 
                instigatorsB, 
                start_year
        )

        print("Parsing trade data for side A")
        trade_valuesA = parse_trade_data(trade_data, instigatorsA_trade_partners, start_year) if len(instigatorsA_trade_partners) > 1 else None

        print("Parsing trade data for side B")
        trade_valuesB = parse_trade_data(trade_data, instigatorsB_trade_partners, start_year) if len(instigatorsB_trade_partners) > 1 else None
    
        print("Calculating trade percentages for side A")
        trade_percentagesA = calculate_trade_percentages(trade_valuesA) if trade_valuesA is not None else None

        print("Calculating trade percentages for side B")
        trade_percentagesB = calculate_trade_percentages(trade_valuesB) if trade_valuesB is not None else None
        
        print("Side A Summary:")
        show_summary(trade_percentagesA, sideA, instigatorsA)
        print("Side B Summary:")
        show_summary(trade_percentagesB, sideB, instigatorsB)

        #TODO: add utility to intersect two lists so both sides can be shown in the same graph
        if trade_valuesA != None: draw_trade_war_graphs(instigatorsA, sideA, trade_valuesA, 'A') 
        if trade_valuesB != None: draw_trade_war_graphs(instigatorsB, sideB, trade_valuesB, 'B') 
