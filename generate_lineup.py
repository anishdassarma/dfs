import sys

from data.player import Player
from data.team import Team
from optimizer.optimizer import Optimizer
from optimizer.optimizer import get_constraints
from extract.rotogrinders import Rotogrinders
from extract.rotogrinders_nba import RotogrindersNBA
from extract.rotogrinders_nhl import RotogrindersNHL
from extract.rotogrinders_nfl import RotogrindersNFL
from extract.rotogrinders_mlb import RotogrindersMLB
from extract.rotogrinders_schedule import load_teams
from data.player_dump import print_all_players
from optimizer.optimizer import TeamCountConstraints



ROTO_FORMAT = 'roto_format'
SABER_FORMAT = 'saber_format'


class GameType(object):
    CASH = 'cash'
    GPP = 'gpp'


def __all_players_from_file(fname,
                            file_format=SABER_FORMAT,
                            game_type=GameType.CASH,
                            SEP=','):
    assert file_format in [ROTO_FORMAT, SABER_FORMAT]
    if file_format == SABER_FORMAT:
        return __all_players_from_saber_file(fname, game_type)
    return Rotogrinders.all_players_from_roto_file(fname, SEP)


def __all_players_from_saber_file(fname, game_type):
    players = []
    with open(fname) as f:
        for l in f:
            if l.startswith('#'):
                continue
            parts = l.strip().split(',')
            player = Player()
            player.name = parts[0]
            player.team = Team(parts[1])

            # Player salary
            player.salary = float(parts[2]) if \
                parts[2] and parts[2] != 'None' else Player.DEFAULT_SALARY
            if not player.salary:
                continue

            # Player position
            player.position = parts[3]

            # Player point projections
            try:
                player.floor_projection = float(parts[4])
                player.ceiling_projection = float(parts[5])
            except:
                continue

            # If gpp lineup take the ceiling projection else take floor
            # projection
            assert game_type in [GameType.CASH, GameType.GPP]
            if game_type == GameType.CASH:
                player.projected_points = player.floor_projection
            else:
                player.projected_points = player.ceiling_projection

            player.value = player.projected_points / player.salary
            players.append(player)
    return players


def restrict_players_to_teams(players,
                              teams=None, excludedteams=None):
    '''
    Take a set of players and set of teams, and restrict players to only those
    teams.
    '''
    return [
        player for player in players
        if (
            (teams is None or player.team.name in teams) and
            (player.team.name not in (excludedteams or []))
        )
    ]


def __team_acronmy_expansion(teams):
    if teams is None:
        return None
    equivalences = [
        ['KAN', 'KC'],
        ['WSH', 'WAS'],
        ['LOS', 'LAD'],
        ['TAM', 'TB', 'TBR'],
        ['SDP', 'SD'],
        ['SFG', 'SF'],
        ['GB', 'GBP'],
        ['KC', 'KCC'],
        ['TB', 'TBB'],
        ['SD', 'SDC'],
        ['SF', 'SFO'],
        ['NO', 'NOS'],
        ['NE', 'NEP'],
        ['SA', 'SAS'],
        ['GS', 'GSW'],
        ['LA', 'LAK'],
        ['LA', 'LAR'],
        ['STL'],
    ]
    output_teams = set(teams.keys())
    for equiv in equivalences:
        for team in equiv:
            if team in teams:
                for eq_team in equiv:
                    teams[eq_team] = teams[team]
                output_teams = output_teams.union(set(equiv))
                break
    assert output_teams == set(teams)
    return teams


def __search_arg(args, arg):
    for i in range(len(args) - 1):
        if args[i] == '--' + arg:
            yield args[i + 1]


def __get_teams_to_use(teams_dict, args):
    teams = []
    for only_arg in __search_arg(args, 'only'):
            if only_arg.lower() == 'none':
                return None
            teams.extend(only_arg.split(','))
    if teams:
        if teams_dict:
            teams_dict = {team: teams_dict[team] for team in teams}
        else:
            teams_dict = {team: Team(team) for team in teams}
    return teams_dict


def __get_teams_to_exclude(teams_dict, args):
    teams = []
    for excl_arg in __search_arg(args, 'excl'):
        teams.extend(excl_arg.split(','))
    if teams:
        if teams_dict:
            teams_dict = {team: teams_dict[team] for team in teams}
        else:
            teams_dict = {team: Team(team) for team in teams}
        return teams_dict
    return None


def __get_team_constraints(args):
    constraints = []
    for max_arg in __search_arg(args, 'max'):
        teams, count = max_arg.split(':')
        constraints.append(TeamCountConstraints(teams.split(','), count, max=True))
    for min_arg in __search_arg(args, 'min'):
        teams, count = min_arg.split(':')
        constraints.append(TeamCountConstraints(teams.split(','), count))
    return constraints


def __use_players(args):
    players = list()
    for fade_arg in __search_arg(args, 'use'):
        players.extend(fade_arg)
    return players


def __fade_players(args):
    players = list()
    for fade_arg in __search_arg(args, 'fade'):
        players.extend(fade_arg)
    return players


if __name__ == "__main__":
    # Get Players from rotolink
    game = 'NBA'

    args = []

    if len(sys.argv) > 1:
        if sys.argv[1].startswith('-'):
            args = sys.argv[1:]
        else:
            args = sys.argv[2:]
            game = sys.argv[1].upper()

    numberfire = "https://www.numberfire.com/nba/fantasy/'\
        'full-fantasy-basketball-projections"
    rotolink = 'https://rotogrinders.com/lineups/{}?site=fanduel'.format(
        game.lower())
    if game == 'NHL':
        func = RotogrindersNHL.get_players_from_link
    elif game == 'NBA':
        func = RotogrindersNBA.get_players_from_link
    elif game == 'MLB':
        func = RotogrindersMLB.get_players_from_link
    elif game == 'NFL':
        func = RotogrindersNFL.get_players_from_link
    else:
        raise "Error. Game not supported"

    SEP = ','

    players = func(rotolink)
    '''
    players = __all_players_from_file(
        'nhl.txt', ROTO_FORMAT,
        SEP=SEP
    )
    '''
    #print_all_players(players, SEP=SEP)

    # Get all the teams that will be used today
    teams_dict = load_teams(game, args)
    teams = __team_acronmy_expansion(__get_teams_to_use(teams_dict, args))
    exclude_teams = __team_acronmy_expansion(__get_teams_to_exclude(teams_dict, args))
    team_constraints = __get_team_constraints(args)

    # Restrict players to required set of teams
    restricted_players = restrict_players_to_teams(
        players, teams, exclude_teams)

    print " ================================================== "
    Optimizer(restricted_players, constraints=get_constraints(game), team_constraints=team_constraints).solve(
        num_solutions=5)
