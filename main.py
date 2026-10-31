import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 连接数据库
load_dotenv()
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

#用户表
class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True)
    password = Column(String(200))

# 往数据库加文章
@app.post("/articles")
def create_article(article: Article):
    db = SessionLocal()
    db_article = DBArticle(title=article.title, content=article.content, category=article.category)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    db.close()
    return {"message": "文章添加成功", "article": db_article}

# 删除文章
@app.delete("/articles/{article_id}")
def delete_article(article_id: int):
    db = SessionLocal()
    db_article = db.query(DBArticle).filter(DBArticle.id == article_id).first()
    if db_article is None:
        db.close()
        raise HTTPException(status_code=404, detail="文章不存在")

    db.delete(db_article)
    db.commit()
    db.close()
    return {"message": "文章删除成功"}

#用户注册
class User(BaseModel):
    username: str
    password: str

@app.post("/users")
def register(user: User):
    db = SessionLocal()
    db_user = DBUser(username=user.username, password=user.password)
    db.add(db_user)
    db.commit()
    db.close()
    return {"message": "注册成功"}


# 编辑文章标题和内容
@app.put("/articles/{article_id}")
def update_article(article_id: int, article: Article):
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
def get_article(article_id: int):
    db=SessionLocal()
    db_article=db.query(DBArticle).filter(DBArticle.id==article_id).first()
    if db_article is None:
        db.close()
        raise HTTPException(status_code=404,detail=" 文章不存在")
    db.close()
    return{"message":db_article}