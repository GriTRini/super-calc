from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import json
import os
import datetime
import re # 정규표현식 (링크 검사)

router = APIRouter(prefix="/board")
templates = Jinja2Templates(directory="templates")

# 게시글 저장 파일
DB_FILE = "posts.json"

def load_posts():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_posts(posts):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

# [보안] 링크 포함 여부 검사 함수
def has_links(text):
    # http://, https://, www., .com, .net, .co.kr 등 감지
    url_pattern = re.compile(r'(http|https)://|www\.|[a-zA-Z0-9-]+\.(com|net|org|co\.kr|kr)')
    return bool(url_pattern.search(text))

# 1. 게시판 목록
@router.get("/")
async def board_list(request: Request):
    posts = load_posts()
    # 최신순 정렬
    posts.sort(key=lambda x: x['id'], reverse=True)
    return templates.TemplateResponse("board_list.html", {"request": request, "posts": posts})

# 2. 글쓰기 페이지 (GET)
@router.get("/write")
async def board_write_form(request: Request):
    return templates.TemplateResponse("board_write.html", {"request": request})

# 3. 글 저장 (POST)
@router.post("/write")
async def board_write_action(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    password: str = Form(...), # 수정/삭제용 비번
    
    # [상세 조건 입력]
    device_name: str = Form(...),
    gongsi: int = Form(default=0),
    store_subsidy: int = Form(default=0),
    addon_detail: str = Form(...), # 부가서비스 내용
    
    content: str = Form(...)
):
    # 1. 링크 검사 (보안)
    if has_links(content) or has_links(title) or has_links(addon_detail):
        return templates.TemplateResponse("board_write.html", {
            "request": request,
            "error": "🚨 보안 정책상 외부 링크(URL)는 포함할 수 없습니다. 텍스트로만 작성해주세요."
        })

    posts = load_posts()
    new_id = 1
    if posts:
        new_id = posts[-1]['id'] + 1
        
    new_post = {
        "id": new_id,
        "title": title,
        "author": author,
        "password": password,
        "device_name": device_name,
        "gongsi": gongsi,
        "store_subsidy": store_subsidy,
        "addon_detail": addon_detail,
        "content": content,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    posts.append(new_post)
    save_posts(posts)
    
    return RedirectResponse(url="/board", status_code=303)

# 4. 게시글 상세 보기
@router.get("/{post_id}")
async def board_detail(request: Request, post_id: int):
    posts = load_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        return RedirectResponse(url="/board")
        
    return templates.TemplateResponse("board_detail.html", {"request": request, "post": post})