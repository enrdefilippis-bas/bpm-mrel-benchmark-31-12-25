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


# TLAC1 row groups used in composition & maturity analyses.
TLAC1_ROW_GROUPS = {
    "cet1": "0010",
    "at1": "0020",
    "tier2": "0060",
    "eligible_before_adjustments": "0110",
    "own_funds_and_eligible_after_adjustments": "0220",
    "own_funds_and_subordinated_after_adjustments": "0230",
    "trea": "0230",
    "tem": "0240",
    "subordinated_instruments_direct": "0120",
    "eligible_not_subordinated": "0130",
    "residual_maturity_1_to_2y": "0070",
    "residual_maturity_2_to_5y": "0080",
    "residual_maturity_5_to_10y": "0090",
    "residual_maturity_perpetual": "0100",
}


def get_caption(key: str) -> MetricCaption:
    """Fetch a metric caption by key — raises KeyError if absent.

    Using this function (rather than dict access) gives a clear callsite
    when a new metric gets wired into a component.
    """
    return METRIC_CAPTIONS[key]
