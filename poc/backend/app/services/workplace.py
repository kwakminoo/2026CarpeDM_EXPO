"""직장대화 — 카테고리 5개에서 장면 1개씩 뽑아 이어간다."""
import random

WORKPLACE_SLUG = "workplace-conversation"


def pick_workplace_episodes(scenario, episodes, rng=None):
    """카테고리 순서대로 장면 1개씩 고른다. rng는 테스트에서 고정한다."""
    rng = rng or random
    groups = (getattr(scenario, "world_setting", None) or {}).get("workplace_categories") or []
    by_order = {episode.order: episode for episode in episodes}
    picked = []
    for group in groups:
        choices = [by_order[order] for order in group.get("orders") or [] if order in by_order]
        if not choices:
            raise ValueError(f"직장대화 카테고리 '{group.get('label', group.get('id'))}'에 장면이 없습니다.")
        picked.append(rng.choice(choices))
    if len(picked) != 5:
        raise ValueError("직장대화는 카테고리 5개가 필요합니다.")
    return picked


def scene_item(episode, category):
    """연습 안내·TIP에 쓸 장면 한 칸."""
    tip_item = (episode.checklist or [{}])[0]
    return {
        "id": f"{episode.id}:scene",
        "episode_id": episode.id,
        "text": episode.initial_question,
        "title": episode.title,
        "situation": episode.situation,
        "category_id": category.get("id", ""),
        "category_label": category.get("label", ""),
        "tip": tip_item.get("tip") or tip_item.get("comment") or "",
    }
