from collections import defaultdict
import urllib2
from data.player import Player
from bs4 import BeautifulSoup
from data.team import Team


class RotogrindersMLB():

    @staticmethod
    def __get_salary_from_element(element):
        salary_str = element.attrs.get('data-salary')
        if not salary_str:
            salary_str = element.get_text()
        salary = salary_str.strip().replace(
            '$', '').replace('K', '')
        try:
            return float(salary) * 1000
        except:
            return Player.DEFAULT_SALARY * 1000

    @staticmethod
    def __create_pitcher_from_roto(pitcher_info):
        player = Player()

        for child in pitcher_info.find_all('a'):
            # Extract the name of the player
            if 'player-popup' in child.attrs['class']:
                player.name = child.get_text().strip()

        for child in pitcher_info.find_all('span'):
            # Handedness
            if 'stats' in child.attrs['class']:
                player.handedness = child.get_text().strip()

            # Projected points
            if 'fpts' in child.attrs['class']:
                projected_points = child.get_text().strip()
                try:
                    player.projected_points = float(projected_points)
                except:
                    player.projected_points = 0.0

        salary = RotogrindersMLB.find_salary_from_text(
            ' '.join([str(x) for x in pitcher_info.contents]))
        try:
            player.salary = float(salary) * 1000
        except:
            player.salary = Player.DEFAULT_SALARY
        player.position = 'P'  # Pitcher
        return player

    @staticmethod
    def __create_mlb_player_from_roto_player_info(player_info):
        player = Player()
        for child in player_info.find_all('span'):

            # Extract the name of the player
            if 'pname' in child.attrs['class']:
                player.name = child.get_text().strip()

            # Data hand and opposing pitcher hand
            if 'data-hand' in child.attrs:
                player.handedness = child.attrs.get('data-hand').strip()
                player.opp_hand = child.attrs.get(
                    'data-opp-pitcher-hand').strip()

            # Extract the position
            if 'position' in child.attrs['class']:
                player.position = child.get_text().strip().replace('SP', 'P')

            # Salary
            if 'data-salary' in child.attrs:
                player.salary = RotogrindersMLB.__get_salary_from_element(
                    child)

            # Projected points
            if 'fpts' in child.attrs['class']:
                projected_points = child.get_text().strip()
                try:
                    player.projected_points = float(projected_points)
                except:
                    player.projected_points = 0.0

        return player

    @staticmethod
    def __get_batters_and_pitchers(rotolink):
        html = urllib2.urlopen(rotolink).read()
        soup = BeautifulSoup(html)

        # Teams order
        teams = []
        for team_mascot in soup.find_all('span', {'class': 'shrt'}):
            teams.append(
                Team(team_mascot.get_text().strip()))

        team_number = -1
        lineup_order = 0
        team_batters = defaultdict(set)
        team_pitchers = defaultdict(set)
        for player_info in soup.find_all('div'):
            if 'pitcher' in (player_info.attrs.get('class') or []):
                # New teams lineup starting
                lineup_order = 0
                team_number += 1
                pitcher = RotogrindersMLB.__create_pitcher_from_roto(
                    player_info)
                pitcher.team = teams[team_number]
                team_pitchers[teams[team_number]].add(pitcher)

            if 'info' in (player_info.attrs.get('class') or []):
                lineup_order += 1
                # TODO: (1) Swith team when new team list starts; (2) keep
                # track of player position when adding players
                player = RotogrindersMLB.\
                    __create_mlb_player_from_roto_player_info(player_info)
                player.team = teams[team_number]
                player.lineup_order = lineup_order
                team_batters[teams[team_number]].add(player)

        return team_batters, team_pitchers

    @staticmethod
    def __union_players(team_batters, team_pitchers):
        players = set()
        added_players = set()
        team_players = set()

        # Add all batters
        for team, batters in team_batters.iteritems():
            for batter in batters:
                team_player = u'{}{}'.format(team.name, batter.name)
                if team_player not in team_players:
                    team_players.add(team_player)
                    players.add(batter)
                    added_players.add(batter.key)

        # Add all pitchers that haven't already been added
        for team, pitchers in team_pitchers.iteritems():
            for pitcher in pitchers:
                if pitcher.key not in added_players:
                    players.add(pitcher)
        return players

    @staticmethod
    def get_players_from_link(rotolink, teams=None):
        '''
        Take a link from rotogrinders, and optionally a list of teams to
        consider, and generate a lineup for that set of teams.
        '''
        team_batters, team_pitchers = \
            RotogrindersMLB.__get_batters_and_pitchers(rotolink)
        players = RotogrindersMLB.__union_players(team_batters, team_pitchers)
        return players
