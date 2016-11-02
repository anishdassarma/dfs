class Team():
    def __init__(self, name, game_time=None, opp=None,
                 line=None, moneyline=None, over_under=None,
                 projected_points=None, projections_change=None):
        self.name = name
        self.game_time = game_time
        self.opp = opp
        self.line = line
        self.moneyline = moneyline
        self.over_under = over_under
        self.projected_points = projected_points
        self.projections_change = projections_change

    def __str__(self):
        return self.name
