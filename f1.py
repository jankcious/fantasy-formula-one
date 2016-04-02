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

RACES = ['Australia', 'Malaysia', 'China', 'Bahrain',
         'Spain', 'Monaco', 'Canada', 'Austria',
         'England', 'Hungary', 'Belgium', 'Italy', 
         'Singapore', 'Japan', 'Russia', 'America',
         'Mexico', 'Brazil' , 'Abu dhabi']

DRIVERS = {'Rosberg':'Nico Rosberg', 'Hamilton':'Lewis Hamilton', 'Raikkonen':'Kimi Räikkönen',
           'Perez':'Sergio Pérez', 'Ricciardo':'Daniel Ricciardo', 'Bottas':'Valtteri Bottas',
          'Hulkenberg':'Nico Hülkenberg', 'Massa':'Felipe Massa', 'Kvyat':'Daniil Kvyat', 
          'Sainz':'Carlos Sainz Jr.', 'Verstappen':'Max Verstappen', 'Button':'Jenson Button',
          'Maldonado':'Pastor Maldonado', 'Nasr':'Felipe Nasr', 'Grosjean':'Romain Grosjean',
          'Vettel':'Sebastian Vettel', 'Alonso':'Fernando Alonso', 'Ericsson':'Marcus Ericsson',
          'Stevens':'Will Stevens', 'Merhi':'Roberto Merhi', 'Rossi':'Alexander Rossi',
          'Magnussen':'Kevin Magnussen'}

DRIVERS_short = {}
for short, driver in DRIVERS.items():
    DRIVERS_short[driver] = short

