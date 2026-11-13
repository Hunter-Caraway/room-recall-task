"""Recognition scores for one grid."""
from __future__ import annotations

from statistics import NormalDist

_z = NormalDist().inv_cdf


def rates(hits: int, targets: int, false_alarms: int, decoys: int) -> tuple[float, float]:
    """Hit and false-alarm rates with the log-linear correction (Hautus, 1995):
    add 0.5 to each count and 1 to each total, so rates of 0 and 1 stay finite."""
    return (hits + 0.5) / (targets + 1), (false_alarms + 0.5) / (decoys + 1)


def dprime(hits: int, targets: int, false_alarms: int, decoys: int) -> float:
    hit_rate, fa_rate = rates(hits, targets, false_alarms, decoys)
    return _z(hit_rate) - _z(fa_rate)


def criterion(hits: int, targets: int, false_alarms: int, decoys: int) -> float:
    """c: positive means cautious (says "yes" less), negative means liberal."""
    hit_rate, fa_rate = rates(hits, targets, false_alarms, decoys)
    return -(_z(hit_rate) + _z(fa_rate)) / 2
