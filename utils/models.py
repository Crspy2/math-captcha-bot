from dataclasses import dataclass

@dataclass
class VerificationData:
    answer: int
    pattern_file: str
    polynomial: str
    attempts: int = 0