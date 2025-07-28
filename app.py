import feedparser
import nltk
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests

# Tải xuống tài nguyên cần thiết cho NLTK để tách câu
# Thư mục 'punkt' sẽ được tạo trong dự án của bạn
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

# --- Khởi tạo ứng dụng FastAPI ---
app = FastAPI(
    title="Vietnam Market Overview API",
    description="API để lấy và phân tích thông tin thị trường từ các nguồn RSS của Investing.com.",
    version="1.0.0",
)

# --- Cấu hình CORS ---
# Cho phép tất cả các nguồn gốc để linh hoạt tối đa khi phát triển.
# Trong môi trường sản xuất, bạn nên giới hạn danh sách này.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức (GET, POST, etc.)
    allow_headers=["*"],  # Cho phép tất cả các tiêu đề
)


# --- URL của các nguồn cấp RSS ---
RSS_FEEDS = {
    "fundamental": "https://vn.investing.com/rss/market_overview_Fundamental.rss",
    "technical": "https://vn.investing.com/rss/market_overview_Technical.rss",
    "opinion": "https://vn.investing.com/rss/market_overview_Opinion.rss",
    "ideas": "https://vn.investing.com/rss/market_overview_investing_ideas.rss",
}

# --- Chức năng xử lý văn bản ---
def get_full_content(url: str) -> str:
    """
    Truy cập URL của bài viết và trích xuất toàn bộ nội dung văn bản.
    """
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tìm thẻ chứa nội dung chính (thường là 'article' hoặc một div có class cụ thể)
        # Selector này có thể cần điều chỉnh tùy theo cấu trúc của trang web
        article_body = soup.find('div', class_='article_body')
        if article_body:
            paragraphs = article_body.find_all('p')
            return "\n".join([p.get_text() for p in paragraphs])
        return ""
    except requests.RequestException as e:
        print(f"Lỗi khi lấy nội dung từ {url}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 5) -> list[str]:
    """
    Chia văn bản đầy đủ thành các đoạn nhỏ (chunks) gồm một số câu nhất định.
    """
    if not text:
        return []
    sentences = nltk.sent_tokenize(text)
    chunks = [" ".join(sentences[i:i + chunk_size]) for i in range(0, len(sentences), chunk_size)]
    return chunks

# --- Các điểm cuối (Endpoints) của API ---
@app.get("/", summary="Endpoint chào mừng", description="Hiển thị thông điệp chào mừng cho API.")
async def read_root():
    """
    Endpoint gốc trả về một thông điệp chào mừng đơn giản.
    """
    return {"message": "Chào mừng bạn đến với Vietnam Market Overview API!"}


@app.get("/rss/{feed_name}", summary="Lấy dữ liệu từ một nguồn RSS cụ thể")
async def get_rss_feed(feed_name: str, include_full_content: bool = False, chunk_content: bool = False):
    """
    Lấy các mục từ một nguồn cấp RSS được chỉ định.

    - **feed_name**: Tên của nguồn cấp (fundamental, technical, opinion, ideas).
    - **include_full_content**: Nếu `True`, sẽ cố gắng lấy toàn bộ nội dung bài viết.
    - **chunk_content**: Nếu `True` (và `include_full_content` cũng là `True`), nội dung đầy đủ sẽ được chia thành các đoạn.
    """
    if feed_name not in RSS_FEEDS:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguồn cấp RSS.")

    feed_url = RSS_FEEDS[feed_name]
    parsed_feed = feedparser.parse(feed_url)

    if parsed_feed.bozo:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi phân tích cú pháp RSS: {parsed_feed.bozo_exception}"
        )

    entries = []
    for entry in parsed_feed.entries:
        entry_data = {
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", "N/A"),
            "summary": entry.summary,
            "full_content": None,
            "content_chunks": None
        }
        
        if include_full_content:
            full_content = get_full_content(entry.link)
            entry_data["full_content"] = full_content
            if chunk_content and full_content:
                entry_data["content_chunks"] = chunk_text(full_content)

        entries.append(entry_data)
        
    return {"feed_name": feed_name, "entries": entries}

# --- Lệnh để chạy máy chủ (sử dụng khi phát triển cục bộ) ---
if __name__ == "__main__":
    # Chạy máy chủ Uvicorn trên cổng 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
