import re
from datetime import datetime


class Team:
    """Represents a cricket team with players."""

    def __init__(self, team_id: int, name: str, player_count: int = 11):
        self._id = team_id
        self._name = self._validate_name(name)
        self._player_count = player_count
        self._players = []
        self._created_at = datetime.now()

    @staticmethod
    def _validate_name(name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError("Team name cannot be empty")
        if len(name) > 50:
            raise ValueError("Team name too long (max 50 characters)")
        if not re.match(r'^[A-Za-z0-9 _\-\.]+$', name):
            raise ValueError(f"Invalid team name: '{name}'")
        return name

    @property
    def id(self): return self._id

    @property
    def name(self): return self._name

    @property
    def player_count(self): return self._player_count

    @property
    def players(self): return list(self._players)

    def add_player(self, player):
        if len(self._players) >= self._player_count:
            raise ValueError(f"Team already has {self._player_count} players")
        self._players.append(player)

    def get_active_batsmen(self):
        return [p for p in self._players if not p.is_out]

    def get_total_runs(self):
        return sum(p.runs for p in self._players)

    def __repr__(self):
        return f"<Team id={self._id} name='{self._name}' players={len(self._players)}>"

    def to_dict(self):
        return {
            'id': self._id,
            'name': self._name,
            'player_count': self._player_count,
            'players': [p.to_dict() for p in self._players],
            'total_runs': self.get_total_runs()
        }
