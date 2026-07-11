from pydantic import BaseModel,Field
from typing import Optional
class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")

class KnowledgeBaseUpdate(BaseModel):
    id: int = Field(..., gt=0, description="知识库ID")
    name: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")

class KnowledgeBaseDelete(BaseModel):
    id: int = Field(..., gt=0, description="知识库ID")