URLs = {'Australia':'https://en.wikipedia.org/wiki/2016_Australian_Grand_Prix',
       'Malaysia':'https://en.wikipedia.org/wiki/2015_Malaysian_Grand_Prix',
       'China':'https://en.wikipedia.org/wiki/2015_Chinese_Grand_Prix',
       'Bahrain':'https://en.wikipedia.org/wiki/2015_Bahrain_Grand_Prix',
       'Spain':'https://en.wikipedia.org/wiki/2015_Spanish_Grand_Prix',
       'Monaco':'https://en.wikipedia.org/wiki/2015_Monaco_Grand_Prix',
       'Canada':'https://en.wikipedia.org/wiki/2015_Canadian_Grand_Prix',
       'Austria':'https://en.wikipedia.org/wiki/2015_Austrian_Grand_Prix',
       'England':'https://en.wikipedia.org/wiki/2015_British_Grand_Prix',
       'Hungary':'https://en.wikipedia.org/wiki/2015_Hungarian_Grand_Prix',
       'Belgium':'https://en.wikipedia.org/wiki/2015_Belgian_Grand_Prix',
       'Italy':'https://en.wikipedia.org/wiki/2015_Italian_Grand_Prix',
       'Singapore':'https://en.wikipedia.org/wiki/2015_Singapore_Grand_Prix',
       'Japan':'https://en.wikipedia.org/wiki/2015_Japanese_Grand_Prix',
       'Russia':'https://en.wikipedia.org/wiki/2015_Russian_Grand_Prix',
       'America':'https://en.wikipedia.org/wiki/2015_United_States_Grand_Prix',
       'Mexico':'https://en.wikipedia.org/wiki/2015_Mexican_Grand_Prix',
       'Brazil':'https://en.wikipedia.org/wiki/2015_Brazilian_Grand_Prix',
       'Abu Dhabi':'https://en.wikipedia.org/wiki/2015_Abu_Dhabi_Grand_Prix',
       }

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
        with open('Teams/team_' + self.name + '.csv', 'rt', newline="\r\n") as f:
            teams = [line.replace('"', '').split(',') for line in f if len(line.split(',')) > 1]
            teams.pop(0) #remove header
        pattern = re.compile('^(.*?)\(')
        for line in range(len(teams)):
            for driver in range(2, len(teams[line])):
                teams[line][driver] = pattern.search(teams[line][driver].strip()).group(1).strip()
        self.teams = {}
        for line in teams:
            self.teams[line[1]] = line[2::]
            
    def drop(self, team, racer):
        if team not in self.teams:
            print(team, 'is not in the league.  Try', self.name + '.teams to see your options.')
            raise
        if DRIVERS[racer] not in self.teams[team]:
            print(racer, 'is not on', team + "'s team.  Try", self.name + '.teams to see the current teams.')
            raise
        self.teams[team].remove(DRIVERS[racer])
        self.push()
        
    def push(self):
        """Push self.teams to the csv"""
        header = [['Player', 'Driver1', 'Driver2', 'Driver3', 'Driver4', 'Driver5']]
        for player in self.teams.keys():
            header.append([player])
            header[header.index([player])].extend(self.teams[player])     
        with open('teams/team_' + self.name + '.csv', 'wt', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerows(header)
        
    def add(self, team, racer):
        if team not in self.teams:
            print(team, 'is not in the league.  Try', self.name + '.teams to see your options.')
            raise
        if len(self.teams[team]) == 5:
            print(team + "'s team already has five drivers.  Consider using .drop or .replace")
        if racer not in DRIVERS:
            print(racer + "is not a valid driver.  Please select from the following:\n", DRIVERS)
        self.teams[team].append(DRIVERS[racer])  
        self.push()
        
    def replace(self, team, drop_racer, add_racer):
        if team not in self.teams:
            print(team, 'is not in the league.  Try', self.name + '.teams to see your options.')
            raise
        if DRIVERS[drop_racer] not in self.teams[team]:
            print(drop_racer, 'is not on', team + "'s team.  Try", self.name + '.teams to see the current teams.')
            raise
        self.teams[team].remove(DRIVERS[drop_racer])
        self.teams[team].append(DRIVERS[add_racer])
        self.push()
        
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
            if driver not in DRIVERS.values():
                driver = DRIVERS[driver]
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
            qualifying_results = [line.split(',') for line in f if len(line.split(',')) > 1]
            qualifying_results.pop(0) #remove header
        with open('Results/' + self.name + '_Race.csv', 'rt', newline='') as f:
            race_results = [line.split(',') for line in f if len(line.split(',')) > 1]
            race_results.pop(0) #remove header
        self.fastest_lap = race_results.pop()[1].strip()
        self.lap_length = race_results.pop()[1].strip()
        self.drivers = {line[2].strip() for line in qualifying_results}
        self.drivers_position = {}
        self.drivers_points = {}
        self.drivers_cost = {}
        self.grid_position = {}
        self.qualifying_position = {}
        self.constructor_finish = {}
        self.drivers_team = {}
        for line in race_results:
            if line[7].strip() == '':
                self.drivers_points[line[2]] = 0
            else:
                self.drivers_points[line[2]] = int(line[7].strip())
            if line[0].isdigit():
                self.drivers_position[line[2]] = int(line[0])
            else:
                self.drivers_position[line[2]] = line[0]
            try:
                self.grid_position[line[2]] = int(line[6])
            except:
                self.grid_position[line[2]] = max(self.grid_position.values()) + 1
            if line[3].strip() not in self.constructor_finish and line[0].strip().isdigit():
                self.constructor_finish[line[3]] = [int(line[0])]
            elif line[0].strip().isdigit():
                self.constructor_finish[line[3]].append(int(line[0]))
            else:
                self.constructor_finish[line[3]] = [0]
            self.drivers_team[line[2]] = line[3]
        for line in qualifying_results:
            try:
                self.qualifying_position[line[2]] = int(line[0])
            except:
                self.qualifying_position[line[2]] = "DNF"
        self.fantasy_points = {}
        for line in race_results:
            driver = line[2]
            #Award points for finishing in the top 10
            self.fantasy_points[driver] = Fantasy_Finish_Points_Dict[self.drivers_position[driver]]
            #Award points for completing the race
            if int(line[4])/int(self.lap_length) > .9:
                self.fantasy_points[driver] += 3
            elif int(line[4])/int(self.lap_length) > .5:
                self.fantasy_points[driver] += 1
        for driver in self.fantasy_points:
            #Award bonus point for being the fastest on the team
            if self.drivers_position[driver] == min(self.constructor_finish[self.drivers_team[driver]]):
                self.fantasy_points[driver] += 1
            #Award movement bonus points
            if type(self.drivers_position[driver]) == int and type(self.grid_position[driver]) == int:
                if self.grid_position[driver] > self.drivers_position[driver] and self.drivers_position[driver] <= 10:
                    self.fantasy_points[driver] += min(self.grid_position[driver] - self.drivers_position[driver], 10)
        for line in qualifying_results:
            driver = line[2]
            if line[0].isdigit():
                if int(line[0]) == 1:
                    self.fantasy_points[driver] += 3
                elif int(line[0]) <= 10:
                    self.fantasy_points[driver] += 2
                elif int(line[0]) <= 15:
                    self.fantasy_points[driver] += 1
                
    def __repr__(self):
        ordered_position = OrderedDict(sorted(self.drivers_position.items(), key=lambda t: str(t[1])))
        ordered_position = OrderedDict(sorted(ordered_position.items(), key=lambda t: len(str(t[1]))))
        print_string = ''
        for driver, position in ordered_position.items():
            print_string += str(position) + '\t' + driver + '\n'
        return print_string
    
    def update_grid(self, driver, position):
        if driver in DRIVERS:
            driver = DRIVERS[driver]
        if driver in self.drivers:
            self.grid_position[driver] = position
            if list(self.grid_position.values()).count(position) > 1:
                print("WARNING: Two drivers have the same grid position.  Use", self.name + '.update_grid to correct this.')
            self.print_grid()
            self.push()
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
            self.push()
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
            self.push()
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
            update_player = input('Enter your update command and options: \nadd|drop|replace   team driver   [driver2] \n')
            if update_player.split()[0].lower() == 'add':
                ThisTeam.add(update_player.split()[1], update_player.split()[2])
            elif update_player.split()[0].lower() == 'drop':
                ThisTeam.drop(update_player.split()[1], update_player.split()[2])
            elif update_player.split()[0].lower() == 'replace':
                if len(update_player.split()) != 4:
                    print('Must enter one team name, one racer to drop, and one racer to add, seperated by spaces.')
                    continue
                ThisTeam.replace(update_player.split()[1], update_player.split()[2], update_player.split()[3])
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
            ThisRace.update_grid(update_grid.split()[0], update_grid.split()[1])
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

    if args.direction == 'push':
        This_Race = Race(args.race)
        This_Team = Team(args.race)
        This_Race.push_to_season(This_Team)
        print('Race results were successfully pushed to the season tracking documents.\n')
        answer = input('Would you like to view the season results? [y/n] ').lower()
        if answer == 'y':
            season = [Race(race) for race in RACES[0:max(RACES.index(args.race) - 1, 1)]]
            season.append(This_Race)
            season_teams = [Team(team) for team in RACES[0:max(RACES.index(args.race) - 1, 1)]]
            season_teams.append(This_Team)
            user_num = 'y'
            while user_num != 'stop':
                user_num = input('Please select a graph:\n1. Driver Championship points\n2.  Fantasy Driver points\n3.  Fantasy Team Points\n4.  Driver Ratio Scatter\nOr press q to quit\n')
                if user_num == '1':
                    driver_champ_pts = defaultdict(int)
                    for race in season:
                        for driver, points in race.drivers_points.items():
                            driver_champ_pts[driver] += points
                    sorted_dict = sorted(driver_champ_pts.items(), key=lambda x:x[1], reverse=True)
                    x_pos = np.arange(len(sorted_dict))
                    points = [drivers[1] for drivers in sorted_dict]
                    plt.bar(x_pos, points, align='center', alpha=0.7)
                    plt.xticks(x_pos, [x[0] for x in sorted_dict], rotation=45)
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
                    plt.xticks(x_pos, [x[0] for x in sorted_dict], rotation=45)
                    plt.xlim([-1, len(sorted_dict)])
                    plt.title('Drivers Fantasy Points')
                    plt.xlabel('Driver')
                    plt.ylabel('Points')
                    plt.show()
                elif user_num == '3':
                    team_points = defaultdict(int)
                    for race_num, race in enumerate(season):
                        for team, drivers in season_teams[race_num].teams.items():
                            for driver in drivers:
                                team_points[team] += race.fantasy_points[driver]
                    sorted_dict = sorted(team_points.items(), key=lambda x:x[1], reverse=True)
                    x_pos = np.arange(len(sorted_dict))
                    points = [x[1] for x in sorted_dict]
                    plt.bar(x_pos, points, align='center', alpha=0.7)
                    plt.xticks(x_pos, [x[0] for x in sorted_dict], rotation=45)
                    plt.xlim([-1, len(sorted_dict)])
                    plt.title('Team Fantasy Points')
                    plt.xlabel('Team')
                    plt.ylabel('Points')
                    plt.show()
                elif user_num == '4':
                    list_driver_fantasy_pts = {}
                    avg_driver_fantasy_pts = {}
                    for race in season:
                        for driver, points in race.fantasy_points.items():
                            if driver not in list_driver_fantasy_pts:
                                list_driver_fantasy_pts[driver] = [points]
                            else:
                                list_driver_fantasy_pts[driver].append(points)
                    for driver, lst in list_driver_fantasy_pts.items():
                        if driver in season[-1].drivers_cost:
                            avg_driver_fantasy_pts[driver] = sum(lst)/len(lst)
                            #avg_driver_fantasy_pts[driver].append(season[-1].drivers_cost[driver])
                    fig, ax = plt.subplots()
                    print([driver for driver in avg_driver_fantasy_pts.keys()])
                    print(season[-1].drivers_cost)
                    ax.scatter([float(season[-1].drivers_cost[driver]) for driver in avg_driver_fantasy_pts.keys()], list(avg_driver_fantasy_pts.values()))
                    ax.plot(np.arange(0,12), np.arange(0,12) * 1.5, 'r--', label='Average Ratio')
                    ax.set_title('Ratio of Average Points To Current Cost')
                    ax.set_xlabel('Current Cost')
                    ax.set_ylabel('Ratio')
                    for name, y, x in zip([DRIVERS_short[driver] for driver in avg_driver_fantasy_pts.keys()], avg_driver_fantasy_pts.values(), [float(season[-1].drivers_cost[driver]) for driver in avg_driver_fantasy_pts.keys()]):
                        ax.annotate(name, xy=(x, y), color='blue', ha='center', va='center', xytext=(0,-10), textcoords='offset points')
                    plt.show()
                elif user_num == 'q' or user_num == 'Q':
                    user_num = 'stop'
                else:
                    print('Must enter a number between 1 and 4, or Q to quit.')
            
            