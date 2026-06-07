"""Reusable rule helpers for fissures and arbitration.

Always filter on the English *Key fields (missionTypeKey, enemyKey) and numeric/boolean
fields (tierNum, isHard, isStorm) — never on the localized display fields.
"""


def tristate(value, flag) -> bool:
    """Match a "yes"/"no"/"both" config value against a boolean field.

    "yes" -> flag True; "no" -> flag False; "both"/None/"" -> always pass.
    """
    if value in (None, "", "both"):
        return True
    if value == "yes":
        return flag is True
    if value == "no":
        return flag is False
    return True


def in_allowlist(value, allowlist) -> bool:
    """Pass if allowlist is empty/None (no constraint) or value is in it."""
    if not allowlist:
        return True
    return value in allowlist


def fissure_matches(raw: dict, rules: dict) -> bool:
    """True if a raw fissure object satisfies all configured rule dimensions."""
    if not in_allowlist(raw.get("tierNum"), rules.get("tier_nums")):
        return False
    if not in_allowlist(raw.get("missionTypeKey"), rules.get("mission_type_keys")):
        return False
    if not in_allowlist(raw.get("enemyKey"), rules.get("enemy_keys")):
        return False
    if not tristate(rules.get("steel_path"), raw.get("isHard")):
        return False
    if not tristate(rules.get("void_storm"), raw.get("isStorm")):
        return False
    return True
