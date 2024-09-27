from datetime import datetime
from enum import Enum
import databases
import sqlalchemy
from ormar import Model, OrmarConfig, Integer, String, \
    DateTime, JSON, UUID, Boolean, ForeignKey
from .config import settings
from pydantic import Json
from typing import Optional

base_ormar_config = OrmarConfig(
    metadata = sqlalchemy.MetaData(),
    database = databases.Database(settings.db_url)
)

class MeasureCategory(Enum):
    ECONOMIC = "Economic"
    SECURITY_DEFENSE = "Security and Defense"
    HEALTH_WELFARE = "Health and Welfare"
    EDUCATION_CULTURE = "Education and Culture"
    ENVIRONMENT_ENERGY = "Environment and Energy"
    JUSTICE_HUMAN_RIGHTS = "Justice and Human Rights"
    TECHNOLOGY_INNOVATION = "Technology and Innovation"
    FOREIGN_RELATIONS = "Foreign Relations"
    OTHERS = "Others"    

class Type(Enum):
    SENATE_PROJECT = 'SenateProject'
    HOUSE_PROJECT = 'HouseProject'

class Body(Enum):
    SENATE = 'Senate'
    REPRESENTATIVE = 'HouseOfRepresentatives'

class Party(Enum):
    PPD = 'PPD'
    PNP = 'PNP'
    PIP = 'PIP'
    VC = 'VC'
    PD = 'PD'
    IND = 'IND'

class Status(Enum):
    FILLED = 'Filled'
    SENATE_APPROVED = 'SenateApproved'
    HOUSE_APPROVED = 'HouseApproved'
    SENT_GOVERNOR = 'SentGovernor'
    GOVERNOR_APPROVED = 'GovernorApproved'

class Term(Enum):
    _1985 = '1985-1988'
    _1989 = '1989-1992'
    _1993 = '1993-1996'
    _1997 = '1997-2000'
    _2001 = '2001-2004'
    _2005 = '2005-2008'
    _2009 = '2009-2012'
    _2013 = '2013-2016'
    _2017 = '2017-2020'
    _2021 = '2021-2024'
    _2024 = '2024-2027'

class DateFieldsMixins:
    created_date: datetime = DateTime(default=datetime.now)
    updated_date: datetime = DateTime(default=datetime.now)

class TermMixins:
    status: str = String(max_length=9, choices=list(Term), default=Term._2021.value)

class StatusMixins:
    status: str = String(max_length=10, choices=list(Status), default=Status.FILLED.value)
    is_law: bool = Boolean(default=False)
    
class LegislatorMixins:
    id: int = Integer(primary_key=True)
    first_name: str = String(max_length=20, nullable=False)
    middle_name: str = String(max_length=20)
    last_first_name: str = String(max_length=20, nullable=False)
    last_second_name: str = String(max_length=20)
    party: str = String(max_length=20, choices=list(Party), default=Party.IND.value)
    body: str = String(max_length=20, choices=list(Body), default=Body.SENATE.value, nullable=False)
    active: bool = Boolean(default=True, nullable=False)    

class Senator(Model, LegislatorMixins, TermMixins):
    ormar_config = base_ormar_config.copy(tablename="senators")
        
class Representative(Model, LegislatorMixins, TermMixins):
    ormar_config = base_ormar_config.copy(tablename="representatives")

class Measure(Model, StatusMixins, DateFieldsMixins, TermMixins):
    ormar_config = base_ormar_config.copy(tablename="measures")

    id: str = UUID(primary_key=True)
    number: str = String(max_length=7, nullable=False)
    summary: str = String(max_length=256, nullable=False)
    authors: Json = JSON(default=list)
    type: str = String(max_length=20, choices=list(Type), default=Type.SENATE_PROJECT.value, nullable=False)
    body: str = String(max_length=20, choices=list(Body), default=Body.SENATE.value, nullable=False)
    status: str = String(max_length=20, unique=True, nullable=False)
    active: bool = Boolean(default=True, nullable=False)
    category: str = String(max_length=20, choices=list(MeasureCategory))

engine = sqlalchemy.create_engine(settings.db_url)