import re


class Player:
    """Represents a cricket player with batting and bowling stats."""

    def __init__(self, player_id: int, team_id: int, name: str):
        self._id = player_id
        self._team_id = team_id
        self._name = self._validate_name(name)
        # Batting stats
        self._runs = 0
        self._balls = 0
        self._fours = 0
        self._sixes = 0
        self._is_out = False
        # Bowling stats
        self._wickets = 0
        self._balls_bowled = 0
        self._runs_conceded = 0

    @staticmethod
    def _validate_name(name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError("Player name cannot be empty")
        if len(name) > 60:
            raise ValueError("Player name too long")
        return name

    @property
    def id(self): return self._id

    @property
    def team_id(self): return self._team_id

    @property
    def name(self): return self._name

    @property
    def runs(self): return self._runs

    @property
    def balls(self): return self._balls

    @property
    def fours(self): return self._fours

    @property
    def sixes(self): return self._sixes

    @property
    def is_out(self): return self._is_out

    @property
    def wickets(self): return self._wickets

    @property
    def strike_rate(self) -> float:
        if self._balls == 0:
            return 0.0
        return round((self._runs / self._balls) * 100, 2)

    @property
    def economy_rate(self) -> float:
        overs = self._balls_bowled / 6
        if overs == 0:
            return 0.0
        return round(self._runs_conceded / overs, 2)

    def add_runs(self, runs: int):
        if runs < 0:
            raise ValueError("Runs cannot be negative")
        self._runs += runs
        self._balls += 1
        if runs == 4:
            self._fours += 1
        elif runs == 6:
            self._sixes += 1

    def add_dot(self):
        self._balls += 1

    def dismiss(self):
        self._is_out = True
        self._balls += 1

    def add_wicket(self):
        self._wickets += 1

    def bowl_ball(self, runs_conceded: int = 0):
        self._balls_bowled += 1
        self._runs_conceded += runs_conceded

    def __repr__(self):
        return f"<Player id={self._id} name='{self._name}' runs={self._runs} wickets={self._wickets}>"

    def to_dict(self):
        return {
            'id': self._id,
            'team_id': self._team_id,
            'name': self._name,
            'runs': self._runs,
            'balls': self._balls,
            'fours': self._fours,
            'sixes': self._sixes,
            'is_out': self._is_out,
            'wickets': self._wickets,
            'strike_rate': self.strike_rate,
            'economy_rate': self.economy_rate
        }
