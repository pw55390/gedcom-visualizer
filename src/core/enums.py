"""
Core Domain Enumerations for Genealogy System.
GEDCOM 5.5.1 / 7.0 compliant standard types.
"""

from enum import Enum


class Sex(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "X"
    UNKNOWN = "U"


class NameType(str, Enum):
    BIRTH = "BIRTH"
    MARRIED = "MARRIED"
    ALIAS = "ALIAS"
    NICKNAME = "NICKNAME"
    ADOPTIVE = "ADOPTIVE"
    MAIDEN = "MAIDEN"
    OTHER = "OTHER"


class UnionType(str, Enum):
    MARRIAGE = "MARRIAGE"
    CIVIL_UNION = "CIVIL_UNION"
    PARTNERSHIP = "PARTNERSHIP"
    UNMARRIED = "UNMARRIED"
    UNKNOWN = "UNKNOWN"


class ParentChildRelType(str, Enum):
    BIOLOGICAL = "BIOLOGICAL"
    ADOPTIVE = "ADOPTIVE"
    FOSTER = "FOSTER"
    STEP = "STEP"
    GUARDIAN = "GUARDIAN"


class SpouseRole(str, Enum):
    HUSBAND = "HUSBAND"
    WIFE = "WIFE"
    PARTNER = "PARTNER"


class EventType(str, Enum):
    # Personal Events
    BIRTH = "BIRT"
    BAPTISM = "CHR"
    DEATH = "DEAT"
    BURIAL = "BURI"
    CREMATION = "CREM"
    EMIGRATION = "EMIG"
    IMMIGRATION = "IMMI"
    CENSUS = "CENS"
    OCCUPATION = "OCCU"
    EDUCATION = "EDUC"
    RESIDENCE = "RESI"

    # Family Events
    MARRIAGE = "MARR"
    ENGAGEMENT = "ENGA"
    DIVORCE = "DIV"
    ANNULMENT = "ANUL"
    MARRIAGE_SETTLEMENT = "MARS"

    # Generic / Custom
    CUSTOM = "EVEN"


class EventRole(str, Enum):
    PRIMARY = "PRIMARY"
    SPOUSE_1 = "SPOUSE_1"
    SPOUSE_2 = "SPOUSE_2"
    WITNESS = "WITNESS"
    GODPARENT = "GODPARENT"
    OFFICIANT = "OFFICIANT"
    INFORMANT = "INFORMANT"
    OTHER = "OTHER"


class DateModifier(str, Enum):
    EXACT = "EXACT"          # e.g., 12 JAN 1920
    ABOUT = "ABT"            # e.g., ABT 1920
    ESTIMATED = "EST"        # e.g., EST 1920
    CALCULATED = "CAL"       # e.g., CAL 1920
    BEFORE = "BEF"          # e.g., BEF 1920
    AFTER = "AFT"            # e.g., AFT 1920
    BETWEEN = "BET"          # e.g., BET 1910 AND 1920
    FROM_TO = "FROM_TO"      # e.g., FROM 1910 TO 1920
    TEXT_ONLY = "TEXT"       # Freeform text date


class SourceQuality(int, Enum):
    VERY_HIGH = 4  # Direct primary evidence, clear official record
    HIGH = 3       # Primary evidence, minor secondary elements
    MEDIUM = 2     # Secondary evidence, reliable source
    LOW = 1        # Questionable source, hearsay
    UNRELIABLE = 0 # Unreliable, unverified assumption
