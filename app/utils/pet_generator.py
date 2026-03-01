"""
Pet gacha generation engine.
- 희귀도 기하급수적 확률
- 천장(Pity) 시스템
- 10연차 10번째 레어 이상 확정
- 단일 뽑기 (1회)
- MBTI 기반 성격 부여
- 리롤권은 커플 단위 통합 관리
"""
import random
from app.models.pet import (
    RARITIES, RARITY_ORDER, BREEDS, MBTI_LIST,
    PITY_THRESHOLD, TEN_PULL_GUARANTEE_INDEX, Pet,
)
from app.extensions import db


def _weighted_rarity(force_rare_plus=False):
    """
    희귀도를 가중치 기반으로 뽑기.
    force_rare_plus=True 이면 rare 이상만 대상.
    """
    if force_rare_plus:
        candidates = [r for r in RARITY_ORDER if RARITY_ORDER.index(r) >= 2]
    else:
        candidates = list(RARITY_ORDER)

    weights = [RARITIES[r]['prob'] for r in candidates]
    total = sum(weights)
    weights = [w / total for w in weights]

    return random.choices(candidates, weights=weights, k=1)[0]


def _random_breed():
    return random.choice(list(BREEDS.keys()))


def _random_personality():
    return random.choice(MBTI_LIST)


def generate_single(couple, force_rare_plus=False):
    """
    단일 펫 생성.
    Pity 카운터를 체크하여 천장 도달 시 rare+ 확정.
    """
    pity = getattr(couple, 'pity_counter', 0) or 0

    if pity >= PITY_THRESHOLD:
        force_rare_plus = True

    rarity = _weighted_rarity(force_rare_plus=force_rare_plus)
    rarity_idx = RARITY_ORDER.index(rarity)

    if rarity_idx >= 2:
        couple.pity_counter = 0
    else:
        couple.pity_counter = pity + 1

    pet = Pet(
        couple_id=couple.id,
        breed=_random_breed(),
        rarity=rarity,
        personality=_random_personality(),
        is_active=False,
    )
    return pet


def generate_ten_pull(couple):
    """
    10연차 생성.
    - 1~9번째: 일반 확률 + pity
    - 10번째: 레어 이상 확정
    """
    pets = []
    for i in range(10):
        force = (i == TEN_PULL_GUARANTEE_INDEX)
        pet = generate_single(couple, force_rare_plus=force)
        pets.append(pet)
    return pets


def do_gacha(couple, pull_count=10):
    """
    뽑기 실행 — 리롤권은 커플 통합 (pull_count: 1 또는 10).
    Returns: (success: bool, message: str, pets: list[Pet])
    """
    pull_count = 10 if pull_count not in (1, 10) else pull_count
    cost = pull_count
    tickets = getattr(couple, 'reroll_tickets', 0) or 0
    if tickets < cost:
        return False, f'리롤권이 부족합니다! ({tickets}/{cost}장) 출석체크로 리롤권을 모아보세요.', []

    couple.reroll_tickets = tickets - cost

    Pet.query.filter_by(couple_id=couple.id, is_active=True)\
             .update({'is_active': False})

    if pull_count == 1:
        pets = [generate_single(couple)]
    else:
        pets = generate_ten_pull(couple)

    for p in pets:
        db.session.add(p)

    best = max(pets, key=lambda p: RARITY_ORDER.index(p.rarity))
    best.is_active = True

    db.session.commit()
    return True, f'{pull_count}연차 완료!', pets


def admin_force_rarity(couple, rarity, breed=None):
    """어드민이 특정 희귀도 펫을 강제 지급."""
    if rarity not in RARITY_ORDER:
        return None

    Pet.query.filter_by(couple_id=couple.id, is_active=True)\
             .update({'is_active': False})

    pet = Pet(
        couple_id=couple.id,
        breed=breed or _random_breed(),
        rarity=rarity,
        personality=_random_personality(),
        is_active=True,
    )
    db.session.add(pet)
    db.session.commit()
    return pet


def admin_grant_tickets(couple, amount):
    """어드민이 커플에 리롤권 수동 지급."""
    couple.reroll_tickets = (couple.reroll_tickets or 0) + amount
    db.session.commit()
    return couple.reroll_tickets
