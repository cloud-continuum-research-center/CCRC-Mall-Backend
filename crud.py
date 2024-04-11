import os
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
import models, schemas
import uuid
import requests
import zipfile
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from urllib.parse import urlparse

# ID로 사용자 찾기
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# 모든 사용자 찾기
def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# 사용자 생성
def create_user(db: Session, user: schemas.UserSchema):
    db_user = models.User(email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 비밀번호 일치 확인
def verify_password(plain_password, hashed_password):
    return plain_password == hashed_password

# 모든 제품 목록 불러오기
def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def get_item_by_id(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

# ID로 제품 불러오기 (상세 보기)
def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

# 제품 생성
def create_item(db: Session, item: schemas.ItemSchema, image_path: str, video_path: str):
    db_item = models.Item(
        name=item.name,
        image=image_path,
        splat=None,  
        video=video_path,
        description=item.description,
        price=item.price,
        category_id=item.category_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


# 카테고리 별 제품 목록
def get_items_by_category(db: Session, category_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Item).filter(models.Item.category_id == category_id).offset(skip).limit(limit).all()

# 카테고리 생성
def create_item_category(db: Session, category: schemas.CategorySchema):
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def search_items_by_name(db: Session, name: str, skip: int = 0, limit: int = 100):
    return db.query(models.Item).filter(models.Item.name.ilike(f"%{name}%")).offset(skip).limit(limit).all()

# 데이터 삭제하기 - 제품 카테고리
def delete_item_category(db: Session, item_id: int, category_id: int):
    Item = db.query(models.Item).filter(models.Item.id == item_id).first()
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    Item.categories.remove(category)
    db.commit()
    db.refresh(Item)
    return Item

# 리뷰 조회
def get_reviews(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Review).offset(skip).limit(limit).all()

# 리뷰 생성
def create_review(db: Session, review: schemas.ReviewSchema):
    db_review = models.Review(user_id=review.user_id, item_id=review.item_id, content=review.content, star=review.star)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

# 제품별 리뷰 불러오기
def get_item_reviews(db: Session, item_id: int):
    return db.query(models.Review).filter(models.Review.item_id == item_id).all()

# 주문 생성
def create_order(db: Session, order: schemas.OrderSchema):
    db_order = models.Order(user_id=order.user_id, item_id=order.item_id, price=order.price, count=order.count, pay=order.pay)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_orders_by_user(db: Session, user_id: int):
    return db.query(models.Order).filter(models.Order.user_id == user_id).all()

def get_orders_by_item(db: Session, item_id: int):
    return db.query(models.Order).filter(models.Order.item_id == item_id).all()

def update_order_payment(db: Session, order_id: int):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if db_order:
        db_order.pay = True
        db.commit()
        db.refresh(db_order)
        return db_order
    return None

async def save_upload_file(file: UploadFile, folder: str):
    unique_filename = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[-1].lower()
    file_path = os.path.join(folder, f"{unique_filename}{file_extension}")

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path

s3_client = boto3.client(
    service_name='', region_name='',
    aws_access_key_id='', aws_secret_access_key=""
)
bucket_name = "3d-modeling-mall"

# GPU 서버 API 호출
def send_video(db: Session, item_id: int):
    try:
        db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
        server_url = 'http://163.180.117.36:20000'

        parsed_url = urlparse(db_item.video)
        path_components = parsed_url.path.split('/')
        file_name = path_components[-1]
        file_name_without_extension = file_name.split('.')[0]
        desired_part = file_name_without_extension

        data = {"video_filename": desired_part}
        response = requests.post(server_url, json=data)
        response.raise_for_status()
        return desired_part
    except requests.RequestException as e:
        print(f"An error occurred while sending image URL to another server: {e}")
        raise HTTPException(status_code=500, detail="Failed to send image URL to GPU server")

# S3 파일 업로드
def upload_image_to_s3(file: UploadFile) -> str:
    try:
        unique_filename = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1]
        s3_key = f"{unique_filename}.{file_extension}"
        file_body = file.file.read()
        response = s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=file_body)

        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        return s3_url

    except Exception as e:
        print(f"An error occurred while uploading file to S3: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload file to S3")

def upload_video_to_s3(video_file: UploadFile) -> str:
    try:
        unique_filename = str(uuid.uuid4())
        s3_key = f"{unique_filename}.zip"

        # 비디오 파일을 메모리에 압축
        with BytesIO() as zip_buffer:
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as z:
                z.writestr(video_file.filename, video_file.file.read())

            # 압축된 파일을 Amazon S3에 업로드
            zip_buffer.seek(0)
            s3_client.upload_fileobj(zip_buffer, bucket_name, s3_key)

        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        return s3_url

    except Exception as e:
        print(f"An error occurred while uploading video to S3: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload video to S3")

def upload_splat_to_s3(db: Session, item_id: int, splat_file: UploadFile):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    splat_path = upload_image_to_s3(splat_file)

    db_item.splat = splat_path
    db.commit()

    return db_item
