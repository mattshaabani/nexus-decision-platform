from nexus.domain.models import DecisionOutcome
from nexus.domain.policy import PolicyConfig, apply_policy, expected_loss


def test_el_formula():
    assert expected_loss(0.1, 0.5, 1000) == 50.0


def test_approve_refer_decline():
    cfg = PolicyConfig(approve_max_pd=0.05, refer_max_pd=0.15)
    assert apply_policy(0.02, ead=5000, config=cfg).outcome == DecisionOutcome.APPROVE
    assert apply_policy(0.10, ead=5000, config=cfg).outcome == DecisionOutcome.REFER
    assert apply_policy(0.20, ead=5000, config=cfg).outcome == DecisionOutcome.DECLINE