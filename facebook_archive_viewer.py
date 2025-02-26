import os
import json
from datetime import datetime
from bs4 import BeautifulSoup
import dateutil.parser  # More flexible date parsing

DEBUG = False  # Set to True to see parsing details
# Configuration - Adjust this path according to your archive structure
POSTS_DIR = "fb_archive/posts"

def load_posts():
    posts = []
    total_files = 0
    processed_files = 0
    try:
        for filename in os.listdir(POSTS_DIR):
            if filename.endswith('.html'):
                total_files += 1
                filepath = os.path.join(POSTS_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        processed_files += 1
                        # Find post containers based on your HTML structure
                        post_containers = soup.find_all('div', class_='pam')
                        if DEBUG:
                            print(f"\nFile: {filename}")
                            print(f"Found {len(post_containers)} post containers")
                        for i, container in enumerate(post_containers):
                            try:
                                # Extract timestamp from the <a> tag
                                time_tag = container.find('a', href=lambda x: x and 'facebook.com/dyi/' in x)
                                timestamp_str = time_tag.text.strip() if time_tag else None
                                # Handle different date formats
                                timestamp = dateutil.parser.parse(timestamp_str) if timestamp_str else None
                                # Extract content from the _2pin divs
                                content_divs = container.find_all('div', class_='_2pin')
                                content_parts = []
                                for div in content_divs:
                                    # Skip divs containing "Updated" text
                                    if 'Updated' in div.text:
                                        continue
                                    # Collect text from all other _2pin divs
                                    content_parts.extend(div.stripped_strings)
                                content = ' '.join(content_parts).strip()
                                if timestamp and content:
                                    posts.append({
                                        'timestamp': timestamp,
                                        'content': content,
                                        'source_file': filename
                                    })
                                    if DEBUG:
                                        print(f"\nPost {i+1} in {filename}")
                                        print(f"Timestamp: {timestamp}")
                                        print(f"Content: {content[:200]}...")
                                        print("="*50)
                            except Exception as post_error:
                                if DEBUG:
                                    print(f"Error processing post {i+1} in {filename}: {post_error}")
                                    print("Container HTML snippet:")
                                    print(container.prettify()[:500])
                                continue
                except Exception as file_error:
                    print(f"Error processing file {filename}: {file_error}")
                    continue
        print(f"\nProcessed {processed_files}/{total_files} HTML files")
        print(f"Total posts found: {len(posts)}")
        return sorted(posts, key=lambda x: x['timestamp'])
    except FileNotFoundError:
        print(f"Directory not found: {POSTS_DIR}")
        return []
    except Exception as e:
        print(f"Critical error: {e}")
        return []

def load_json_posts():
    posts = []
    total_files = 0
    processed_files = 0
    try:
        for filename in os.listdir(POSTS_DIR):
            if filename.endswith('.json'):
                total_files += 1
                filepath = os.path.join(POSTS_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        processed_files += 1
                        # Facebook's structure varies - try different keys
                        post_list = data.get('posts', data.get('status_updates', []))
                        for post in post_list:
                            try:
                                # Handle different timestamp formats
                                timestamp_str = post.get('timestamp')
                                if timestamp_str:
                                    if 'T' in timestamp_str:
                                        timestamp = datetime.fromisoformat(timestamp_str)
                                    else:
                                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S%z")
                                else:
                                    timestamp = datetime(1970, 1, 1)  # Fallback
                                # Handle different content structures
                                content = ""
                                if 'data' in post:
                                    for entry in post['data']:
                                        content += entry.get('post', '') + " "
                                else:
                                    content = post.get('title', post.get('text', 'No content'))
                                posts.append({
                                    'timestamp': timestamp,
                                    'content': content.strip(),
                                    'raw': post
                                })
                            except Exception as post_error:
                                print(f"Error processing post in {filename}: {post_error}")
                                continue
                except Exception as file_error:
                    print(f"Error processing file {filename}: {file_error}")
                    continue
        print(f"Processed {processed_files}/{total_files} JSON files successfully")
        return sorted(posts, key=lambda x: x['timestamp'])
    except FileNotFoundError:
        print(f"Directory not found: {POSTS_DIR}")
        return []
    except Exception as e:
        print(f"Critical error: {e}")
        return []

def filter_posts(posts, keyword=None, start_date=None, end_date=None):
    filtered = []
    for post in posts:
        match = True
        if keyword:
            match &= keyword.lower() in post['content'].lower()
        if start_date:
            match &= post['timestamp'] >= start_date
        if end_date:
            match &= post['timestamp'] <= end_date
        if match:
            filtered.append(post)
    return sorted(filtered, key=lambda x: x['timestamp'])

def main():
    posts = load_posts()
    print(f"Loaded {len(posts)} posts")

    current_filter = {
        'keyword': None,
        'start_date': None,
        'end_date': None
    }

    while True:
        print("\nCurrent filters:")
        print(f"1. Keyword: {current_filter['keyword']}")
        print(f"2. Start date: {current_filter['start_date']}")
        print(f"3. End date: {current_filter['end_date']}")
        print("\nOptions:")
        print("1. Set keyword filter")
        print("2. Set start date (YYYY-MM-DD)")
        print("3. Set end date (YYYY-MM-DD)")
        print("4. Clear filters")
        print("5. Show posts")
        print("6. Exit")

        choice = input("Enter choice: ")

        try:
            if choice == '1':
                current_filter['keyword'] = input("Enter keyword: ").strip() or None
            elif choice == '2':
                date_str = input("Enter start date (YYYY-MM-DD): ")
                current_filter['start_date'] = datetime.strptime(date_str, "%Y-%m-%d") if date_str else None
            elif choice == '3':
                date_str = input("Enter end date (YYYY-MM-DD): ")
                current_filter['end_date'] = datetime.strptime(date_str, "%Y-%m-%d") if date_str else None
            elif choice == '4':
                current_filter = {'keyword': None, 'start_date': None, 'end_date': None}
            elif choice == '5':
                filtered = filter_posts(posts,
                                        keyword=current_filter['keyword'],
                                        start_date=current_filter['start_date'],
                                        end_date=current_filter['end_date'])
                print(f"\nDisplaying {len(filtered)} posts:")
                for post in filtered:
                    print(f"\n[{post['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}]")
                    print(post['content'])
                    print("-" * 50)
            elif choice == '6':
                break
            else:
                print("Invalid choice")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
