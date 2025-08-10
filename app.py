from flask import Flask, jsonify
from flask_cors import CORS
import feedparser

app = Flask(__name__)
CORS(app)  # Cho phép tất cả các domain

RSS_FEEDS = [
    "https://cafef.vn/thi-truong-chung-khoan.rss",
    "https://vneconomy.vn/chung-khoan.rss",
    "https://vneconomy.vn/tai-chinh.rss",
    "https://vneconomy.vn/thi-truong.rss",
    "https://vneconomy.vn/nhip-cau-doanh-nghiep.rss",
    "https://vneconomy.vn/tin-moi.rss",
    "https://cafebiz.vn/rss/cau-chuyen-kinh-doanh.rss"
]

def parse_feed(url):
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries:
            entries.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "published": entry.get("published", "")
            })
        return entries
    except Exception as e:
        return [{"error": str(e)}]

@app.route('/api/news', methods=['GET'])
def get_news():
    all_news = []
    for url in RSS_FEEDS:
        all_news.extend(parse_feed(url))
    return jsonify(all_news)

@app.route('/', methods=['GET'])
def home():
    return "News Aggregator API - /api/news"

if __name__ == '__main__':
    app.run(debug=True)