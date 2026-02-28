from datetime import datetime
from typing import Optional


class Match:
    """Manages cricket match logic, scoring and state."""

    VALID_EVENTS = {'0', '1', '2', '3', '4', '6', 'wicket', 'wide', 'no_ball'}

    def __init__(self, match_id: int, team1: str, team2: str, overs: int, fmt: str = 'real'):
        if overs < 1 or overs > 50:
            raise ValueError("Overs must be between 1 and 50")
        self._id = match_id
        self._team1 = team1
        self._team2 = team2
        self._overs = overs
        self._format = fmt
        self._player_count = 11 if fmt == 'real' else 9
        self._innings = 1
        self._result = 'In Progress'
        self._created_at = datetime.now()

        # Innings scores
        self._team1_score = 0
        self._team1_wickets = 0
        self._team1_balls = 0
        self._team2_score = 0
        self._team2_wickets = 0
        self._team2_balls = 0

        # Extras
        self._wides = 0
        self._no_balls = 0
        self._extras = 0

        # Target
        self._target = 0

    @property
    def id(self): return self._id

    @property
    def innings(self): return self._innings

    @property
    def result(self): return self._result

    @property
    def overs(self): return self._overs

    @property
    def target(self): return self._target

    @property
    def current_score(self):
        if self._innings == 1:
            return self._team1_score, self._team1_wickets, self._team1_balls
        return self._team2_score, self._team2_wickets, self._team2_balls

    @property
    def max_balls(self):
        return self._overs * 6

    def run_rate(self) -> float:
        score, _, balls = self.current_score
        if balls == 0:
            return 0.0
        return round(score / (balls / 6), 2)

    def required_run_rate(self) -> float:
        """Calculate required run rate in 2nd innings."""
        if self._innings != 2:
            return 0.0
        balls_remaining = self.max_balls - self._team2_balls
        runs_needed = self._target - self._team2_score
        if balls_remaining <= 0:
            return 0.0
        overs_remaining = balls_remaining / 6
        return round(runs_needed / overs_remaining, 2)

    def process_event(self, event_type: str) -> dict:
        """Process a ball event and return updated state."""
        if event_type not in self.VALID_EVENTS:
            raise ValueError(f"Invalid event type: {event_type}")
        if self._result != 'In Progress':
            raise ValueError("Match is already complete")

        result = {
            'event': event_type,
            'ball_counted': True,
            'runs_scored': 0,
            'innings_ended': False,
            'match_ended': False
        }

        if event_type == 'wide':
            self._add_runs(1)
            self._wides += 1
            self._extras += 1
            result['ball_counted'] = False
            result['runs_scored'] = 1
        elif event_type == 'no_ball':
            self._add_runs(1)
            self._no_balls += 1
            self._extras += 1
            result['ball_counted'] = False
            result['runs_scored'] = 1
        elif event_type == 'wicket':
            self._add_wicket()
            self._add_balls()
        else:
            runs = int(event_type)
            self._add_runs(runs)
            self._add_balls()
            result['runs_scored'] = runs

        # Check innings end
        score, wickets, balls = self.current_score
        innings_ended = (balls >= self.max_balls or wickets >= self._player_count - 1)

        if innings_ended:
            result['innings_ended'] = True
            if self._innings == 1:
                self._target = score + 1
                self._innings = 2
            else:
                result['match_ended'] = True
                result['result'] = self._determine_winner()
                self._result = result['result']

        # Check if chasing team wins
        if self._innings == 2 and self._team2_score > self._team1_score:
            result['innings_ended'] = True
            result['match_ended'] = True
            result['result'] = self._determine_winner()
            self._result = result['result']

        result.update({'run_rate': self.run_rate(), 'innings': self._innings})
        return result

    def _add_runs(self, runs: int):
        if self._innings == 1:
            self._team1_score += runs
        else:
            self._team2_score += runs

    def _add_wicket(self):
        if self._innings == 1:
            self._team1_wickets += 1
        else:
            self._team2_wickets += 1

    def _add_balls(self):
        if self._innings == 1:
            self._team1_balls += 1
        else:
            self._team2_balls += 1

    def _determine_winner(self) -> str:
        if self._team2_score > self._team1_score:
            wl = (self._player_count - 1) - self._team2_wickets
            return f"{self._team2} won by {wl} wickets"
        elif self._team2_score == self._team1_score:
            return "Match Tied"
        else:
            diff = self._team1_score - self._team2_score
            return f"{self._team1} won by {diff} runs"

    def __repr__(self):
        return f"<Match id={self._id} {self._team1} vs {self._team2} innings={self._innings}>"

    def to_dict(self):
        score, wickets, balls = self.current_score
        return {
            'id': self._id,
            'team1': self._team1,
            'team2': self._team2,
            'overs': self._overs,
            'format': self._format,
            'innings': self._innings,
            'score': score,
            'wickets': wickets,
            'balls': balls,
            'overs_display': f"{balls // 6}.{balls % 6}",
            'run_rate': self.run_rate(),
            'extras': self._extras,
            'wides': self._wides,
            'no_balls': self._no_balls,
            'target': self._target,
            'result': self._result,
            'created_at': self._created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
