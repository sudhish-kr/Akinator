from enum import Enum

# Answer weights per TDD v1.1 Section 2.1
ANSWER_WEIGHTS: dict[str, float] = {
    "yes": 1.0,
    "probably_yes": 0.75,
    "dont_know": 0.5,
    "probably_no": 0.25,
    "no": 0.0,
}


class Answer(str, Enum):
    YES = "yes"
    PROBABLY_YES = "probably_yes"
    DONT_KNOW = "dont_know"
    PROBABLY_NO = "probably_no"
    NO = "no"

    @property
    def weight(self) -> float:
        return ANSWER_WEIGHTS[self.value]


ALL_ANSWERS: tuple[Answer, ...] = tuple(Answer)

# Default engine thresholds (overridable via Settings in services layer)
DEFAULT_ELIMINATION_FLOOR = 0.0005
DEFAULT_ELIMINATION_MAGNITUDE = 1000.0
DEFAULT_CONFIDENCE_HIGH = 0.85
DEFAULT_CONFIDENCE_SEPARATION = 0.6
DEFAULT_CONFIDENCE_MARGIN = 0.4
DEFAULT_MAX_QUESTIONS = 25
DEFAULT_IG_TIE_THRESHOLD = 0.001
DEFAULT_CONSECUTIVE_DONT_KNOW_CAP = 5
DEFAULT_NEW_QUESTION_MIN_SAMPLES = 5
DEFAULT_LEARNING_RATE = 0.07
