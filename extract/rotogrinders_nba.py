from collections import defaultdict
import urllib2
from data.player import Player
from bs4 import BeautifulSoup
from data.team import Team
from extract.rotogrinders import Rotogrinders


class RotogrindersNBA(Rotogrinders):

    @classmethod
    def __create_nbaplayer_from_roto(cls, player_info):
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
                player.position = child.get_text().strip()
        return player

    @classmethod
    def __get_nba_players(cls, rotolink):
        html = urllib2.urlopen(rotolink).read()
        soup = BeautifulSoup(html)

        # Teams order
        teams = []
        for team_name in soup.find_all('span', {'class': 'shrt'}):
            teams.append(
                Team(team_name.get_text().strip()))

        team_number = -1
        team_players = defaultdict(set)
        new_team = True
        team_names = set()
        for player_info in soup.find_all('li'):
            # New teams lineup starting
            if 'class' in player_info.attrs and\
                    'player' in player_info.attrs['class']:
                if new_team:
                    team_number += 1
                    new_team = False
                player = cls.__create_nbaplayer_from_roto(player_info)
                if player.name not in team_names:
                    team_names.add(player.name)
                    player.team = teams[team_number]
                    team_players[teams[team_number]].add(player)
            else:
                if 'Starters' in player_info.contents:
                    new_team = True
                continue

        return team_players

    @classmethod
    def get_players_from_link(cls, rotolink, teams=None):
        '''
        Take a link from rotogrinders, and optionally a list of teams to
        consider, and generate a lineup for that set of teams.
        '''
        team_players = cls.__get_nba_players(rotolink)
        players = set()
        for team, team_players in team_players.iteritems():
            players = players.union(team_players)
        return players
