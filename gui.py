from flask import Flask, render_template, request, jsonify, send_file
from facebook_archive_viewer import load_posts, filter_posts
import csv
from datetime import datetime

app = Flask(__name__)
PORT = 5897  # Uncommon port

# Initialize posts once at startup (no decorator needed)
POSTS = load_posts()
print(f"Loaded {len(POSTS)} posts")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts')
def get_filtered_posts():
    # Get filter parameters
    keyword = request.args.get('keyword', '').lower()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = int(request.args.get('page', 1))
    per_page = 50

    # Apply filters
    filtered = filter_posts(
        POSTS,
        keyword=keyword if keyword else None,
        start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else None,
        end_date=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    )

    # Paginate results
    total = len(filtered)
    start = (page-1)*per_page
    end = start + per_page

    return jsonify({
        'posts': [{
            'timestamp': p['timestamp'].isoformat(),
            'content': p['content']
        } for p in filtered[start:end]],
        'total': total,
        'page': page
    })

@app.route('/export')
def export_posts():
    # Get filter parameters
    keyword = request.args.get('keyword', '')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Apply filters
    filtered = filter_posts(
        POSTS,
        keyword=keyword if keyword else None,
        start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else None,
        end_date=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    )

    # Generate CSV
    filename = 'facebook_posts_export.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Content'])
        for post in filtered:
            writer.writerow([
                post['timestamp'].isoformat(),
                post['content']
            ])

    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(port=PORT, debug=False)
