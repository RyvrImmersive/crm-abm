from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class CRMCompany(BaseModel):
    id: str
    entity_type: str = "company"
    name: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    website: Optional[str] = None
    research_notes: Optional[str] = None
    crm_score: Optional[float] = None
    industry_score: Optional[float] = None
    total_score: Optional[float] = None

class CRMContact(BaseModel):
    id: str
    entity_type: str = "contact"
    firstname: str
    lastname: str
    email: Optional[str] = None
    company_id: Optional[str] = None
    title: Optional[str] = None
    meeting_engagement: Optional[bool] = None
    crm_score: Optional[float] = None
    industry_score: Optional[float] = None
    total_score: Optional[float] = None

class CRMDeal(BaseModel):
    id: str
    entity_type: str = "deal"
    dealname: str
    amount: Optional[float] = None
    company_id: Optional[str] = None
    contact_id: Optional[str] = None
    stage: Optional[str] = None
    crm_score: Optional[float] = None
    industry_score: Optional[float] = None
    total_score: Optional[float] = None

class ScoreComponents(BaseModel):
    signals: List[str] = []
    weights: Dict[str, float] = {}

class ScoreResult(BaseModel):
    crm_score: float
    industry_score: float
    total_score: float
    components: ScoreComponents
    entity_id: str
    entity_type: str
