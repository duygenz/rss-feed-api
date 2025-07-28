import feedparser
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from flask_cors import CORS

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Kích hoạt CORS cho tất cả các domain trên tất cả các route
# Điều này cho phép các ứng dụng web khác có thể gọi API của bạn
CORS(app)

# Danh sách các URL của RSS feed
RSS_FEEDS = {
    'fundamental': 'https://vn.investing.com/rss/market_overview_Fundamental.rss',
    'technical': 'https://vn.investing.com/rss/market_overview_Technical.rss',
    'opinion': 'https://vn.investing.com/rss/market_overview_Opinion.rss',
    'ideas': 'https://vn.investing.com/rss/market_overview_investing_ideas.rss'
}

def scrape_article_content(url):
    """
    Hàm này thực hiện scraping để lấy nội dung chính của bài viết từ URL.
    Lưu ý: Cấu trúc của mỗi trang web là khác nhau, bạn có thể cần điều chỉnh
    các bộ chọn (selector) của BeautifulSoup cho phù hợp.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Ném lỗi nếu request không thành công
        soup = BeautifulSoup(response.content, 'html.parser')

        # Ví dụ về cách tìm nội dung bài viết.
        # Bạn cần "Inspect" (Kiểm tra) trang web đích để tìm đúng selector.
        # Ví dụ này giả định nội dung nằm trong một thẻ <article>
        article_body = soup.find('article')
        if article_body:
            return article_body.get_text(strip=True)
        return "Không thể lấy được nội dung chi tiết."
    except requests.exceptions.RequestException as e:
        return f"Lỗi khi truy cập URL: {e}"
    except Exception as e:
        return f"Lỗi không xác định khi scraping: {e}"

@app.route('/')
def index():
    """Endpoint chính, cung cấp thông tin về các API có sẵn."""
    return jsonify({
        "message": "Chào mừng đến với API tổng hợp tin tức từ Investing.com",
        "available_feeds": list(RSS_FEEDS.keys())
    })

@app.route('/feed/<string:feed_name>')
def get_feed(feed_name):
    """
    Endpoint động để lấy dữ liệu từ một RSS feed cụ thể.
    Ví dụ: /feed/technical
    """
    if feed_name not in RSS_FEEDS:
        return jsonify({"error": "Không tìm thấy feed này."}), 404

    # Lấy dữ liệu từ URL của RSS feed
    feed = feedparser.parse(RSS_FEEDS[feed_name])
    posts = []

    # Lặp qua từng mục tin trong feed
    for entry in feed.entries:
        posts.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published if hasattr(entry, 'published') else 'Không có ngày xuất bản',
            'summary': entry.summary,
            # Bật dòng dưới đây nếu bạn muốn scraping nội dung của từng bài viết
            # 'content': scrape_article_content(entry.link)
        })

    return jsonify(posts)

if __name__ == '__main__':
    # Chạy ứng dụng ở chế độ debug khi được thực thi trực tiếp
    app.run(debug=True)
