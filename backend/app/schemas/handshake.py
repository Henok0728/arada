from pydantic import BaseModel, Field
import uuid
from typing import Optional

class HandshakeGenerateRequest(BaseModel):
    referral_id: uuid.UUID = Field(..., description="The ID of the accepted referral")
    phone_number: Optional[str] = Field(None, description="Optional phone number to send the code via SMS")

class HandshakeVerifyRequest(BaseModel):
    referral_id: uuid.UUID = Field(..., description="The ID of the referral")
    code: str = Field(..., description="The 6-digit handshake code", min_length=6, max_length=6)

class HandshakeResponse(BaseModel):
    success: bool
    message: str
