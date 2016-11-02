class Player():
    DEFAULT_SALARY = 10

    def __init__(self):
        self.name = None
        self.team = None
        self.position = None
        self.handedness = None
        self.opp_hand = None  # This should be should be in opp team
        self.salary = None
        self.floor_projection = None
        self.ceiling_projection = None
        self.projected_points = None
        self.lineup_order = None

    @property
    def key(self):
        return ''.join(c for c in '{}_{}'.format(self.team, self.name)
                       if c.isalpha() or c == '_')

    def __str__(self):
        return '{}. {}({}, {}, {}): '\
            'proj_score; {}, hand: {}, opp_hand: {}'.format(
                str(self.lineup_order),
                str(self.name),
                str(self.salary),
                str(self.position),
                str(self.team),
                str(self.projected_points),
                str(self.handedness),
                str(self.opp_hand),
            )
