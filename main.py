import os
import bcrypt
from jose import jwt,JWTError
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 连接数据库
load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 数据库表结构
class DBArticle(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    content = Column(Text)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=True)

# 自动建表
Base.metadata.create_all(bind=engine)

app = FastAPI()



def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="请先登录"
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="无效或已过期的 token"
        )

    username = payload.get("sub")

    if username is None:
        raise HTTPException(
            status_code=401,
            detail="token 中没有用户信息"
        )

    return username

# 允许跨域（让 HTML 页面能请求后端）
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Article(BaseModel):
    title: str
    content: str
    category:str=""

@app.get("/")
def home():
    return {"message": "你好，这是我的第一个接口！"}

@app.get("/me")
def read_me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}

@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"你好 {name}，欢迎来到我的博客！"}

# 从数据库查所有文章
@app.get("/articles")
def get_articles():
    db = SessionLocal()
    articles = db.query(DBArticle).all()
    db.close()
    return {"articles": articles}

#用户表(数据库)
class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True)
    password = Column(String(200))

#用户注册（接口接收的数据格式）
class User(BaseModel):
    username: str
    password: str

@app.post("/users")
def register(user: User):
    password=user.password.encode("utf-8")
    hashed_password=bcrypt.hashpw(
        password,
        bcrypt.gensalt()
    )
    db = SessionLocal()
    existing_user=db.query(DBUser).filter(
        DBUser.username==user.username
        ).first()
    if existing_user is not None:
        db.close()
        raise HTTPException(
            status_code=400,detail="该用户名已注册！"
            )
    db_user = DBUser(username=user.username, password=hashed_password.decode("utf-8"))
    db.add(db_user)
    db.commit()
    db.close()
    return {"message": "注册成功"}

@app.post("/login")
def login(user:User):
    db = SessionLocal()
    existing_user = db.query(DBUser).filter(
        DBUser.username == user.username
        ).first()
    if existing_user is  None:
        db.close()
        raise HTTPException(
            status_code=401,detail="该用户不存在！请重新输入~"
        )
    password1=user.password.encode("utf-8")
    password2=existing_user.password.encode("utf-8")
    lemp=bcrypt.checkpw(password1,password2)
    if not lemp:
        db.close()
        raise HTTPException(
              status_code=401,detail="用户名或密码错误！请重新输入"
        )
    db.close()
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload={
        "sub":user.username,
        "exp":expire_time
    }
    access_token=jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return {
    "access_token": access_token,
    "token_type": "bearer"
    }

# 往数据库加文章
@app.post("/articles")
def create_article(article: Article,current_user:str=Depends(get_current_user)):
    db = SessionLocal()
    db_article = DBArticle(title=article.title, content=article.content, category=article.category)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    db.close()
    return {"message": "文章添加成功", "article": db_article}

# 删除文章
@app.delete("/articles/{article_id}")
def delete_article(article_id: int,current_user:str=Depends(get_current_user)):
    db = SessionLocal()
    db_article = db.query(DBArticle).filter(DBArticle.id == article_id).first()
    if db_article is None:
        db.close()
        raise HTTPException(status_code=404, detail="文章不存在")

    db.delete(db_article)
    db.commit()
    db.close()
    return {"message": "文章删除成功"}

# 编辑文章标题和内容
@app.put("/articles/{article_id}")
def update_article(article_id: int, article: Article,current_user:str=Depends(get_current_user)):
    db = SessionLocal()
    db_article = db.query(DBArticle).filter(DBArticle.id == article_id).first()
    if db_article is None:
        db.close()
        raise HTTPException(status_code=404, detail="文章不存在")
    db_article.title = article.title
    db_article.content = article.content
    db_article.category = article.category
    db.commit()
    db.close()
    return {"message": "文章修改成功"}

@app.get("/articles/{article_id}")
def get_article(article_id: int,current_user:str=Depends(get_current_user)):
    db=SessionLocal()
    db_article=db.query(DBArticle).filter(DBArticle.id==article_id).first()
    if db_article is None:
        db.close()
        raise HTTPException(status_code=404,detail=" 文章不存在")
    db.close()
    return{"message":db_article}