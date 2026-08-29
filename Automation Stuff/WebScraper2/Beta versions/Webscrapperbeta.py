from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #000000;
            --border-color: #666666;
            --row-border: #bbbbbb;
            --link-color: purple;
            --desc-color: #555555;
            --input-bg: #eeeeee;
        }

        [data-theme="dark"] {
            --bg-color: #121212;
            --text-color: #e0e0e0;
            --border-color: #888888;
            --row-border: #444444;
            --link-color: #bb86fc;
            --desc-color: #aaaaaa;
            --input-bg: #222222;
        }

        body { font-family: monospace; background: var(--bg-color); color: var(--text-color); margin: 0; display: flex; transition: background 0.1s, color 0.1s; }
        .sidebar { width: 150px; border-right: 3px solid var(--border-color); padding: 15px; height: 100vh; box-sizing: border-box; position: fixed; }
        .main { flex-grow: 1; padding: 15px; max-width: 800px; border: 3px solid red; margin: 10px 10px 10px 170px; }
        .header { border-bottom: 2px solid var(--border-color); padding-bottom: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; }
        .link-row { padding: 10px 0; border-bottom: 2px solid var(--row-border); font-size: 14px; }
        .url-box { color: var(--link-color); text-decoration: underline; font-weight: bold; }
        .slash { color: brown; font-weight: bold; margin: 0 10px; }
        .desc { color: var(--desc-color); }
        .input-bar { margin-bottom: 20px; padding: 10px; background: var(--input-bg); }
        
        .menu-btn { display: block; width: 100%; margin: 5px 0; padding: 5px; font-family: monospace; cursor: pointer; text-align: left; background: var(--input-bg); color: var(--text-color); border: 1px solid var(--border-color); }
        .menu-btn.active { border-left: 5px solid red; font-weight: bold; }
        .search-box { width: 100%; padding: 5px; margin-top: 10px; font-family: monospace; box-sizing: border-box; background: var(--input-bg); color: var(--text-color); border: 1px solid var(--border-color); }
        
        /* Layout Grid for Pictures view */
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; padding: 10px 0; }
        .image-card { border: 2px solid var(--row-border); padding: 5px; text-align: center; background: var(--input-bg); }
        .image-card img { max-width: 100%; max-height: 120px; object-fit: contain; display: block; margin: 0 auto 5px auto; }
        .image-card a { font-size: 11px; color: var(--link-color); word-break: break-all; }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
    <script>
        (function() {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {
                document.documentElement.setAttribute('data-theme', 'dark');
            }
        })();
    </script>
