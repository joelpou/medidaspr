from datetime import datetime
from enum import Enum
import databases
import sqlalchemy
from ormar import Model, OrmarConfig, Integer, String, \
    Text, DateTime, JSON, ManyToMany, Boolean, ForeignKey
from .config import settings
from pydantic import Json
from typing import List, Optional

base_ormar_config = OrmarConfig(
    metadata = sqlalchemy.MetaData(),
    database = databases.Database(settings.db_url)
)

class MeasureCategory(Enum):
    ECONOMIC = "Económico"
    SECURITY_DEFENSE = "Seguridad y Defensa"
    HEALTH_WELFARE = "Salud y Bienestar"
    EDUCATION_CULTURE = "Educación y Cultura"
    ENVIRONMENT_ENERGY = "Medio Ambiente y Energía"
    JUSTICE_HUMAN_RIGHTS = "Justicia y Derechos Humanos"
    TECHNOLOGY_INNOVATION = "Tecnología e Innovación"
    FOREIGN_RELATIONS = "Relaciones Exteriores"
    OTHERS = "Otros"
    
class MeasureType(Enum):
    SENATE_PROJECT = 'Proyecto del Senado'
    HOUSE_PROJECT = 'Proyecto de la Cámara'

class Body(Enum):
    SENATE = 'Senado'
    REPRESENTATIVE = 'Cámara de Representantes'

class Party(Enum):
    PPD = 'Partido Popular Democrático'
    PNP = 'Partido Nuevo Progresista'
    PIP = 'Partido Independentista Puertorriqueño'
    MVC = 'Movimiento Victoria Ciudadana'
    PD = 'Proyecto Dignidad'
    IND = 'Independiente'
    
class Position(Enum):
    PRESIDENT = 'President'
    VICEPRESIDENT = 'Vicepresident'
    SPOKEPERSON = 'Spokeperson' # Portavoz

class Status(Enum):
    FILLED = 'Radicado'
    SENATE_APPROVED = 'Aprobado Por Senado'
    HOUSE_APPROVED = 'Aprobado Por Camara'
    SENT_GOVERNOR = 'Enviado Al Gobernador'
    GOVERNOR_APPROVED = 'Aprobado Por Gobernador'

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
    term: str = String(max_length=9, choices=list(Term), default=Term._2021.value)

class StatusMixins:
    status: str = String(max_length=20, choices=list(Status), default=Status.FILLED.value)
    is_law: bool = Boolean(default=False)
    
class LegislatorMixins:
    id: int = Integer(primary_key=True)
    first_name: str = String(max_length=20, nullable=False)
    middle_name: str = String(max_length=20, default=None)
    last_first_name: str = String(max_length=20, nullable=False)
    last_second_name: str = String(max_length=20)
    party: str = String(max_length=40, choices=list(Party), nullable=False)
    body: str = String(max_length=21, choices=list(Body), default=Body.SENATE.value, nullable=False)
    position: str = String(max_length=50, default=None, nullable=False)
    district: str = String(max_length=30, nullable=False)
    bio: str = String(max_length=100, nullable=False)
    pic: str = String(max_length=150, nullable=False)
    active: bool = Boolean(default=True, nullable=False)

class Senator(Model, LegislatorMixins, TermMixins):
    ormar_config = base_ormar_config.copy(tablename="senators")
        
class Representative(Model, LegislatorMixins, TermMixins):
    ormar_config = base_ormar_config.copy(tablename="representatives")

class Measure(Model, StatusMixins, TermMixins):
    ormar_config = base_ormar_config.copy(tablename="measures")

    id: int = Integer(primary_key=True)
    number: str = String(max_length=7, nullable=False)
    aisummary: str = Text()
    authors: List[Senator] = ManyToMany(Senator)
    type: str = String(
        max_length=20, 
        choices=list(MeasureType), 
        default=MeasureType.SENATE_PROJECT.value, 
        nullable=False
    )
    url: str = String(max_length=70, nullable=False)
    category: str = String(max_length=20, choices=list(MeasureCategory), nullable=True)
    filled_date: datetime = DateTime(nullable=False)

engine = sqlalchemy.create_engine(settings.db_url)