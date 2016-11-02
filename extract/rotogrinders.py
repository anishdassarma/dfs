from data.player import Player
from data.team import Team


class Rotogrinders():

    @classmethod
    def find_salary_from_text(cls, text_nodes):
        for text in text_nodes.split(' '):
            text = text.strip()
            if text.startswith('$') and text.endswith('K'):
                return float(text[1:-1])
        # Make the price too high as default so not selected
        return Player.DEFAULT_SALARY

    @staticmethod
    def all_players_from_roto_file(fname, SEP=','):
        players = []
        with open(fname) as f:
            for l in f:
                if l.startswith('#'):
                    continue
                parts = l.strip().split(SEP)
                player = Player()
                player.name = parts[0]
                player.team = Team(parts[1])
                player.salary = float(parts[2]) if \
                    parts[2] and parts[2] != 'None' else Player.DEFAULT_SALARY
                player.projected_points = float(parts[4]) if parts[4] and\
                    parts[4] != 'None' else 0.0
                if not player.salary:
                    continue
                player.value = player.projected_points / player.salary
                player.position = parts[3]
                players.append(player)
        return players