</head>
<body>
    <div class="sidebar">
        <h3>|||</h3>
        <p>i am options</p>
        <button class="menu-btn" onclick="toggleTheme()">Toggle Dark</button>
        <input type="text" id="liveSearch" class="search-box" onkeyup="filterContent()" placeholder="Search content...">
        
        <hr style="border-color: var(--row-border); margin: 15px 0;">
        
        <!-- Subsection Navigation Tabs -->
        <button id="btn-links" class="menu-btn active" onclick="switchTab('links')">only links</button>
        <button id="btn-pictures" class="menu-btn" onclick="switchTab('pictures')">only pictures</button>
    </div>
    
    <div class="main">
        <div class="header">
            <span style="color: green;">this is the link portal</span>
            <span style="color: pink;">not google.com</span>
        </div>
        <div class="input-bar">
            <form method="POST">
                <input type="text" name="url" placeholder="Paste bloated URL here..." style="width: 70%; padding: 5px;" value="{{ target_url }}">
                <button type="submit" style="padding: 5px 15px;">Scrape Site</button>
            </form>
        </div>
        
        <!-- Tab 1: Only Links view -->
        <div id="tab-links" class="tab-content active">
            {% for item in links %}
            <div class="link-row item-container">
                <a class="url-box searchable-text" href="{{ item.url }}" target="_blank">{{ item.text }}</a>
                <span class="slash">/</span>
                <span class="desc searchable-text">{{ item.desc }}</span>
            </div>
            {% else %}
                {% if target_url %}
                <p style="color: red;">No direct download files or release links discovered.</p>
                {% endif %}
            {% endfor %}
        </div>
        
        <!-- Tab 2: Only Pictures view -->
        <div id="tab-pictures" class="tab-content">
            <div class="image-grid">
                {% for img in images %}
                <div class="image-card item-container">
                    <img src="{{ img.url }}" alt="Scraped image" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\'http://w3.org\' width=\'100\' height=\'100\'><rect width=\'100\' height=\'100\' fill=\'gray\'/><text x=\'10\' y=\'50\' fill=\'white\'>Broken</text></svg>';">
                    <a class="searchable-text" href="{{ img.url }}" target="_blank">{{ img.alt or "View Image File" }}</a>
                </div>
                {% else %}
                    {% if target_url %}
                    <p style="color: red;">No pictures discovered on this page.</p>
                    {% endif %}
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            if (currentTheme === 'dark') {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            }
        }

        // Sub-section Tab Switch Logic
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.sidebar .menu-btn').forEach(el => {
                if(el.id.startsWith('btn-')) el.classList.remove('active');
            });
            
            document.getElementById('tab-' + tabName).classList.add('active');
            document.getElementById('btn-' + tabName).classList.add('active');
            
            // Clear current search filter when flipping tabs
            document.getElementById('liveSearch').value = '';
            filterContent();
        }

        // Unified Live Search Logic for both Links and Pictures
        function filterContent() {
            const query = document.getElementById('liveSearch').value.toLowerCase();
            const activeTab = document.querySelector('.tab-content.active');
            const items = activeTab.getElementsByClassName('item-container');
            
            for (let i = 0; i < items.length; i++) {
                const text = items[i].innerText.toLowerCase();
                items[i].style.display = text.includes(query) ? "" : "none";
            }
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    extracted_links = []
    extracted_images = []
    target_url = ""
    if request.method == 'POST':
        target_url = request.form.get('url', '')
        if target_url:
            #try:
                #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64)'}
                #response = requests.get(target_url, headers=headers, timeout=10)
                #soup = BeautifulSoup(response.text, 'html.parser')

            try:
                # Upgraded headers to perfectly mimic a standard desktop browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Referer': target_url  # Crucial for bypassing Danbooru/image-board filters
                }
                
                # Fetch the site data using our hidden identity
                response = requests.get(target_url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
    
                
                # Keywords to target files/releases
                dl_patterns = re.compile(r'(\.(exe|msi|zip|7z|tar|gz|dmg|onnx|gguf|rar|pkg)$|/releases/|/download)', re.IGNORECASE)
                trash_patterns = re.compile(r'(sign in|log in|privacy|terms|about|contact|features|pricing|security|skip to content|blog|feedback|support)', re.IGNORECASE)

                # Link Parser
                for a_tag in soup.find_all('a', href=True):
                    link_text = a_tag.get_text(strip=True)
                    link_url = urljoin(target_url, a_tag['href'])
                    
                    if (dl_patterns.search(link_url) or dl_patterns.search(link_text)) and not trash_patterns.search(link_text):
                        parent_text = a_tag.parent.get_text(strip=True)
                        description = parent_text.replace(link_text, "")[:100].strip() or "Direct download file link detected"
                        extracted_links.append({
                            'text': link_text[:60] or "Direct Payload File Target",
                            'url': link_url,
                            'desc': description
                        })

                # Picture Parser
                for img_tag in soup.find_all('img'):
                    img_src = img_tag.get('src') or img_tag.get('data-src')
                    if img_src:
                        img_url = urljoin(target_url, img_src)
                        alt_text = img_tag.get('alt', '').strip()
                        
                        # Cleaned filter: Only drop raw base64 data and tiny structural pixel spacers
                        if not img_url.startswith('data:image') and not any(x in img_url.lower() for x in ['pixel', 'spacer']):
                            extracted_images.append({
                                'url': img_url,
                                'alt': alt_text[:40] or img_url.split('/')[-1][:30]
                            })
                            
            except Exception as e:
                extracted_links.append({'text': 'Error fetching site', 'url': '#', 'desc': str(e)})
                
    return render_template_string(HTML_TEMPLATE, links=extracted_links, images=extracted_images, target_url=target_url)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)
