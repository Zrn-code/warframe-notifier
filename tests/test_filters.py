from wfnotify.filters import fissure_matches, in_allowlist, tristate


def test_tristate():
    assert tristate("yes", True) is True
    assert tristate("yes", False) is False
    assert tristate("no", False) is True
    assert tristate("no", True) is False
    assert tristate("both", True) is True
    assert tristate("both", False) is True
    assert tristate(None, True) is True
    assert tristate("", False) is True


def test_in_allowlist():
    assert in_allowlist("Survival", []) is True          # empty = no constraint
    assert in_allowlist("Survival", None) is True
    assert in_allowlist("Survival", ["Survival", "Defense"]) is True
    assert in_allowlist("Spy", ["Survival", "Defense"]) is False


AXI_NORMAL = {"tierNum": 4, "missionTypeKey": "Survival", "enemyKey": "Corpus",
              "isHard": False, "isStorm": False}


def test_fissure_axi_rules():
    rules = {"tier_nums": [4], "steel_path": "no", "void_storm": "no"}
    assert fissure_matches(AXI_NORMAL, rules) is True
    assert fissure_matches({**AXI_NORMAL, "tierNum": 1}, rules) is False    # wrong tier
    assert fissure_matches({**AXI_NORMAL, "isHard": True}, rules) is False  # steel path
    assert fissure_matches({**AXI_NORMAL, "isStorm": True}, rules) is False # void storm


def test_fissure_mission_allowlist():
    rules = {"tier_nums": [4], "mission_type_keys": ["Defense"]}
    assert fissure_matches(AXI_NORMAL, rules) is False                  # Survival not allowed
    assert fissure_matches({**AXI_NORMAL, "missionTypeKey": "Defense"}, rules) is True


def test_fissure_empty_rules_match_all():
    assert fissure_matches(AXI_NORMAL, {}) is True
