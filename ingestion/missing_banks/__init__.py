"""Bank-specific Pillar 3 parsers for banks missing from the EBA export."""
from __future__ import annotations

from .base import BankMeta, BaseBankParser
from .bbva import BBVAParser
from .credit_agricole import CreditAgricoleParser
from .intesa import IntesaParser
from .socgen import SocGenParser
from .unicredit import UniCreditParser

ALL_PARSERS: tuple[type[BaseBankParser], ...] = (
    IntesaParser,
    UniCreditParser,
    BBVAParser,
    CreditAgricoleParser,
    SocGenParser,
)

__all__ = [
    "BankMeta",
    "BaseBankParser",
    "IntesaParser",
    "UniCreditParser",
    "BBVAParser",
    "CreditAgricoleParser",
    "SocGenParser",
    "ALL_PARSERS",
]
