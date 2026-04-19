"""Bank-specific Pillar 3 parsers for banks missing from the EBA export."""
from __future__ import annotations

from .base import BankMeta, BaseBankParser
from .bbva import BBVAParser
from .bper import BPERParser
from .cassa_centrale import CassaCentraleParser
from .credem import CredemParser
from .credit_agricole import CreditAgricoleParser
from .iccrea import ICCREAParser
from .intesa import IntesaParser
from .mediobanca import MediobancaParser
from .mediolanum import MediolanumParser
from .mps import MPSParser
from .socgen import SocGenParser
from .unicredit import UniCreditParser

ALL_PARSERS: tuple[type[BaseBankParser], ...] = (
    IntesaParser,
    UniCreditParser,
    BBVAParser,
    CreditAgricoleParser,
    SocGenParser,
    MPSParser,
    MediobancaParser,
    BPERParser,
    CredemParser,
    MediolanumParser,
    ICCREAParser,
    CassaCentraleParser,
)

__all__ = [
    "BankMeta",
    "BaseBankParser",
    "IntesaParser",
    "UniCreditParser",
    "BBVAParser",
    "CreditAgricoleParser",
    "SocGenParser",
    "MPSParser",
    "MediobancaParser",
    "BPERParser",
    "CredemParser",
    "MediolanumParser",
    "ICCREAParser",
    "CassaCentraleParser",
    "ALL_PARSERS",
]
