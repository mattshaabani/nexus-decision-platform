"""Tests for person-level fairness metrics."""

import numpy as np

from nexus.domain.fairness import four_fifths_and_eo


def test_four_fifths_balanced():
    # 4 persons, 2 per group, same approval pattern
    person_ids = np.array([0, 1, 2, 3])
    y_true = np.array([0, 0, 0, 0])
    y_prob = np.array([0.2, 0.2, 0.2, 0.2])  # all approved (prob < 0.5)
    protected = np.array([0, 0, 1, 1])
    r = four_fifths_and_eo(person_ids, y_true, y_prob, protected)
    assert r.four_fifths_ratio == 1.0
    assert r.eo_gap == 0.0
    assert r.n_persons_a == 2
    assert r.n_persons_b == 2


def test_four_fifths_imbalanced():
    person_ids = np.array([0, 1, 2, 3, 4, 5])
    y_true = np.array([0, 0, 0, 0, 0, 0])
    # group 0: both approved; group 1: only 1 of 4 approved
    y_prob = np.array([0.1, 0.1, 0.8, 0.8, 0.8, 0.2])
    protected = np.array([0, 0, 1, 1, 1, 1])
    r = four_fifths_and_eo(person_ids, y_true, y_prob, protected, approve_threshold=0.5)
    assert r.approval_rate_a == 1.0
    assert r.approval_rate_b == 0.25
    assert r.four_fifths_ratio == 0.25


def test_person_collapse():
    # same person, multiple rows — should count once
    person_ids = np.array([0, 0, 1, 1])
    y_true = np.array([0, 1, 0, 0])  # person 0 is bad
    y_prob = np.array([0.1, 0.1, 0.1, 0.1])
    protected = np.array([0, 0, 1, 1])
    r = four_fifths_and_eo(person_ids, y_true, y_prob, protected)
    assert r.n_persons_a == 1
    assert r.n_persons_b == 1