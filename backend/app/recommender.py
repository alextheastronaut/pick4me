from dataclasses import dataclass, field

from app.models import MenuItem, MenuItemTag, Tag
from app.quiz_config import ANSWER_EFFECTS


@dataclass
class TagInfo:
    key: str
    display_name: str
    weight: float


@dataclass
class ItemWithTags:
    item: MenuItem
    tags: list[TagInfo] = field(default_factory=list)


@dataclass
class ScoredItem:
    item: MenuItem
    score: float
    reasons: list[str]


def _collect_effects(quiz_answers: dict[str, str]) -> tuple[set[str], set[str]]:
    boost: set[str] = set()
    exclude: set[str] = set()
    for question_key, answer_key in quiz_answers.items():
        effects = ANSWER_EFFECTS.get(question_key, {}).get(answer_key, {})
        boost.update(effects.get("boost", []))
        exclude.update(effects.get("exclude", []))
    return boost, exclude


def recommend(items_with_tags: list[ItemWithTags], quiz_answers: dict[str, str], n: int = 4) -> list[ScoredItem]:
    boost_tags, exclude_tags = _collect_effects(quiz_answers)

    scored: list[ScoredItem] = []
    for entry in items_with_tags:
        item = entry.item
        item_tag_keys = {t.key for t in entry.tags}

        if item_tag_keys & exclude_tags:
            continue

        score = 0.0
        reasons: list[str] = []

        for tag_info in entry.tags:
            if tag_info.key in boost_tags:
                score += tag_info.weight
                reasons.append(f"matches your {tag_info.display_name.lower()} preference")

        score += 0.5 * item.popularity_score

        if item.is_signature:
            score += 1.0
            reasons.append("chef's signature")

        if item.popularity_score > 7.0:
            reasons.append("popular pick")

        scored.append(ScoredItem(item=item, score=score, reasons=reasons))

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:n]


def build_items_with_tags(menu_items: list[MenuItem]) -> list[ItemWithTags]:
    result = []
    for item in menu_items:
        tags = [
            TagInfo(key=it.tag.key, display_name=it.tag.display_name, weight=it.weight)
            for it in item.item_tags
        ]
        result.append(ItemWithTags(item=item, tags=tags))
    return result
