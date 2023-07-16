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
    non_best_scores: list[Score] = field(default_factory=list)
    best_scores: list[Score] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.best_scores)

    def remove_score_index(self, index: int) -> None:
        self.best_scores.pop(index)

    async def find_user_score(
        self,
        user_id: int,
        unrestricted: bool = True,
    ) -> Optional[UserScore]:
        if unrestricted:
            unrestricted_scores = await self.get_unrestricted_scores(user_id)
        else:
            unrestricted_scores = self.best_scores

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
        mods: Optional[int] = None,
    ) -> list[Score]:
        scores = []

        scores_to_check = self.best_scores

        # if we are on the mods leaderboard, we want to include their best score with the mod-combo
        # even if it is not their submitted best
        score_lookup: dict[int, tuple[int, float]] = {}
        if mods is not None:
            scores_to_check = self.best_scores + self.non_best_scores

        for score in scores_to_check:
            user_privileges = await app.usecases.privileges.get_privileges(
                score.user_id,
            )
            if not user_privileges.is_restricted or (
                include_self and score.user_id == user_id
            ):
                if mods is not None and score.mods == mods:
                    (score_idx, user_previous_score_pp) = score_lookup.get(
                        score.user_id,
                        (None, None),
                    )
                    if user_previous_score_pp is None or score_idx is None:
                        scores.append(score)
                        score_lookup[score.user_id] = (scores.index(score), score.pp)
                        continue

                    if user_previous_score_pp > score.pp:
                        continue
                    else:
                        scores.pop(score_idx)

                scores.append(score)
                if score.mods == mods:
                    score_lookup[score.user_id] = (scores.index(score), score.pp)

        return scores

    def remove_user(self, user_id: int) -> None:
        for score in self.best_scores:
            if score.user_id == user_id:
                self.best_scores.remove(score)
                break

    def sort(self) -> None:
        if self.mode > Mode.MANIA:
            sort = lambda score: score.pp
        else:
            sort = lambda score: score.score

        self.best_scores = sorted(self.best_scores, key=sort, reverse=True)

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

    def replace_user_score(self, score: Score) -> None:
        self.remove_user(score.user_id)
        self.best_scores.append(score)
        self.sort()

    def add_submitted_score(self, score: Score) -> None:
        self.non_best_scores.append(score)
