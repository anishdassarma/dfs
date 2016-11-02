from collections import defaultdict
from data.player_dump import print_all_players
from pulp import LpVariable, GLPK, LpProblem, LpMaximize
from pulp import value, LpStatus, lpSum

NHL_CONSTRAINTS = {
    'W': 4,
    'C': 2,
    'D': 2,
    'G': 1,
    'max_salary': 55000
}


NBA_CONSTRAINTS = {
    'PG': 2,
    'SG': 2,
    'SF': 2,
    'PF': 2,
    'C': 1,
    'max_salary': 60000
}


NFL_CONSTRAINTS = {
    'QB': 1,
    'RB': 2,
    'WR': 3,
    'TE': 1,
    'K': 1,
    'D': 1,
    'max_salary': 60000
}


MLB_CONSTRAINTS = {
    'OF': 3,
    '1B': 1,
    '2B': 1,
    '3B': 1,
    'P': 1,
    'SS': 1,
    'C': 1,
    'max_salary': 35000
}


def get_constraints(game):
    return {
        'NBA': NBA_CONSTRAINTS,
        'NHL': NHL_CONSTRAINTS,
        'NFL': NFL_CONSTRAINTS,
        'MLB': MLB_CONSTRAINTS
    }[game]


class TeamCountConstraints(object):

    def __init__(self, teams, count, max=False):
        self.teams = teams
        self.count = int(count)
        self.max = max

    def constraint(self, team_to_players_dict):
        sum_vars = sum(var for team, team_vars in
                       team_to_players_dict.iteritems()
                       for var in team_vars if team in self.teams)
        if self.max:
            return sum_vars <= self.count
        return sum_vars >= self.count


class Optimizer(object):

    def __init__(self, players, constraints=None,
                 team_constraints=list()):
        self.players = players
        if not constraints:
            constraints = MLB_CONSTRAINTS
        self.constraints = constraints
        self.team_constraints = team_constraints

    def __optimize(self, num_solutions=1):
        players_by_key = dict()

        # Formulate variables
        position_variables = defaultdict(list)
        prob = LpProblem("roster", LpMaximize)
        for player in self.players:
            if (not player.name) or (not player.salary) or \
                    (not player.projected_points):
                continue
            players_by_key[player.key] = player
            var = LpVariable(player.key, 0, 1, cat='Integer')

            # Create all binary variables on selection of players
            position_variables[player.position].append(var)

        # Create the constraints on number of players per position
        all_vars = []
        for key, bound in self.constraints.iteritems():
            if key != 'max_salary':
                prob += sum(
                    player_var for player_var in
                    position_variables[key]) == bound
            all_vars.extend(position_variables[key])
        prob += sum([
            variable * float(players_by_key[str(variable)].salary)
            for variable in all_vars]) <= self.constraints['max_salary']

        # No team can have more than 4 players
        # To capture the intuition that we need "stacks", at least two teams
        # must have >= 2 players, or at least one team with >=4 players
        team_to_players_dict = defaultdict(list)
        for variable in all_vars:
            team_to_players_dict[players_by_key[
                str(variable)].team.name].append(variable)
        team_counts = []
        for team, team_vars in team_to_players_dict.iteritems():
            prob += sum([var for var in team_vars]) <= 4
            team_count = LpVariable('{}_count'.format(team),
                                    0, 1000, cat='Integer')
            prob += team_count == sum([var for var in team_vars])
            team_counts.append(team_count)
        for team_constraint in self.team_constraints:
            prob += team_constraint.constraint(team_to_players_dict)
        prob += sum([var for var in all_vars if str(var) == 'DEN_DevontaeBooker']) == 1

        # Add the objective function
        prob += sum([
            variable * float(players_by_key[str(variable)].projected_points)
            for variable in all_vars])

        # Solve the problem
        prob.writeLP('tmp.txt')
        solutions = []
        for i in range(1, num_solutions):
            #GLPK().solve(prob)
            prob.solve()

            # Add this solution to the space of solutions
            selected_players = []
            selected_variables = []
            for v in prob.variables():
                if v.varValue == 1.0 and str(v) in players_by_key:
                    selected_variables.append(v)
                    selected_players.append(players_by_key[str(v)])
            solutions.append((selected_players, value(prob.objective)))

            # Add the constraint that the next solution must be different
            prob += lpSum(selected_variables) <= 7

        # Return all solutions with respective objective function values
        return solutions

    def solve(self, num_solutions=18):
        '''
        Given the players and constraints on number of pitchers, etc.,
        solve the ILP and return optimal solution

        @num_solutions - number of distinct solutions to obtain
        '''
        solutions = self.__optimize(num_solutions)
        solution_number = 1
        for (selected_players, objective_value) in solutions:
            total_salary = sum([player.salary for player in selected_players])
            total_floor = 0
            print "========= SOLUTION {} (VALUE: {}, TOTAL_SALARY: {}, FLOOR_SUM: {}): "\
                "SELECTED PLAYERS ==========".format(
                    solution_number, objective_value, total_salary, total_floor)
            print_all_players(selected_players)
            print " ===================================================== "
            solution_number += 1
