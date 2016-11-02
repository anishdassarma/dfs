from collections import defaultdict
import urllib2
from data.player import Player
from bs4 import BeautifulSoup
from data.team import Team
from extract.rotogrinders import Rotogrinders


class RotogrindersNHL(Rotogrinders):

    @classmethod
    def __create_nhlgoalie_from_roto(cls, goalie_info):
        goalie = Player()

        for child in goalie_info.find_all('a'):
            # Extract the name of the goalie
            if 'class' in child.attrs and \
                    'player-popup' in child.attrs['class']:
                #goalie.name = child.get_text().strip()
                goalie.name = child.get_text().strip()

        for child in goalie_info.find_all('span'):
            if 'class' not in child.attrs:
                continue

            # Projected points
            if 'fpts' in child.attrs['class']:
                projected_points = child.get_text().strip()
                try:
                    goalie.projected_points = float(projected_points)
                except:
                    goalie.projected_points = 0.0

            # Salary
            if 'stats' in child.attrs['class']:
                salary_text = child.get_text().strip()
                salary = cls.find_salary_from_text(salary_text)
                try:
                    goalie.salary = float(salary) * 1000
                except:
                    goalie.salary = Player.DEFAULT_SALARY

            # Position
            goalie.position = 'G'
        return goalie

    @classmethod
    def __create_nhlplayer_from_roto(cls, player_info):
        player = Player()

        for child in player_info.find_all('a'):
            # Extract the name of the player
            if 'class' in child.attrs and \
                    'player-popup' in child.attrs['class']:
                #player.name = child.get_text().strip()
                player.name = child.attrs['title']

        for child in player_info.find_all('span'):
            if 'class' not in child.attrs:
                continue

            # Projected points
            if 'fpts' in child.attrs['class']:
                projected_points = child.get_text().strip()
                try:
                    player.projected_points = float(projected_points)
                except:
                    player.projected_points = 0.0

            # Salary
            if 'salary' in child.attrs['class']:
                salary_text = child.get_text().strip()
                salary = cls.find_salary_from_text(salary_text)
                try:
                    player.salary = float(salary) * 1000
                except:
                    player.salary = Player.DEFAULT_SALARY

            # Position
            if 'position' in child.attrs['class']:
                player.position = RotogrindersNHL.transform_position(
                    child.get_text().strip())
        return player

    @staticmethod
    def transform_position(pos):
        if pos == 'RW' or pos == 'LW':
            return 'W'
        return pos

    @classmethod
    def __get_nhl_players(cls, rotolink):
        html = urllib2.urlopen(rotolink).read()
        soup = BeautifulSoup(html)

        # Teams order
        teams = []
        for team_name in soup.find_all('span', {'class': 'shrt'}):
            teams.append(
                Team(team_name.get_text().strip()))

        team_number = -1
        team_players = defaultdict(set)
        for game_info in soup.find_all('div', {'class': 'blk game'}):

            # Add the road team for this game
            for team_info in game_info.find_all('div',
                                                {'class': 'blk away-team'}):
                team_number += 1
                team = teams[team_number]
                cls.add_team_players(team_info, team_players, team)

            # Add the home team for this game
            for team_info in game_info.find_all('div',
                                                {'class': 'blk home-team'}):
                team_number += 1
                team = teams[team_number]
                cls.add_team_players(team_info, team_players, team)
        return team_players

    @classmethod
    def add_team_players(cls, team_info, team_players, team):

        # Add all non goalie players
        for player_info in team_info.find_all('li'):
            if 'class' in player_info.attrs and\
                    'player' in player_info.attrs['class']:
                player = cls.__create_nhlplayer_from_roto(player_info)
                player.team = team
                team_players[team].add(player)

        # Add the goalie of the team
        for goalie_info in team_info.find_all('div',
                                              {'class': 'pitcher players'}):
            goalie = cls.__create_nhlgoalie_from_roto(goalie_info)
            goalie.team = team
            team_players[team].add(goalie)

    @classmethod
    def get_players_from_link(cls, rotolink, teams=None):
        '''
        Take a link from rotogrinders, and optionally a list of teams to
        consider, and generate a lineup for that set of teams.
        '''
        team_players = cls.__get_nhl_players(rotolink)
        players = set()
        for team, team_players in team_players.iteritems():
            players = players.union(team_players)
        return players
