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
    direction: str = "higher_better"
    # "higher_better" → green when BPM > peer median, red when below
    # "lower_better"  → blue when BPM < peer median (favorable), red when above
    # "neutral"       → grey delta (size metric, no favorable direction)


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
        direction="lower_better",
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
        direction="neutral",
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
        direction="neutral",
    ),
    "tem": MetricCaption(
        key="tem",
        label="Total Exposure Measure",
        short_label="TEM",
        unit="€bn",
        formula="K_90.01 r0060 c0010",
        sources=("K_90.01 r0060 c0010",),
        description="Leverage-ratio denominator of the resolution group.",
        direction="neutral",
    ),
    "total_assets": MetricCaption(
        key="total_assets",
        label="Total Assets",
        short_label="Total Assets",
        unit="€bn",
        formula="K_90.01 r0060 c0010",
        sources=("K_90.01 r0060 c0010",),
        description="Total exposure measure — alias for TEM, used as size proxy for peer comparisons.",
        direction="neutral",
    ),
    "cet1_ratio": MetricCaption(
        key="cet1_ratio",
        label="CET1 Ratio",
        short_label="CET1 %",
        unit="%",
        formula="K_91.00 (CET1 ratio row) c0010",
        sources=("K_91.00 c0010",),
        description="Common Equity Tier 1 capital as a percentage of risk-weighted assets (CRR/CRD IV).",
    ),
    "t1_capital_ratio": MetricCaption(
        key="t1_capital_ratio",
        label="Tier 1 Capital Ratio",
        short_label="T1 %",
        unit="%",
        formula="K_91.00 (Tier 1 ratio row) c0010 or Tier1 / TREA",
        sources=("K_91.00 c0010", "K_90.01 r0030 c0010"),
        description="Total Tier 1 capital (CET1 + AT1) as a percentage of TREA.",
    ),
    "total_capital_ratio": MetricCaption(
        key="total_capital_ratio",
        label="Total Capital Ratio",
        short_label="Total Cap %",
        unit="%",
        formula="K_91.00 (total capital row) c0010 or (CET1+AT1+T2) / TREA",
        sources=("K_91.00 c0010", "K_90.01 r0030 c0010"),
        description="Total capital (CET1 + AT1 + T2) as a percentage of TREA.",
    ),
    "leverage_ratio": MetricCaption(
        key="leverage_ratio",
        label="Leverage Ratio",
        short_label="Lev %",
        unit="%",
        formula="K_91.00 (leverage row) c0010 or Tier1 / TEM",
        sources=("K_91.00 c0010", "K_90.01 r0060 c0010"),
        description="Tier 1 capital as a percentage of TEM (leverage-ratio denominator).",
    ),
    "cbr_pct_trea": MetricCaption(
        key="cbr_pct_trea",
        label="Combined Buffer Requirement (% of TREA)",
        short_label="CBR % TREA",
        unit="%",
        formula="Per-bank disclosure (Pillar 3 narrative) — core.cbr.lookup_cbr",
        sources=("Pillar 3 PDF (narrative)",),
        description=(
            "Combined Buffer Requirement applicable on top of Pillar 1 + Pillar 2R, "
            "sourced from each bank's narrative Pillar 3 disclosure. NOT from EBA "
            "export row 0160 (which is absent for every bank in the 2025 release)."
        ),
        direction="lower_better",
    ),
    "mrel_requirement_trea_ex_cbr": MetricCaption(
        key="mrel_requirement_trea_ex_cbr",
        label="MREL requirement ex-CBR (% of TREA)",
        short_label="MREL req ex-CBR",
        unit="%",
        formula="req − CBR (if bank discloses INCLUDED) else req (ON_TOP)",
        sources=("K_90.01 r0120 c0010", "Pillar 3 PDF (narrative)"),
        description=(
            "Binding MREL-TREA requirement normalized to an EX-CBR base so all "
            "peers are comparable. The KM2 filing default is on_top (excludes CBR); "
            "for banks that disclose the figure already inclusive of CBR "
            "(e.g. Mediobanca, Iccrea) we subtract CBR to align."
        ),
        direction="lower_better",
    ),
    "mrel_requirement_trea_with_cbr": MetricCaption(
        key="mrel_requirement_trea_with_cbr",
        label="MREL requirement + CBR (% of TREA)",
        short_label="MREL req + CBR",
        unit="%",
        formula="req_ex_cbr + CBR",
        sources=("K_90.01 r0120 c0010", "Pillar 3 PDF (narrative)"),
        description=(
            "Overall MREL threshold (OCR-equivalent) below which the bank would "
            "face M-MDA / distribution restrictions. This is the 'real' bar a "
            "bank must clear, not the narrow MREL figure."
        ),
        direction="lower_better",
    ),
    "mrel_surplus_trea_ex_cbr_pp": MetricCaption(
        key="mrel_surplus_trea_ex_cbr_pp",
        label="Cushion vs MREL (ex-CBR, TREA)",
        short_label="Cushion vs MREL",
        unit="pp",
        formula="mrel_pct_trea − mrel_requirement_trea_ex_cbr",
        sources=("K_90.01 r0040 c0010", "K_90.01 r0120 c0010"),
        description=(
            "Capacity minus the MREL-only requirement (excluding CBR). "
            "Matches the 'cushion' figure most banks cite in their own decks."
        ),
    ),
    "mrel_surplus_trea_with_cbr_pp": MetricCaption(
        key="mrel_surplus_trea_with_cbr_pp",
        label="Cushion vs OCR (MREL + CBR, TREA)",
        short_label="Cushion vs OCR",
        unit="pp",
        formula="mrel_pct_trea − mrel_requirement_trea_with_cbr",
        sources=("K_90.01 r0040 c0010", "K_90.01 r0120 c0010", "Pillar 3 PDF"),
        description=(
            "Capacity minus the overall threshold (MREL + CBR). Negative = "
            "the bank would face M-MDA restrictions; positive = full distribution "
            "flexibility. Stricter, more economically meaningful cushion."
        ),
    ),
    "mrel_subord_requirement_trea": MetricCaption(
        key="mrel_subord_requirement_trea",
        label="MREL subordination requirement (% of TREA)",
        short_label="Subord req % TREA",
        unit="%",
        formula="K_90.01 r0130 c0010",
        sources=("K_90.01 r0130 c0010",),
        description=(
            "Subordination requirement — the portion of the MREL requirement "
            "that must be met with own funds and subordinated instruments."
        ),
        direction="lower_better",
    ),
    "mrel_subord_requirement_trea_ex_cbr": MetricCaption(
        key="mrel_subord_requirement_trea_ex_cbr",
        label="Subordination requirement ex-CBR (% of TREA)",
        short_label="Subord req ex-CBR",
        unit="%",
        formula="subord_req − CBR (if INCLUDED) else subord_req (ON_TOP)",
        sources=("K_90.01 r0130 c0010", "Pillar 3 PDF (narrative)"),
        description=(
            "Subordination requirement normalized to an EX-CBR base so all "
            "peers are comparable. Follows the same CBR treatment as the "
            "total-MREL requirement for the same bank."
        ),
        direction="lower_better",
    ),
    "mrel_subord_requirement_trea_with_cbr": MetricCaption(
        key="mrel_subord_requirement_trea_with_cbr",
        label="Subordination requirement + CBR (% of TREA)",
        short_label="Subord req + CBR",
        unit="%",
        formula="subord_req_ex_cbr + CBR",
        sources=("K_90.01 r0130 c0010", "Pillar 3 PDF (narrative)"),
        description=(
            "Subordination requirement augmented with CBR — the analogue of the "
            "OCR threshold for the subordinated portion of the MREL stack."
        ),
        direction="lower_better",
    ),
    "subord_surplus_trea_ex_cbr_pp": MetricCaption(
        key="subord_surplus_trea_ex_cbr_pp",
        label="Subord cushion vs MREL-sub (ex-CBR, TREA)",
        short_label="Subord cushion (ex-CBR)",
        unit="pp",
        formula="subord_pct_trea − mrel_subord_requirement_trea_ex_cbr",
        sources=("K_90.01 r0050 c0010", "K_90.01 r0130 c0010"),
        description=(
            "Subordinated-capacity minus the subordination requirement on an "
            "ex-CBR base. Positive = cushion; negative = shortfall."
        ),
    ),
    "subord_surplus_trea_with_cbr_pp": MetricCaption(
        key="subord_surplus_trea_with_cbr_pp",
        label="Subord cushion vs MREL-sub + CBR (TREA)",
        short_label="Subord cushion (with-CBR)",
        unit="pp",
        formula="subord_pct_trea − mrel_subord_requirement_trea_with_cbr",
        sources=("K_90.01 r0050 c0010", "K_90.01 r0130 c0010", "Pillar 3 PDF"),
        description=(
            "Subordinated-capacity minus subordination requirement plus CBR. "
            "The stricter subordination-space analogue of the OCR cushion."
        ),
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
