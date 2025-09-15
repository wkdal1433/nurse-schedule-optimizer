"""
Value Object: ExperienceLevel
경력 수준 값 객체
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ExperienceLevel:
    """경력 수준 값 객체 - 불변 객체"""

    years: int
    skill_level: int  # 1-5 점수

    def __post_init__(self):
        if self.years < 0:
            raise ValueError("경력 연수는 0 이상이어야 합니다")
        if not (1 <= self.skill_level <= 5):
            raise ValueError("숙련도는 1-5 사이여야 합니다")

    @classmethod
    def from_years(cls, years: int) -> "ExperienceLevel":
        """경력 연수로부터 숙련도 자동 계산"""
        if years < 1:
            skill_level = 1
        elif years < 3:
            skill_level = 2
        elif years < 5:
            skill_level = 3
        elif years < 10:
            skill_level = 4
        else:
            skill_level = 5

        return cls(years=years, skill_level=skill_level)

    @property
    def is_junior(self) -> bool:
        return self.years < 2

    @property
    def is_senior(self) -> bool:
        return self.years >= 5

    def __str__(self) -> str:
        return f"{self.years}년차 (숙련도: {self.skill_level})"