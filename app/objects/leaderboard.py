from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import TYPE_CHECKING
from typing import TypedDict
from typing import Union

from app.constants.mode import Mode

if TYPE_CHECKING:
    from app.models.score import Score

import app.usecases


class UserScore(TypedDict):
    score: Score
    rank: int


@dataclass
class Leaderboard:
    mode: Mode
    scores: list[Score] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.scores)

    def remove_score_index(self, index: int) -> None:
        self.scores.pop(index)

    async def find_user_score(
        self,
        user_id: int,
        unrestricted: bool = True,
    ) -> Optional[UserScore]:
        if unrestricted:
            unrestricted_scores = await self.get_unrestricted_scores(user_id)
        else:
            unrestricted_scores = self.scores

        for idx, score in enumerate(unrestricted_scores):
            if score.user_id == user_id:
                return {
                    "score": score,
                    "rank": idx + 1,
                }

    async def find_score_rank(self, user_id: int, score_id: int) -> int:
        unrestricted_scores = await self.get_unrestricted_scores(user_id)

        for idx, score in enumerate(unrestricted_scores):
            if score.id == score_id:
                return idx + 1

        return 0

    async def get_unrestricted_scores(
        self,
        user_id: int,
        include_self: bool = True,
    ) -> list[Score]:
        scores = []

        for score in self.scores:
            user_privilege = await app.usecases.privileges.get_privilege(score.user_id)
            if user_privilege.is_restricted and not (
                score.user_id == user_id and include_self
            ):
                continue

            scores.append(score)

        return scores

    async def remove_user(self, user_id: int) -> None:
        result = await self.find_user_score(user_id, unrestricted=False)

        if result is not None:
            self.scores.remove(result["score"])

    def sort(self) -> None:
        if self.mode > Mode.MANIA:
            sort = lambda score: score.pp
        else:
            sort = lambda score: score.score

        self.scores = sorted(self.scores, key=sort, reverse=True)

    async def whatif_placement(
        self,
        user_id: int,
        sort_value: Union[int, float],
    ) -> int:
        unrestricted_scores = await self.get_unrestricted_scores(user_id)

        for idx, score in enumerate(unrestricted_scores):
            if self.mode > Mode.MANIA:
                sort_key = score.pp
            else:
                sort_key = score.score

            if sort_value > sort_key:
                return idx + 1

        return 1

    async def add_score(self, score: Score) -> None:
        await self.remove_user(score.user_id)

        self.scores.append(score)
        self.sort()

    def scores_list(self) -> list[dict]:
        return [score.db_dict for score in self.scores]
