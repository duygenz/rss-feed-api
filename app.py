import feedparser
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from flask_cors import CORS

# Khởi tạo ứng dụng Flask
app = Flask(__name__)
# Bật CORS cho tất cả các domain. Để an toàn hơn trong production,
# bạn nên chỉ định rõ domain của frontend, ví dụ: CORS(app, origins="https://your-frontend-app.com")
CORS(app)

# Danh sách các RSS feed từ Investing.com
RSS_FEEDS = {
    'fundamental': 'https://vn.investing.com/rss/market_overview_Fundamental.rss',
    'technical': 'https://vn.investing.com/rss/market_overview_Technical.rss',
    'opinion': 'https://vn.investing.com/rss/market_overview_Opinion.rss',
    'ideas': 'https://vn.investing.com/rss/market_overview_investing_ideas.rss',
}

def scrape_article_content(url):
    """
    Hàm này nhận một URL của bài viết, tải nội dung HTML và
    trích xuất nội dung chính của bài viết bằng BeautifulSoup.
    Lưu ý: Cấu trúc HTML của mỗi trang web là khác nhau,
    selector có thể cần phải được điều chỉnh cho phù hợp.
    """
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  # Ném lỗi nếu request không thành công

        soup = BeautifulSoup(response.content, 'html.parser')

        # Selector này dùng để tìm nội dung chính của bài viết trên Investing.com
        # Đây là phần khó nhất và có thể cần thay đổi nếu trang web cập nhật layout
        article_body = soup.find('div', class_='article_body')

        if article_body:
            # Lấy một vài đoạn văn bản đầu tiên làm tóm tắt
            paragraphs = article_body.find_all('p')
            summary = ' '.join(p.get_text() for p in paragraphs[:3]) # Lấy 3 đoạn đầu
            return summary
        return "Không thể trích xuất nội dung."
    except requests.RequestException as e:
        return f"Lỗi khi tải trang: {e}"
    except Exception as e:
        return f"Lỗi khi scraping: {e}"

def parse_rss(feed_url, with_content=False):
    """
    Phân tích một RSS feed và trả về danh sách các bài viết.
    Nếu with_content=True, hàm sẽ thực hiện scraping để lấy nội dung tóm tắt.
    """
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        article = {
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'summary': entry.summary,
            'scraped_content': None # Khởi tạo giá trị
        }
        # Nếu có yêu cầu scraping, gọi hàm scrape_article_content
        if with_content:
            article['scraped_content'] = scrape_article_content(entry.link)
        articles.append(article)
    return articles

# --- Định nghĩa các API Endpoints ---

@app.route('/')
def index():
    """Endpoint chào mừng và hướng dẫn."""
    return jsonify({
        "message": "Chào mừng đến với API RSS Investing.com",
        "endpoints": {
            "/api/fundamental": "Phân tích cơ bản",
            "/api/technical": "Phân tích kỹ thuật",
            "/api/opinion": "Bài viết quan điểm",
            "/api/ideas": "Ý tưởng đầu tư",
        },
        "note": "Thêm `?scrape=true` vào cuối URL để lấy thêm nội dung tóm tắt từ trang gốc (chậm hơn)."
    })

@app.route('/api/<category>')
def get_feed(category):
    """
    Endpoint chung để lấy tin tức theo danh mục.
    Ví dụ: /api/fundamental
    """
    if category not in RSS_FEEDS:
        return jsonify({"error": "Danh mục không hợp lệ."}), 404

    # Kiểm tra query parameter 'scrape'
    from flask import request
    should_scrape = request.args.get('scrape', 'false').lower() == 'true'

    try:
        feed_url = RSS_FEEDS[category]
        articles = parse_rss(feed_url, with_content=should_scrape)
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Chạy app ở chế độ debug khi phát triển ở local
    # Gunicorn sẽ được dùng trong production
    app.run(debug=True, port=5001)

