# CCRC-Mall-Backend

---

### 기술 스택
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)

---
### Getting Started (Installation)

```bash
pip install "fastapi[all]"
pip install "uvicorn[standard]"
```


### Start Server
```bash
uvicorn main:app --reload
```

### Configuring S3 Credentials

In order to store and access files using S3 in this project, you'll need to set up your credentials securely. For security reasons, these credentials should be stored in a `crud.py` file at the root of the project directory.

```python
s3_client = boto3.client(
    service_name='', region_name='',
    aws_access_key_id='', aws_secret_access_key=""
)
```