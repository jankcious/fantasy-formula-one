# coding=utf-8

import argparse
import csv
from collections import defaultdict
from collections import OrderedDict
import re
from lxml.html import parse
from urllib import request
import lxml
from lxml.html.clean import Cleaner
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from unidecode import unidecode

#Build up globals from season documents
seasons = pd.DataFrame.from_csv('season_info.csv')
RACES = list(seasons['Country'])
URLs = {seasons['Country'][i]:seasons['url'][i] for i in range(len(seasons))}
drivers = pd.DataFrame.from_csv('driver_info.csv')
DRIVERS = list(drivers['GivenName'] + " " + drivers['FamilyName'])
conv_DRIVERS = {unidecode(drivers['FamilyName'][i]):(drivers['GivenName'][i] + " " + drivers['FamilyName'][i])
                for i in range(len(drivers))}

### Class Definitions ###
class Team():
    """Team is an object correlating to a specific F1 race.  An instance will open the corresponding file
    and build a dictionary of players and their drivers.
    """
    def __init__(self, name):
        global RACES
        if name not in RACES:
            print(name, 'is an invalid race name.\nPlease select from the following:\n', RACES)
        self.name = name
        with open('teams/team_' + self.name + '.csv', 'rt', newline="\r\n") as f:
            teams = [line.replace('"', '').split(',') for line in f if len(line.split(',')) > 1]
            teams.pop(0) #remove header
        pattern = re.compile('^(.*?)\(')
        for line in range(len(teams)):
            for driver in range(2, len(teams[line])):
                teams[line][driver] = pattern.search(teams[line][driver].strip()).group(1).strip()
        self.teams = {}
        for line in teams:
            self.teams[line[1]] = line[2::]
            
    def drop(self, team, driver):
        if team not in self.teams:
            print(team, 'is not in the league.  Try', self.name + '.teams to see your options.')
            raise
        if driver not in self.teams[team]:
            print(driver, 'is not on', team + "'s team.  Try", self.name + '.teams to see the current teams.')
            raise
        self.teams[team].remove(driver)
        #self.push()
                
    def add(self, team, driver):
        if team not in self.teams:
            print(team, 'is not in the league.  Try', self.name + '.teams to see your options.')
            raise
        if len(self.teams[team]) == 5:
            print(team + "'s team already has five drivers.  Consider using drop or replace")
        if driver not in DRIVERS:
            print(driver + "is not a valid driver.  Please select from the following:\n", DRIVERS)
        self.teams[team].append(driver)
        #self.push()
        
    def replace(self, team, drop_racer, add_racer):
        if team not in self.teams:
            print(team, 'is not in the league.  Try', self.name + '.teams to see your options.')
            raise
        if DRIVERS[drop_racer] not in self.teams[team]:
            print(drop_racer, 'is not on', team + "'s team.  Try", self.name + '.teams to see the current teams.')
            raise
        self.teams[team].remove(DRIVERS[drop_racer])
        self.teams[team].append(DRIVERS[add_racer])
        #self.push()
        
    def push(self):
        """Push self.teams to the csv"""
        header = [['Player', 'Driver1', 'Driver2', 'Driver3', 'Driver4', 'Driver5']]
        for player in self.teams.keys():
            header.append([player])
            header[header.index([player])].extend(self.teams[player])     
        with open('teams/team_' + self.name + '.csv', 'wt', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerows(header)
            
    def __repr__(self):
        print_string = ''
        for team in self.teams:
            print_string += team + ':\t' + str(sorted(self.teams[team])) + '\n'
        return print_string
    
    def validate(self, team):
        global DRIVERS
        driver_cost = {}
        cost_column = RACES.index(self.name) * 2 + 2
        with open('Season_Drivers.csv', 'rt', newline='') as f:
            for line in f:
                val = line.split(',')
                driver_cost[val[0]] = val[cost_column]
        budget = 33
        for driver in self.teams[team]:
            budget -= int(driver_cost[driver])
        return budget

class Race():
    """
    Race is an object that correlates to a specific F1 race.  It contains results for 
    qualifying, grid position, finish positions, and the corresponding scores for the fantasy
    league, along with methods for updating any of the positions."""
    def __init__(self, name):
        global RACES
        global DRIVERS
        Fantasy_Finish_Points_Dict = defaultdict(int)
        for position in range(1,11):
            Fantasy_Finish_Points_Dict[position] = 11 - position
        if name not in RACES:
            print(name, 'is an invalid race name.\nPlease select from the following:\n', RACES)
            raise
        self.name = name
        with open('Results/' + self.name + '_Qualifying.csv', 'rt', newline='') as f:
            qualifying_results = [line.split(',') for line in f if len(line.split(',')) > 2]
            qualifying_results.pop(0) #remove header
        with open('Results/' + self.name + '_Race.csv', 'rt', newline='') as f:
            race_results = [line.split(',') for line in f if len(line.split(',')) > 1]
            race_results.pop(0) #remove header
        self.fastest_lap = race_results.pop()[1].strip()
        self.lap_length = int(race_results.pop()[1].strip())
        self.drivers = {line[2].strip() for line in qualifying_results if line[2] != ""}
        self.drivers_position = {}
        self.drivers_points = {}
        self.drivers_cost = {}
        self.grid_position = {}
        self.qualifying_position = {}
        self.constructor_finish = {}
        self.laps_completed = {}
        self.classified = {}
        self.drivers_team = {}
        self.fantasy_points = {}
        self.q_round = {}
        #Go through Race Results file and build attributes
        for line in race_results:
            if line[7].strip() == '':
                self.drivers_points[line[2]] = 0
            else:
                self.drivers_points[line[2]] = int(line[7].strip())
            if line[0].isdigit():
                if line[5][0].isdigit() or line[5][1].isdigit():
                    self.drivers_position[line[2]] = int(line[0])
                else:
                    self.drivers_position[line[2]] = "Ret"
            else:
                self.drivers_position[line[2]] = line[0]
            if line[6].isdigit():
                self.grid_position[line[2]] = int(line[6])
            elif line[6] == 'PL':
                self.grid_position[line[2]] = 'PL'
            else:
                self.grid_position[line[2]] = 'DNS'
            if line[3].strip() not in self.constructor_finish and line[0].strip().isdigit():
                self.constructor_finish[line[3]] = [int(line[0])]
            elif line[0].strip().isdigit():
                self.constructor_finish[line[3]].append(int(line[0]))
            else:
                self.constructor_finish[line[3]] = [0]
            self.drivers_team[line[2]] = line[3]
            self.laps_completed[line[2]] = line[4]
            if line[0].isdigit():
                self.classified[line[2]] = True
            else:
                self.classified[line[2]] = False
        for line in qualifying_results:
            if line[2] in self.drivers:
                try:
                    self.qualifying_position[line[2]] = int(line[0])
                except:
                    self.qualifying_position[line[2]] = 'DNF'
                if line[6] != "":
                    self.q_round[line[2]] = 3
                elif line[5] != "":
                    self.q_round[line[2]] = 2
                elif line[4] != "":
                    self.q_round[line[2]] = 1
                else:
                    self.q_round[line[2]] = 0
                                
    def score(self, watch=False):
        ###Instead we're building a dataframe
        fantasy_points = pd.DataFrame(columns=['Team', 'Qualifying', 'Grid', 'Eff_Grid', 'Finish',
                                               'Qual_Pts', 'Fin_Pts', 'Team_Pts', 'Movement_Pts', 
                                               'Completion', 'Fst_Lap', 'Total_Race_Pts'], index=self.drivers)
        for driver in self.drivers_team:
            fantasy_points.ix[driver, 'Team'] = self.drivers_team[driver]
        for driver in self.qualifying_position:
            fantasy_points.ix[driver, 'Qualifying'] = self.qualifying_position[driver]
        for driver in self.grid_position:
            fantasy_points.ix[driver, 'Grid'] = self.grid_position[driver]
        for driver in self.drivers_position:
            fantasy_points.ix[driver, 'Finish'] = self.drivers_position[driver]
        fantasy_points.Grid.fillna('DNS', inplace=True)
        ordered_position = OrderedDict(sorted(self.grid_position.items(), key=lambda t: str(t[1])))
        ordered_position = OrderedDict(sorted(ordered_position.items(), key=lambda t: len(str(t[1]))))
        pos = 1
        for driver, position in ordered_position.items():
            if fantasy_points.ix[driver, 'Finish'] == 'Ret':
                fantasy_points.ix[driver, 'Eff_Grid'] = np.NaN
            elif fantasy_points.ix[driver, 'Finish'] == 'DNS':
                fantasy_points.ix[driver, 'Eff_Grid'] = np.NaN
            elif str(position).isdigit():
                fantasy_points.ix[driver, 'Eff_Grid'] = pos
                pos += 1
            elif position == "PL":
                fantasy_points.ix[driver, 'Eff_Grid'] = pos
                pos += 1
        for driver, q_round in self.q_round.items():
            if self.qualifying_position[driver] == 1:
                fantasy_points.ix[driver, 'Qual_Pts'] = q_round
            else:
                fantasy_points.ix[driver, 'Qual_Pts'] = max(q_round - 1, 0)
        for driver, pos in self.drivers_position.items():
            if str(pos).isdigit():
                fantasy_points.ix[driver, 'Fin_Pts'] = max(11 - pos, 0)
            else:
                fantasy_points.ix[driver, 'Fin_Pts'] = 0
        fantasy_points.sort_values(['Team', 'Finish'], ascending=[True, True], inplace=True)
        grouped = fantasy_points[(fantasy_points['Finish'] != 'Ret') & (fantasy_points['Finish'] != 'DNS')].groupby('Team')
        team_points = list(grouped.first()['Finish'])        
        fantasy_points['Team_Pts'] = fantasy_points['Finish'].isin(team_points).apply(lambda x: int(x))
        #fantasy_points['Team_Pts'][fantasy_points['Finish'].isin(team_points)] = 1
        fantasy_points['Team_Pts'].fillna(0, inplace=True)
        fantasy_points['Movement_Pts'] = fantasy_points['Eff_Grid'][fantasy_points['Eff_Grid'].isin(range(23))] -         fantasy_points['Finish'][fantasy_points['Finish'].isin(range(23))]
        fantasy_points['Movement_Pts'].fillna(0, inplace=True)
        fantasy_points['Movement_Pts'] = [min(max(0, x), 10) for x in fantasy_points['Movement_Pts']]
        #fantasy_points['Movement_Pts'][fantasy_points['Movement_Pts'] < 0] = 0
        #fantasy_points['Movement_Pts'][fantasy_points['Movement_Pts'] > 10] = 10
        fantasy_points.ix[self.fastest_lap, 'Fst_Lap'] = 2
        fantasy_points['Fst_Lap'].fillna(0, inplace=True)
        if watch:
            for driver, laps in self.laps_completed.items():
                if int(laps) / self.lap_length >= .9:
                    fantasy_points.ix[driver, 'Completion'] = 3
                elif int(laps) / self.lap_length >= .5:
                    fantasy_points.ix[driver, 'Completion'] = 1
                else:
                    fantasy_points.ix[driver, 'Completion'] = 0
        else:
            for driver, laps in self.laps_completed.items():
                if self.classified[driver]:
                    fantasy_points.ix[driver, 'Completion'] = 3
                elif int(laps) / self.lap_length >= .5:
                    fantasy_points.ix[driver, 'Completion'] = 1
                else:
                    fantasy_points.ix[driver, 'Completion'] = 0
        fantasy_points['Total_Race_Pts'] = fantasy_points['Qual_Pts'] + fantasy_points['Fin_Pts'] + fantasy_points['Team_Pts'] + fantasy_points['Movement_Pts'] + fantasy_points['Completion'] + fantasy_points['Fst_Lap']
        fantasy_points.to_csv('races/' + self.name + '.csv')
        for driver in self.drivers:
            self.fantasy_points[driver] = fantasy_points.ix[driver, 'Total_Race_Pts']
        return fantasy_points
                
    def __repr__(self):
        ordered_position = OrderedDict(sorted(self.drivers_position.items(), key=lambda t: str(t[1])))
        ordered_position = OrderedDict(sorted(ordered_position.items(), key=lambda t: len(str(t[1]))))
        print_string = ''
        for driver, position in ordered_position.items():
            print_string += str(position) + '\t' + driver + '\n'
        return print_string
    
    def update_grid(self, driver, position):
        if driver not in self.drivers:
            driver = conv_DRIVERS[driver]
        if driver in self.drivers:
            self.grid_position[driver] = position
            if list(self.grid_position.values()).count(position) > 1:
                print("WARNING: Two drivers have the same grid position.  Use", self.name + '.update_grid to correct this.')
            self.print_grid()
            #self.push()
        else:
            print(driver, 'is not a valid driver.  See', self.name + '.drivers to see valid names.')
        
    def update_qualifying(self, driver, position):
        if driver in DRIVERS:
            driver = DRIVERS[driver]
        if driver in self.drivers:
            self.qualifying_position[driver] = position
            if list(self.qualifying_position.values()).count(position) > 1:
                print("WARNING: Two drivers have the same qualifying position.  Use", self.name + '.update_qualifying to correct this.')
            self.print_qualifying()
            #self.push()
        else:
            print(driver, 'is not a valid driver.  See', self.name + '.drivers to see valid names.')
        
    def update_race(self, driver, position):
        if driver in DRIVERS:
            driver = DRIVERS[driver]
        if driver in self.drivers:
            self.drivers_position[driver] = position
            if list(self.drivers_position.values()).count(position) > 1:
                print("WARNING: Two drivers have the same finish position.  Use", self.name + '.update_finish to correct this.')
            self.print_race()
            #self.push()
        else:
            print(driver, 'is not a valid driver.  See', self.name + '.drivers to see valid names.')
            
    def print_race(self):
        ordered_position = OrderedDict(sorted(self.drivers_position.items(), key=lambda t: str(t[1])))
        ordered_position = OrderedDict(sorted(ordered_position.items(), key=lambda t: len(str(t[1]))))
        print_string = ''
        for driver, position in ordered_position.items():
            print_string += str(position) + '\t' + driver + '\n'
        print("Pos. \tFinish Results\n" + print_string)
        
    def print_qualifying(self):
        ordered_position = OrderedDict(sorted(self.qualifying_position.items(), key=lambda t: str(t[1])))
        ordered_position = OrderedDict(sorted(ordered_position.items(), key=lambda t: len(str(t[1]))))
        print_string = ''
        for driver, position in ordered_position.items():
            print_string += str(position) + '\t' + driver + '\n'
        print("Pos. \tQualifying\n" + print_string)
        
    def print_grid(self):
        ordered_position = OrderedDict(sorted(self.grid_position.items(), key=lambda t: str(t[1])))
        ordered_position = OrderedDict(sorted(ordered_position.items(), key=lambda t: len(str(t[1]))))
        print_string = ''
        for driver, position in ordered_position.items():
            print_string += str(position) + '\t' + driver + '\n'
        print("Pos. \tGrid Position\n" + print_string)
        
    def push(self):
        #Push results to the Racing CSV
        with open('results/' + self.name + '_Race.csv', 'rt', newline='') as f:
            reader = csv.reader(f)
            lines = []
            for row in reader:
                lines.append(row)
            for line in lines:
                if len(line) >= 7:
                    if line[2] in self.drivers:
                        line[6] = str(self.grid_position[line[2]])
                        line[0] = str(self.drivers_position[line[2]])
        with open('results/' + self.name + '_Race.csv', 'wt', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(lines)
            
        #Push results to the Qualifying CSV
        with open('results/' + self.name + '_Qualifying.csv', 'rt', newline='') as f:
            reader = csv.reader(f)
            lines = []
            for row in reader:
                lines.append(row)
            for line in lines:
                if len(line) >= 8:
                    if line[2] in self.grid_position:
                        line[7] = str(self.grid_position[line[2]])
                    if line[2] in self.qualifying_position:
                        line[0] = str(self.qualifying_position[line[2]])
        with open('results/' + self.name + '_Qualifying.csv', 'wt', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(lines)
    def push_to_season(self, TeamObj):
        #Results have been finalized, append these to the season documents
        with open('Season_Drivers.csv', 'rt', newline='') as f:
            reader = csv.reader(f)
            lines = []
            for row in reader:
                lines.append(row)
        index = RACES.index(self.name)
        last_4_race_sum = 0
        for line in lines[1::]:
            if line[0] not in self.fantasy_points.keys():
                line[index * 2 + 3] = 0
            else:
                line[index * 2 + 3] = self.fantasy_points[line[0]]
            last_4_race_sum += sum(list(map(int, line[max(3, index*2-3):index*2+4:2])))
        #Add costing to the next race column
        if self.name != RACES[-1]:
            for line in lines[1::]:
                prev_scores = list(map(int, line[max(3, index*2-3):index*2+4:2]))
                average_score = sum(prev_scores)/last_4_race_sum*100
                line[index*2 + 4] = max([round(average_score), 1])
                self.drivers_cost[line[0]] = line[max(2, index*2)]
        with open('Season_Drivers.csv', 'wt', newline = '') as f:
            writer = csv.writer(f)
            writer.writerows(lines)
        #Push to Season_Teams.csv
        with open('Season_Teams.csv', 'rt', newline='') as f:
            reader = csv.reader(f)
            lines = []
            for row in reader:
                lines.append(row)
        for row, line in enumerate(lines[1::]):
            player = line[0]
            if (row + 1)%6 > 0 or row == 0:
                driver = TeamObj.teams[player][row%6-1]
                line[index*2 + 1] = driver
                line[index*2 + 2] = self.fantasy_points[driver]
            else:
                line[index*2 + 1] = 'Total:'
                line[index*2 + 2] = sum([self.fantasy_points[driver] for driver in TeamObj.teams[player]]) + TeamObj.validate(player)
        with open('Season_Teams.csv', 'wt', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(lines)

def unpack(row, kind='td'):
    data = row.findall('.//%s' % kind)
    return [val.text_content() for val in data]

def download(race):
    URL = URLs[race]
    parsed = parse(request.urlopen(URL))
    doc = parsed.getroot()
    #Remove superscript tags and their content
    cleaner = Cleaner(kill_tags=['sup'])
    doc = cleaner.clean_html(doc)
    tables = doc.findall('.//table')
    #QUALIFYING
    qualifying_results = tables[1]
    rows = qualifying_results.findall('.//tr')
    #Pull headers and data, then merge them together
    header = [unpack(row, kind='th') for row in rows]
    data = [unpack(row, kind='td') for row in rows]
    for i in range(len(data)):
        for c in range(len(header[i])-1, -1, -1):
            data[i].insert(0, header[i][c])
    for i in range(len(data)):
        for c in range(len(data[i])):
            data[i][c] = data[i][c].strip().replace(',', '')
    #Save Qualfiying results as .csv
    with open('results/' + race + '_Qualifying.csv', 'wt', newline='') as f:
        file = csv.writer(f)
        file.writerows(data)
    #RACE
    race_results = tables[2]
    rows = race_results.findall('.//tr')
    #Pull headers and data, then merge them together
    header = [unpack(row, kind='th') for row in rows]
    data = [unpack(row, kind='td') for row in rows]
    for i in range(len(data)):
        for c in range(len(header[i])-1, -1, -1):
            data[i].insert(0, header[i][c].strip())
    for i in range(len(data)):
        for c in range(len(data[i])):
            data[i][c] = data[i][c].strip().replace(',', '').replace('\r\n', '')
    #Total laps and fastest lap are stored in a metatable, appended to race results
    metatable = tables[0]
    metarows = metatable.findall('.//tr')
    metaheaders = [unpack(row, kind='th') for row in metarows]
    metadata = [unpack(row, kind='td') for row in metarows]
    #Save Race results as .csv
    with open('results/' + race + '_Race.csv', 'wt', newline='') as f:
        file = csv.writer(f)
        file.writerows(data)
        file.writerows([['Total Laps', int(metadata[metaheaders.index(['Distance'])][0].split()[0])]])
        file.writerows([['Fastest Lap', metadata[metaheaders.index(['Fastest lap']) + 1][0].strip()]])

### Command Line work flow ###
if __name__ == '__main__':
    ###Parse Command Line Arguments
    parser = argparse.ArgumentParser(description='Process F1 Races')
    parser.add_argument('direction', type=str)
    parser.add_argument('race', type=str)
    args = parser.parse_args()

    #Validate entries
    if args.direction not in ['push', 'pull']:
        print(args.direction, 'is invalid.  F1 must either push or pull.  See F1.py -h for help.')
        exit()
    if args.race not in RACES:
        print(args.race.capitalize(), 'is an invalid race.  Please select from the following: \n', RACES)
        exit()

    if args.direction == 'pull':
        answer = input('Would you like to download results from Wikipedia? [y/n] ').lower()
        if answer == 'y':
            if os.path.isfile('Results/' + args.race + '_Race.csv'):
                answer = input('File already exists.  Are you sure you want to redownload and overwrite? [y/n] ').lower()
                download(args.race)
                answer = 'n'
            download(args.race)
        if not os.path.isfile('Results/' + args.race + '_Race.csv'):
            print('File is missing.  Try downloading again.')
            exit()
        ThisTeam = Team(args.race)
        print('----TEAMS----')
        print(ThisTeam)
        for team in ThisTeam.teams:
            if ThisTeam.validate(team) < 0:
                print(team + "'s team is overbudget by " + str(ThisTeam.validate(team)) + 'points.')
        answer = input('Would you like to update any of the team members? [y/n] ').lower()
        while answer == 'y':
            update_player = input('Enter your update command and options: \nadd|drop|replace   team   driver   [driver2] \n').split()
            update_player[2] = conv_DRIVERS[update_player[2]]
            if len(update_player) == 4:
                update_player[3] = conv_DRIVERS[update_player[3]]
            if update_player[0].lower() == 'add':
                ThisTeam.add(update_player[1], update_player[2])
            elif update_player[0].lower() == 'drop':
                ThisTeam.drop(update_player[1], update_player[2])
            elif update_player[0].lower() == 'replace':
                if len(update_player) != 4:
                    print('Must enter one team name, one racer to drop, and one racer to add, seperated by spaces.')
                    continue
                ThisTeam.replace(update_player[1], update_player[2], update_player[3])
            else:
                print("Invalid method.  Must use add, drop, or update.")
            print(ThisTeam)
            answer = input('Additional updates? [y/n] ').lower()
        ThisRace = Race(args.race)
        print('\n----QUALIFYING----\n')
        ThisRace.print_qualifying()
        answer = input('Would you like to update any of the qualifying results? [y/n] ').lower()
        while answer == 'y':
            update_qual = input('Enter your driver and position: \ndriver   position\n')
            ThisRace.update_qualifying(update_qual.split()[0], update_qual.split()[1])
            #ThisRace.print_qualifying()
            answer = input('Additional updates? [y/n] ').lower()
        print('\n----GRID POSITIONS----\n')
        ThisRace.print_grid()
        answer = input('Would you like to update any of the grid results? [y/n] ').lower()
        while answer == 'y':
            update_grid = input('Enter your driver and grid position: \ndriver   position\n')
            print(update_grid.split()[0], update_grid.split()[1], update_grid.split()[2])
            print(str(update_grid.split()[0]) + " " + str(update_grid.split()[1]))
            ThisRace.update_grid(str(update_grid.split()[0]) + " " + str(update_grid.split()[1]), update_grid.split()[2])
            #ThisRace.print_grid()
            answer = input('Additional updates? [y/n] ').lower()
        answer = input('Would you like to view the race results? [y/n] ').lower()
        if answer == 'y':
            print('\n----RACE RESULTS----\n')
            ThisRace.print_race()
        answer = input('\nWould you like to update any of the race results? [y/n] ').lower()
        while answer == 'y':
            update_race = input('Enter your driver and grid position: \ndriver   position\n')
            ThisRace.update_race(update_race.split()[0], update_race.split()[1])
            ThisRace.print_race()
            answer = input('Additional updates? [y/n] ').lower()
        answer = input('\nWould you like to save these race results? [y/n] ').lower()
        if answer == 'y':
            ThisRace.score()
        ThisRace.push_to_season(ThisTeam)
        print('Race results were successfully pushed to the season tracking documents.\n')
        answer = input('Would you like to view the season results? [y/n] ').lower()
        if answer == 'y':
            season = [Race(race) for race in RACES[0:max(RACES.index(args.race), 1)]]
            season.append(ThisRace)
            print([race.name for race in season])
            for race in season:
                race.score()
            if args.race == 'Bahrain':
                season_teams = []
                season_teams.append(ThisTeam)
            else:
                season_teams = [Team(team) for team in RACES[1:max(RACES.index(args.race), 1)]]
                season_teams.append(ThisTeam)
            print(season_teams)
            user_num = 'y'
            while user_num != 'stop':
                user_num = input('Please select a graph:\n1. Driver Championship points\n2.  Fantasy Driver points\n3.  Fantasy Team Points\n4.  Driver Ratio Scatter\nOr press q to quit\n')
                if user_num == '1':
                    driver_champ_pts = defaultdict(int)
                    for race in season:
                        for driver, points in race.drivers_points.items():
                            driver_champ_pts[driver] += points
                    sorted_dict = sorted(driver_champ_pts.items(), key=lambda x:x[1], reverse=True)
                    print(sorted_dict)
                    x_pos = np.arange(len(sorted_dict))
                    points = [drivers[1] for drivers in sorted_dict]
                    print(x_pos)
                    print(points)
                    plt.bar(x_pos, points, align='center', alpha=0.7)
                    plt.xticks(x_pos, [x[0] for x in sorted_dict], rotation=90)
                    plt.xlim([-1, len(sorted_dict)])
                    plt.title('Drivers Championship Points')
                    plt.xlabel('Driver')
                    plt.ylabel('Points')
                    plt.show()
                elif user_num == '2':
                    driver_fantasy_pts = defaultdict(int)
                    for race in season:
                        for driver, points in race.fantasy_points.items():
                            driver_fantasy_pts[driver] += points
                    sorted_dict = sorted(driver_fantasy_pts.items(), key=lambda x:x[1], reverse=True)
                    x_pos = np.arange(len(sorted_dict))
                    points = [drivers[1] for drivers in sorted_dict]
                    plt.bar(x_pos, points, align='center', alpha=0.7)
                    plt.xticks(x_pos, [x[0] for x in sorted_dict], rotation=90)
                    plt.xlim([-1, len(sorted_dict)])
                    plt.title('Drivers Fantasy Points')
                    plt.xlabel('Driver')
                    plt.ylabel('Points')
                    plt.show()
                elif user_num == '3':
                    team_points = defaultdict(int)
                    for race_num, race in enumerate(season_teams):
                        for team, drivers in season_teams[race_num].teams.items():
                            for driver in drivers:
                                team_points[team] += season[race_num + 1].fantasy_points[driver]
                                print(team, 'gets', season[race_num + 1].fantasy_points[driver], 'points.')
                                print(team, 'has', team_points[team], 'points total.')
                            team_points[team] += season_teams[race_num].validate(team)
                    sorted_dict = sorted(team_points.items(), key=lambda x:x[1], reverse=True)
                    x_pos = np.arange(len(sorted_dict))
                    points = [x[1] for x in sorted_dict]
                    plt.bar(x_pos, points, align='center', alpha=0.7)
                    plt.xticks(x_pos, [x[0] for x in sorted_dict], rotation=90)
                    plt.xlim([-1, len(sorted_dict)])
                    plt.title('Team Fantasy Points')
                    plt.xlabel('Team')
                    plt.ylabel('Points')
                    plt.show()
                elif user_num == '4':
                    list_driver_fantasy_pts = defaultdict(list)
                    avg_driver_fantasy_pts = {}
                    next_race_cost = {}
                    race_num = RACES.index(season[-1].name)
                    for race in season:
                        for driver, points in race.fantasy_points.items():
                            list_driver_fantasy_pts[driver].append(points)
                    
                    for driver, lst in list_driver_fantasy_pts.items():
                        avg_driver_fantasy_pts[driver] = sum(lst)/len(lst)
                        next_race_cost[driver] = sum(lst[max(0, race_num - 4)::]) / sum([sum(vals[max(0, race_num - 4)::]) for vals in list_driver_fantasy_pts.values()]) * 100 
                    fig, ax = plt.subplots()
                    ax.scatter([next_race_cost[drivers] for drivers in avg_driver_fantasy_pts.keys()], list(avg_driver_fantasy_pts.values()))
                    ax.plot(np.arange(0,12), np.arange(0,12) * 1.5, 'r--', label='Average Ratio')
                    ax.set_title('Ratio of Average Points To Current Cost')
                    ax.set_xlabel('Current Cost')
                    ax.set_ylabel('Average POints')
                    for name, y, x in zip([driver for driver in avg_driver_fantasy_pts.keys()], avg_driver_fantasy_pts.values(), next_race_cost.values()):
                        ax.annotate(name, xy=(x, y), color='blue', ha='center', va='center', xytext=(0,-10), textcoords='offset points')
                    plt.show()
                elif user_num == 'q' or user_num == 'Q':
                    user_num = 'stop'
                else:
                    print('Must enter a number between 1 and 4, or Q to quit.')
            
            