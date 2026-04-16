"""Single source of truth for metric formulas and chart captions.

Every tile, chart and tooltip pulls its explanatory text from here so
the tool is self-documenting: hovering any metric shows the formula and
the exact Pillar 3 source cell it derives from.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricCaption:
    """Describes a derived metric."""

    key: str
    label: str
    short_label: str            # for tile titles
    unit: str                   # "%", "€bn", "pp", …
    formula: str                # human-readable formula using source cell refs
    sources: tuple[str, ...]    # Pillar 3 cell refs, e.g. ("K_90.01 r0040 c0010",)
    description: str            # one-sentence tooltip body


METRIC_CAPTIONS: dict[str, MetricCaption] = {
    "mrel_pct_trea": MetricCaption(
        key="mrel_pct_trea",
        label="Own funds and eligible liabilities as % of TREA",
        short_label="MREL % TREA",
        unit="%",
        formula="K_90.01 r0040 c0010",
        sources=("K_90.01 r0040 c0010",),
        description=(
            "MREL capacity expressed as a percentage of the Total Risk Exposure "
            "Amount. This is the headline MREL ratio."
        ),
    ),
    "mrel_pct_tem": MetricCaption(
        key="mrel_pct_tem",
        label="Own funds and eligible liabilities as % of TEM",
        short_label="MREL % TEM",
        unit="%",
        formula="K_90.01 r0070 c0010",
        sources=("K_90.01 r0070 c0010",),
        description=(
            "MREL capacity expressed as a percentage of the Total Exposure "
            "Measure (leverage-ratio denominator)."
        ),
    ),
    "subord_pct_trea": MetricCaption(
        key="subord_pct_trea",
        label="Of which own funds and subordinated liabilities as % of TREA",
        short_label="Subord % TREA",
        unit="%",
        formula="K_90.01 r0050 c0010",
        sources=("K_90.01 r0050 c0010",),
        description=(
            "Portion of MREL capacity made up of own funds and subordinated "
            "instruments, as a percentage of TREA."
        ),
    ),
    "mrel_requirement_trea": MetricCaption(
        key="mrel_requirement_trea",
        label="MREL requirement (% of TREA)",
        short_label="MREL req % TREA",
        unit="%",
        formula="K_90.01 r0120 c0010",
        sources=("K_90.01 r0120 c0010",),
        description="Binding MREL requirement expressed as a percentage of TREA.",
    ),
    "mrel_surplus_trea_pp": MetricCaption(
        key="mrel_surplus_trea_pp",
        label="MREL surplus vs requirement (TREA)",
        short_label="Surplus (TREA)",
        unit="pp",
        formula="K_90.01 r0040 c0010  –  K_90.01 r0120 c0010",
        sources=("K_90.01 r0040 c0010", "K_90.01 r0120 c0010"),
        description=(
            "MREL capacity minus MREL requirement, both as % of TREA. "
            "Positive = cushion above requirement; negative = shortfall."
        ),
    ),
    "mrel_total_amount": MetricCaption(
        key="mrel_total_amount",
        label="Own funds and eligible liabilities (total, €)",
        short_label="MREL stack",
        unit="€bn",
        formula="K_90.01 r0010 c0010",
        sources=("K_90.01 r0010 c0010",),
        description="Absolute euro amount of MREL capacity (stack).",
    ),
    "subordination_ratio": MetricCaption(
        key="subordination_ratio",
        label="Subordination ratio",
        short_label="Subord ratio",
        unit="%",
        formula="K_90.01 r0050 c0010  /  K_90.01 r0040 c0010",
        sources=("K_90.01 r0050 c0010", "K_90.01 r0040 c0010"),
        description=(
            "Share of MREL capacity that is subordinated (own funds plus "
            "subordinated liabilities divided by total eligible liabilities, "
            "both on TREA basis)."
        ),
    ),
    "trea": MetricCaption(
        key="trea",
        label="Total Risk Exposure Amount",
        short_label="TREA",
        unit="€bn",
        formula="K_90.01 r0030 c0010",
        sources=("K_90.01 r0030 c0010",),
        description="Total risk-weighted exposure of the resolution group.",
    ),
    "tem": MetricCaption(
        key="tem",
        label="Total Exposure Measure",
        short_label="TEM",
        unit="€bn",
        formula="K_90.01 r0060 c0010",
        sources=("K_90.01 r0060 c0010",),
        description="Leverage-ratio denominator of the resolution group.",
    ),
}


# Instrument-class labels used on the composition page (see
# core.metrics.TLAC1_COMPOSITION_CLASSES for the row-code mapping).
COMPOSITION_CLASS_LABELS: dict[str, str] = {
    "cet1": "CET1",
    "at1": "Additional Tier 1",
    "tier2": "Tier 2",
    "subord_eligible_liabilities": "Subordinated eligible liabilities",
    "senior_eligible_liabilities": "Senior eligible liabilities",
}

COMPOSITION_CLASS_DESCRIPTION: dict[str, str] = {
    "cet1": "Common Equity Tier 1 capital (TLAC1 row 0010).",
    "at1": "Additional Tier 1 capital (TLAC1 row 0020).",
    "tier2": "Tier 2 capital (TLAC1 row 0060).",
    "subord_eligible_liabilities": (
        "Subordinated eligible liabilities — own issuance plus intra-group "
        "plus grandfathered plus T2 with residual maturity < 1y "
        "(TLAC1 rows 0100 + 0110 + 0120 + 0130, col c0010)."
    ),
    "senior_eligible_liabilities": (
        "Senior (non-subordinated) eligible liabilities — pre-cap plus "
        "grandfathered plus post-Art 72b(3) capped amount "
        "(TLAC1 rows 0140 + 0150 + 0160, col c0010)."
    ),
}


# Maturity-bucket labels + descriptions (K_97.00 col c0050).
MATURITY_BUCKET_LABELS: dict[str, str] = {
    "maturity_1_to_2y":   "1–2y",
    "maturity_2_to_5y":   "2–5y",
    "maturity_5_to_10y":  "5–10y",
    "maturity_10y_plus":  "10y+",
    "maturity_perpetual": "Perpetual",
}

MATURITY_BUCKET_SOURCES: dict[str, str] = {
    "maturity_1_to_2y":   "K_97.00 r0060 c0050",
    "maturity_2_to_5y":   "K_97.00 r0070 c0050",
    "maturity_5_to_10y":  "K_97.00 r0080 c0050",
    "maturity_10y_plus":  "K_97.00 r0090 c0050",
    "maturity_perpetual": "K_97.00 r0100 c0050",
}


# Creditor-ranking (TLAC3 / TLAC3b) labels for the creditor-rank page.
CREDITOR_SCOPE_LABELS: dict[str, str] = {
    "resolution":     "Resolution entity (K_97.00 — TLAC3)",
    "non_resolution": "Non-resolution subsidiary (K_98.00 — TLAC3b)",
}

CREDITOR_SCOPE_DESCRIPTION: dict[str, str] = {
    "resolution": (
        "MREL-eligible stack of the resolution entity broken down by "
        "insolvency rank (K_97.00 row 0050 col c0010). Lower rank numbers "
        "sit higher in the creditor hierarchy (more senior)."
    ),
    "non_resolution": (
        "MREL-eligible stack of material non-resolution subsidiaries broken "
        "down by insolvency rank (K_98.00 row 0020 col c0010). Only banks "
        "that report as non-resolution entities appear here."
    ),
}


def get_caption(key: str) -> MetricCaption:
    """Fetch a metric caption by key — raises KeyError if absent.

    Using this function (rather than dict access) gives a clear callsite
    when a new metric gets wired into a component.
    """
    return METRIC_CAPTIONS[key]
