"""
Pet gacha generation engine.
- 희귀도 기하급수적 확률
- 천장(Pity) 시스템
- 10연차 10번째 레어 이상 확정
- MBTI 기반 성격 부여
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
        candidates = [r for r in RARITY_ORDER if RARITY_ORDER.index(r) >= 2]  # rare+
    else:
        candidates = list(RARITY_ORDER)

    weights = [RARITIES[r]['prob'] for r in candidates]
    total = sum(weights)
    weights = [w / total for w in weights]  # normalize

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

    # 천장 도달
    if pity >= PITY_THRESHOLD:
        force_rare_plus = True

    rarity = _weighted_rarity(force_rare_plus=force_rare_plus)
    rarity_idx = RARITY_ORDER.index(rarity)

    # Pity 카운터 업데이트
    if rarity_idx >= 2:  # rare 이상이면 리셋
        couple.pity_counter = 0
    else:
        couple.pity_counter = pity + 1

    pet = Pet(
        couple_id=couple.id,
        breed=_random_breed(),
        rarity=rarity,
        personality=_random_personality(),
        is_active=False,  # 10연차 완료 후 유저가 선택
    )
    return pet


def generate_ten_pull(couple):
    """
    10연차 생성.
    - 1~9번째: 일반 확률 + pity
    - 10번째: 레어 이상 확정
    Returns: list[Pet] (10마리)
    """
    pets = []
    for i in range(10):
        force = (i == TEN_PULL_GUARANTEE_INDEX)  # 10번째
        pet = generate_single(couple, force_rare_plus=force)
        pets.append(pet)

    return pets


def do_gacha(couple, user):
    """
    10연차 실행 — 리롤권 1장 소모.
    Returns: (success: bool, message: str, pets: list[Pet])
    """
    tickets = getattr(user, 'reroll_tickets', 0) or 0
    if tickets < 1:
        return False, '리롤권이 부족합니다! 출석체크로 리롤권을 모아보세요.', []

    # 리롤권 차감 (Transaction 안전)
    user.reroll_tickets = tickets - 1

    # 기존 활성 펫 비활성화
    Pet.query.filter_by(couple_id=couple.id, is_active=True)\
             .update({'is_active': False})

    pets = generate_ten_pull(couple)
    for p in pets:
        db.session.add(p)

    # 가장 높은 희귀도 펫을 활성화
    best = max(pets, key=lambda p: RARITY_ORDER.index(p.rarity))
    best.is_active = True

    db.session.commit()
    return True, '10연차 완료!', pets


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


def admin_grant_tickets(user, amount):
    """어드민이 리롤권 수동 지급."""
    user.reroll_tickets = (user.reroll_tickets or 0) + amount
    db.session.commit()
    return user.reroll_tickets
