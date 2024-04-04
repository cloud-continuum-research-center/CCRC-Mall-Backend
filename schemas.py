from typing import Optional
from fastapi import File, UploadFile
from pydantic import BaseModel


class UserSchema(BaseModel):
    id: Optional[int] = None
    email: str
    password: str

class ItemSchema(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    price: float
    category_id: int
    image: Optional[UploadFile] = File(None)
    splat: Optional[UploadFile] = File(None)
    video: Optional[UploadFile] = File(None)

class ItemResponseModel(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    price: float
    category_id: int
    image: Optional[str]
    splat: Optional[str]
    video: Optional[str]
    
class OrderSchema(BaseModel):
    id: Optional[int] = None
    user_id: int
    item_id: int
    price: int
    count: int
    pay: bool

class CategorySchema(BaseModel):
    id: Optional[int] = None
    name: str

class ReviewSchema(BaseModel):
    id: Optional[int] = None
    content: str
    star: int
    user_id: int
    item_id: int