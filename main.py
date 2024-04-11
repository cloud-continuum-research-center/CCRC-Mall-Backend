from typing import List

from fastapi import Depends, FastAPI, HTTPException, APIRouter
from sqlalchemy.orm import Session
from fastapi import File, UploadFile
from fastapi.responses import FileResponse
from fastapi import Form
from urllib.parse import urlparse

import crud, models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

UPLOAD_DIR = "./photo"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

api_router = APIRouter(prefix="/api")

# 회원가입
@api_router.post("/join/", response_model=schemas.UserSchema)
def create_user(user: schemas.UserSchema, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="User with this ID already registered")
    return crud.create_user(db=db, user=user)

# 로그인
@api_router.post("/login")
def login(user: schemas.UserSchema, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user or not crud.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return True

# 모든 사용자 보기
@api_router.get("/users/", response_model=List[schemas.UserSchema])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# 상품 등록
@api_router.post("/items/")
async def create_item(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    image: UploadFile = File(None),
    video: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    try:
        # 이미지와 동영상을 S3에 업로드하고 경로 획득
        image_path = None
        video_path = None

        if image:
            image_path = crud.upload_image_to_s3(image)
        if video:
            video_path = crud.upload_video_to_s3(video)

        # 데이터베이스에 아이템 생성 및 이미지 및 동영상 경로 저장
        db_item = crud.create_item(
            db,
            schemas.ItemSchema(
                name=name,
                description=description,
                price=price,
                category_id=category_id,
                image_path=image_path,
                video_path=video_path  # 이 부분이 추가됐습니다.
            ),
            image_path,
            video_path
        )

        return {"item": db_item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

   

# 모든 상품 목록 조회
@api_router.get("/items/", response_model=List[schemas.ItemResponseModel])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

# 카테고리 별 상품 목록 조회
@api_router.get("/items/category/{category_id}", response_model=List[schemas.ItemResponseModel])
def get_items_by_category(category_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items_by_category(db, category_id=category_id, skip=skip, limit=limit)
    return items

# 제품 명 검색
@api_router.get("/items/search/{item_name}", response_model=List[schemas.ItemResponseModel])
def search_items_by_name(item_name: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.search_items_by_name(db, name=item_name, skip=skip, limit=limit)
    return items

# 상품 상세 보기
@api_router.get("/items/{item_id}", response_model=schemas.ItemResponseModel)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id=item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    return item

# 카테고리 생성
@api_router.post("/categorys", response_model=schemas.CategorySchema)
def create_item_category(category: schemas.CategorySchema, db: Session = Depends(get_db)):
    return crud.create_item_category(db=db, category=category)

# 전체 리뷰 불러오기
@api_router.get("/reviews/", response_model=List[schemas.ReviewSchema])
def read_reviews(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    reviews = crud.get_reviews(db, skip=skip, limit=limit)
    return reviews

# 리뷰 생성
@api_router.post("/items/{item_id}/reviews/", response_model=schemas.ReviewSchema)
def create_review_for_item(item_id: int, review: schemas.ReviewSchema, db: Session = Depends(get_db)):
    return crud.create_review(db=db, review=review)

# 제품별 리뷰 불러오기
@api_router.get("/items/{item_id}/reviews/", response_model=List[schemas.ReviewSchema])
def read_item_reviews(item_id: int, db: Session = Depends(get_db)):
    reviews = crud.get_item_reviews(db=db, item_id=item_id)
    return reviews

# 주문하기
@api_router.post("/order/", response_model=schemas.OrderSchema)
def create_order(order: schemas.OrderSchema, db: Session = Depends(get_db)):
    item = crud.get_item_by_id(db, item_id=order.item_id)

    user = crud.get_user_by_id(db, user_id=order.user_id)

    item.price = item.price * order.count

    db_order = crud.create_order(db=db, order=order)
    return db_order

# 유저ID로 주문 내역 조회
@api_router.get("/orders/user/{user_id}", response_model=List[schemas.OrderSchema])
def get_orders_by_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    orders = crud.get_orders_by_user(db, user_id=user_id)
    
    return orders

# 상품ID로 주문 내역 조회
# item.user_id와 조회하는 Id가 다를 경우 접근 불가
@api_router.get("/orders/items/{item_id}", response_model=List[schemas.OrderSchema])
def get_orders_by_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item_by_id(db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    orders = crud.get_orders_by_item(db, item_id=item_id)
    return orders

# 결제 완료
@api_router.put("/order/pay/{order_id}", response_model=schemas.OrderSchema)
def update_order_payment(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.update_order_payment(db, order_id=order_id)
    if db_order:
        return db_order
    else:
        raise HTTPException(status_code=404, detail="Order not found")
    
'''
# .jpeg 업로드
@api_router.get("/items/{item_id}/image")
def get_image_by_item_id(item_id: int, db: Session = Depends(get_db)):
    media = crud.get_media_by_item_id(db, item_id)
    
    if media and media.image:
        return FileResponse(media.image, media_type="image/jpeg")
    else:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    
# .mp4 다운로드
@api_router.get("/items/{item_id}/video")
def get_video_by_item_id(item_id: int, db: Session = Depends(get_db)):
    media = crud.get_media_by_item_id(db, item_id)
    
    if media and media.video:
        return FileResponse(media.video, media_type="video/mp4")
    else:
        raise HTTPException(status_code=404, detail="동영상을 찾을 수 없습니다.")

# .splat 업로드
@api_router.put("items/{item_id}/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".splat"):
        raise HTTPException(status_code=400, detail="올바른 확장자가 아닙니다. '.splat' 파일만 업로드 가능합니다.")
    
    return {"filename": file.filename}
'''

@api_router.get("/items/{item_id}/multi/")
async def get_item_multi_paths(item_id: int, db: Session = Depends(get_db)):
    # 데이터베이스에서 item_id에 해당하는 상품을 가져옵니다.
    db_item = crud.get_item(db, item_id=item_id)
    
    # 상품이 없을 경우 404 오류를 반환합니다.
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # 상품의 이미지, 동영상, .splat 파일의 경로를 반환합니다.
    return {
        "image_path": db_item.image,
        "video_path": db_item.video,
        "splat_path": db_item.splat
    }

@api_router.get("/items/{item_id}/image/")
async def get_item_multi_paths(item_id: int, db: Session = Depends(get_db)):
    # 데이터베이스에서 item_id에 해당하는 상품을 가져옵니다.
    db_item = crud.get_item(db, item_id=item_id)
    
    # 상품이 없을 경우 404 오류를 반환합니다.
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # 상품의 이미지, 동영상, .splat 파일의 경로를 반환합니다.
    return db_item.image


@api_router.put("/items/{item_id}/splat")
def update_item_splat(
    item_id: int,
    splat_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # 상품의 .splat 파일을 업데이트합니다.
        db_item = crud.update_item_splat(db, item_id, splat_file)
        return {"item": db_item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GPU 서버 API 호출
@app.post("/send/{item_id}")
def send_video(item_id: int, db: Session = Depends(get_db)):
    try:
        return crud.send_video(db, item_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send video: {str(e)}")


app.include_router(api_router)