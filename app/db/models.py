from datetime import datetime
from enum import Enum
import databases
import sqlalchemy
from ormar import Model, OrmarConfig, Integer, String, \
    DateTime, JSON, UUID, Boolean, ForeignKey
from .config import settings
from pydantic import Json
from typing import Optional

database = databases.Database(settings.db_url)
metadata = sqlalchemy.MetaData()

class Type(Enum):
    senate_proyect = 'SenateProject'
    house_proyect = 'HouseProject'

class Body(Enum):
    senate = 'Senate'
    representative = 'HouseOfRepresentatives'

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

class Party(Enum):
    ppd = 'PPD'
    pnp = 'PNP'
    pip = 'PIP'
    vc = 'VC'
    pd = 'PD'
    ind = 'Ind'

class Status(Enum):
    filled = 'Filled'
    senate_approved = 'SenateApproved'
    house_approved = 'HouseApproved'
    sent_governor = 'SentGovernor'
    governor_approved = 'GovernorApproved'

class DateFieldsMixins:
    created_date: datetime = DateTime(default=datetime.now)
    updated_date: datetime = DateTime(default=datetime.now)

class TermMixins:
    status: str = String(max_length=9, choices=list(Term), default=Term._2021.value)

class StatusMixins:
    status: str = String(max_length=10, choices=list(Status), default=Status.filled.value)
    is_law: bool = Boolean(default=False)

class BaseMeta(OrmarConfig):
    metadata = metadata
    database = database
    
class LegislatorMixins:
    id: int = Integer(primary_key=True)
    first_name: str = String(max_length=20, nullable=False)
    middle_name: str = String(max_length=20)
    last_first_name: str = String(max_length=20, nullable=False)
    last_second_name: str = String(max_length=20)
    party: str = String(max_length=20, choices=list(Party), default=Party.ind.value)
    body: str = String(max_length=20, choices=list(Body), default=Body.senate.value, nullable=False)
    active: bool = Boolean(default=True, nullable=False)    

class Senator(Model, LegislatorMixins, TermMixins):
    class Meta(BaseMeta):
        tablename = "senators"
        
class Representative(Model, LegislatorMixins, TermMixins):
    class Meta(BaseMeta):
        tablename = "representatives"

class Measure(Model, StatusMixins, DateFieldsMixins, TermMixins):
    class Meta(BaseMeta):
        tablename = "measures"

    id: str = UUID(primary_key=True)
    number: str = String(max_length=7, nullable=False)
    summary: str = String(max_length=256, nullable=False)
    authors: Json = JSON(default=list)
    type: str = String(max_length=20, choices=list(Type), default=Type.senate_proyect.value, nullable=False)
    body: str = String(max_length=20, choices=list(Body), default=Body.senate.value, nullable=False)
    status: str = String(max_length=20, unique=True, nullable=False)
    active: bool = Boolean(default=True, nullable=False)

# class Pipeline(Model, StatusMixins, DateFieldsMixins, ExecutedMixins):
#     class Meta(BaseMeta):
#         tablename = "pipelines"

#     id: int = Integer(primary_key=True)
#     owner: Optional[User] = ForeignKey(User, ondelete="CASCADE")
#     name: str = String(max_length=100)
#     env: str = String(max_length=10)
#     stage_list: Json = JSON(default=list)

# class Instance(Model):
#     class Meta(BaseMeta):
#         tablename = "instances"

#     id: str = String(primary_key=True, max_length=8)
#     pipeline: Optional[Pipeline] = ForeignKey(Pipeline)

# class Stage(Model, StatusMixins, DateFieldsMixins, ExecutedMixins):
#     class Meta(BaseMeta):
#         tablename = "stages"

#     id: int = Integer(primary_key=True)
#     pipeline: Optional[Pipeline] = ForeignKey(Pipeline, ondelete="CASCADE")
#     name: str = String(max_length=100)
#     job_list: Json = JSON(default=list)

# class Job(Model, StatusMixins, DateFieldsMixins, ExecutedMixins):
#     class Meta(BaseMeta):
#         tablename = "jobs"

#     id: int = Integer(primary_key=True)
#     stage: Optional[Stage] = ForeignKey(Stage, ondelete="CASCADE")
#     name: str = String(max_length=100)
#     parallel: bool = Boolean(default=False)
#     parameters: Json = JSON(default={})
#     build_number: int = Integer(default=0, minimum=0)
#     build_url: str = String(default="", max_length=2000)
#     on_start: Json = JSON(default={})
#     on_finish: Json = JSON(default={})

#TODO
# class Validation(Model):
#     class Meta(BaseMeta):
#         tablename = "validations"

#     job: Optional[Job] = ForeignKey(Job)

# class Verification(Model):
#     class Meta(BaseMeta):
#         tablename = "verifications"

#     job: Optional[Job] = ForeignKey(Job)
#     env: str = String(default=Pipeline.env, max_length=10)
#     verifier: str = String(default="hdfs_records_count", max_length=100)
#     threshold: int = Integer(default=0.1, minimum=0.1)

engine = sqlalchemy.create_engine(settings.db_url)