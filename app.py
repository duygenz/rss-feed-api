from flask import Flask, jsonify, request
import feedparser
import requests
from datetime import datetime
import re
from flask_cors import CORS

app = Flask(**name**)
CORS(app)  # Cho phép CORS để frontend có thể gọi API

# Danh sách các RSS feeds

RSS_FEEDS = {
‘fundamental’: ‘https://vn.investing.com/rss/market_overview_Fundamental.rss’,
‘technical’: ‘https://vn.investing.com/rss/market_overview_Technical.rss’,
‘opinion’: ‘https://vn.investing.com/rss/market_overview_Opinion.rss’,
‘investing_ideas’: ‘https://vn.investing.com/rss/market_overview_investing_ideas.rss’
}

def clean_html(text):
“”“Xóa HTML tags khỏi text”””
if not text:
return “”
clean = re.compile(’<.*?>’)
return re.sub(clean, ‘’, text).strip()

def parse_rss_feed(url):
“”“Parse RSS feed và trả về danh sách bài viết”””
try:
# Thêm headers để tránh bị block
headers = {
‘User-Agent’: ‘Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36’
}

```
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    feed = feedparser.parse(response.content)
    
    articles = []
    for entry in feed.entries[:20]:  # Lấy 20 bài viết mới nhất
        article = {
            'title': clean_html(entry.get('title', '')),
            'link': entry.get('link', ''),
            'description': clean_html(entry.get('description', '')),
            'published': entry.get('published', ''),
            'author': entry.get('author', ''),
            'category': entry.get('category', '')
        }
        
        # Parse published date
        if entry.get('published_parsed'):
            try:
                article['published_date'] = datetime(*entry.published_parsed[:6]).isoformat()
            except:
                article['published_date'] = article['published']
        else:
            article['published_date'] = article['published']
        
        articles.append(article)
    
    return {
        'success': True,
        'feed_title': clean_html(feed.feed.get('title', '')),
        'feed_description': clean_html(feed.feed.get('description', '')),
        'total_articles': len(articles),
        'articles': articles
    }
    
except requests.RequestException as e:
    return {
        'success': False,
        'error': f'Network error: {str(e)}',
        'articles': []
    }
except Exception as e:
    return {
        'success': False,
        'error': f'Parsing error: {str(e)}',
        'articles': []
    }
```

@app.route(’/’)
def home():
“”“Trang chủ API”””
return jsonify({
‘message’: ‘RSS Feed API for Investing.com Vietnam’,
‘version’: ‘1.0’,
‘endpoints’: {
‘/feeds’: ‘Lấy tất cả feeds’,
‘/feeds/<category>’: ‘Lấy feed theo category (fundamental, technical, opinion, investing_ideas)’,
‘/search’: ‘Tìm kiếm bài viết (query parameter: q)’,
‘/latest’: ‘Lấy bài viết mới nhất từ tất cả feeds’
},
‘categories’: list(RSS_FEEDS.keys())
})

@app.route(’/feeds’)
def get_all_feeds():
“”“Lấy tất cả RSS feeds”””
limit = request.args.get(‘limit’, 10, type=int)
limit = min(limit, 50)  # Giới hạn tối đa 50 bài viết

```
all_feeds = {}
for category, url in RSS_FEEDS.items():
    feed_data = parse_rss_feed(url)
    if feed_data['success']:
        feed_data['articles'] = feed_data['articles'][:limit]
    all_feeds[category] = feed_data

return jsonify({
    'success': True,
    'timestamp': datetime.now().isoformat(),
    'feeds': all_feeds
})
```

@app.route(’/feeds/<category>’)
def get_feed_by_category(category):
“”“Lấy RSS feed theo category”””
if category not in RSS_FEEDS:
return jsonify({
‘success’: False,
‘error’: f’Category “{category}” not found’,
‘available_categories’: list(RSS_FEEDS.keys())
}), 404

```
limit = request.args.get('limit', 20, type=int)
limit = min(limit, 50)

feed_data = parse_rss_feed(RSS_FEEDS[category])
if feed_data['success']:
    feed_data['articles'] = feed_data['articles'][:limit]

feed_data['category'] = category
feed_data['timestamp'] = datetime.now().isoformat()

return jsonify(feed_data)
```

@app.route(’/latest’)
def get_latest_articles():
“”“Lấy bài viết mới nhất từ tất cả feeds”””
limit = request.args.get(‘limit’, 20, type=int)
limit = min(limit, 100)

```
all_articles = []

for category, url in RSS_FEEDS.items():
    feed_data = parse_rss_feed(url)
    if feed_data['success']:
        for article in feed_data['articles']:
            article['feed_category'] = category
            article['feed_title'] = feed_data['feed_title']
            all_articles.append(article)

# Sắp xếp theo thời gian published
try:
    all_articles.sort(key=lambda x: x.get('published_date', ''), reverse=True)
except:
    pass

return jsonify({
    'success': True,
    'timestamp': datetime.now().isoformat(),
    'total_articles': len(all_articles),
    'articles': all_articles[:limit]
})
```

@app.route(’/search’)
def search_articles():
“”“Tìm kiếm bài viết”””
query = request.args.get(‘q’, ‘’).strip()
if not query:
return jsonify({
‘success’: False,
‘error’: ‘Missing search query parameter “q”’
}), 400

```
limit = request.args.get('limit', 20, type=int)
limit = min(limit, 100)

matching_articles = []

for category, url in RSS_FEEDS.items():
    feed_data = parse_rss_feed(url)
    if feed_data['success']:
        for article in feed_data['articles']:
            # Tìm kiếm trong title và description
            if (query.lower() in article['title'].lower() or 
                query.lower() in article['description'].lower()):
                article['feed_category'] = category
                article['feed_title'] = feed_data['feed_title']
                matching_articles.append(article)

# Sắp xếp theo thời gian
try:
    matching_articles.sort(key=lambda x: x.get('published_date', ''), reverse=True)
except:
    pass

return jsonify({
    'success': True,
    'query': query,
    'timestamp': datetime.now().isoformat(),
    'total_results': len(matching_articles),
    'articles': matching_articles[:limit]
})
```

@app.route(’/health’)
def health_check():
“”“Health check endpoint”””
return jsonify({
‘status’: ‘healthy’,
‘timestamp’: datetime.now().isoformat()
})

@app.errorhandler(404)
def not_found(error):
return jsonify({
‘success’: False,
‘error’: ‘Endpoint not found’
}), 404

@app.errorhandler(500)
def internal_error(error):
return jsonify({
‘success’: False,
‘error’: ‘Internal server error’
}), 500

if **name** == ‘**main**’:
port = int(os.environ.get(‘PORT’, 5000))
app.run(host=‘0.0.0.0’, port=port, debug=False)
