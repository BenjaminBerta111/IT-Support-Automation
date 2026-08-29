from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

app = Flask(__name__)

# Core system state to persist history across clean hits
SCRAPE_HISTORY = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        :root {
            --bg-color: #121212;
            --text-color: #e0e0e0;
            --border-color: #444444;
            --main-box-border: #f1c40f; /* High prominence yellow border from your mockup */
            --header-bg: #1f3a60; /* Soft water theme blue accent */
            --link-color: #3498db;
            --desc-color: #aaaaaa;
            --input-bg: #1e1e1e;
        }

        body { font-family: monospace; background: var(--bg-color); color: var(--text-color); margin: 0; display: flex; flex-direction: column; min-height: 100vh; }
        
        /* Top Banner Theme Styling */
        .top-banner { background: var(--header-bg); height: 60px; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; border-bottom: 3px solid #2980b9; position: relative; }
        .logo-area { display: flex; align-items: center; gap: 15px; color: #fff; font-size: 24px; font-weight: bold; }
        .duck-mascot { font-size: 14px; background: #f1c40f; color: #000; padding: 5px 10px; border-radius: 10px; font-weight: bold; cursor: help; }
        
        /* Workspace Setup */
        .workspace { display: flex; flex-grow: 1; position: relative; }
        
        /* Sticky Sidebar Setup */
        .sidebar { width: 170px; border-right: 3px solid var(--border-color); padding: 15px; box-sizing: border-box; position: sticky; top: 0; height: calc(100vh - 60px); display: flex; flex-direction: column; justify-content: space-between; }
        .menu-group { display: flex; flex-direction: column; gap: 8px; }
        
        .search-box { width: 100%; padding: 5px; font-family: monospace; box-sizing: border-box; background: var(--input-bg); color: var(--text-color); border: 1px solid var(--border-color); }
        .menu-btn { display: block; width: 100%; padding: 6px; font-family: monospace; cursor: pointer; text-align: left; background: var(--input-bg); color: var(--text-color); border: 1px solid var(--border-color); font-size: 13px; }
        .menu-btn.active { border-left: 5px solid #e74c3c; font-weight: bold; background: #2c3e50; }
        
        .history-list { font-size: 11px; color: #888; max-height: 100px; overflow-y: auto; padding-left: 5px; list-style-type: square; margin: 5px 0; }
        
        /* Main Payload Container */
        .main { flex-grow: 1; padding: 20px; max-width: 900px; border: 3px solid var(--main-box-border); margin: 20px; background: #080808; position: relative; }
        .header-labels { border-bottom: 2px dashed var(--border-color); padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; font-size: 16px; font-weight: bold; }
        .input-bar { margin-bottom: 25px; padding: 15px; background: var(--input-bg); border: 1px solid var(--border-color); }
        
        /* Clean Image Card Formatting */
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 15px; }
        .image-card { border: 1px solid var(--border-color); padding: 8px; text-align: center; background: var(--input-bg); transition: transform 0.1s; }
        .image-card:hover { transform: scale(1.02); border-color: #9b59b6; }
        .image-card img { max-width: 100%; max-height: 130px; object-fit: contain; display: block; margin: 0 auto 8px auto; background: #000; }
        .image-card a { font-size: 12px; color: var(--link-color); word-break: break-all; text-decoration: none; }
        
        /* Filtered Link Table Output */
        .link-row { padding: 12px 0; border-bottom: 1px solid var(--border-color); font-size: 14px; }
        .url-box { color: #2ecc71; font-weight: bold; text-decoration: underline; }
        .slash { color: #e67e22; font-weight: bold; margin: 0 10px; }
        .desc { color: var(--desc-color); }
        
        /* Polished UI Utilities */
        .scroll-top-btn { position: fixed; bottom: 60px; right: 30px; background: var(--input-bg); color: #e74c3c; border: 2px solid #e74c3c; padding: 8px 15px; font-family: monospace; font-weight: bold; cursor: pointer; border-radius: 4px; z-index: 100; text-decoration: none; font-size: 12px; }
        .scroll-top-btn:hover { background: #e74c3c; color: #fff; }
        
        .footer { background: #111; color: #666; font-size: 11px; text-align: left; padding: 15px 30px; border-top: 2px solid var(--border-color); margin-top: auto; }
    </style>
</head>
<body>

    <!-- Top Banner Element -->
    <div class="top-banner">
        <div class="logo-area">
            <span>Web Scraper</span>
            <!-- Fix: Massive hand-drawn globe graphic directly alongside title -->
            <img src="/static/globe.png" alt="Globe" style="height: 45px; width: auto; margin-left: 10px; vertical-align: middle;">
        </div>
        <!-- Fix: Swaps hardcoded text box for your hand-drawn duck illustration -->
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-family: monospace; color: #fff; font-weight: bold;">*quack*</span>
            <img src="/static/duck.png" alt="Duck Mascot" style="height: 50px; width: auto;">
        </div>
    </div>


    <div class="workspace">
        <!-- Sidebar Navigation Controls -->
        <div class="sidebar">
            <div class="menu-group">
                <span style="font-size: 11px; text-transform: uppercase; color: #666; font-weight: bold;">Controls</span>
                <input type="text" id="liveSearch" class="search-box" onkeyup="filterContent()" placeholder="Search content.">
                
                <span style="font-size: 11px; text-transform: uppercase; color: #666; font-weight: bold; margin-top: 10px;">History</span>
                <ul class="history-list">
                    {% for h_url in history %}
                    <li>{{ h_url }}</li>
                    {% else %}
                    <li style="list-style:none; margin-left:-5px;">No lookups yet</li>
                    {% endfor %}
                </ul>

                <span style="font-size: 11px; text-transform: uppercase; color: #666; font-weight: bold; margin-top: 10px;">Filter Logic</span>
                <button id="btn-links" class="menu-btn active" onclick="switchTab('links')">only links</button>
                <button id="btn-pictures" class="menu-btn" onclick="switchTab('pictures')">only pictures</button>
            </div>
            
            <div class="menu-group">
                <button class="menu-btn" style="text-align:center; border-color:#555;" onclick="alert('Light mode suppressed to protect your vision.')">Toggle Dark</button>
            </div>
        </div>
        
        <!-- Main Interface Sandbox -->
        <div class="main" id="topAnchor">
            <div class="header-labels">
                <span style="color: #2ecc71;">THIS IS THE LINK PORTAL</span>
                <span style="color: #e91e63; font-size:12px;">not google.com</span>
            </div>
            
            <div class="input-bar">
                <form method="POST">
                    <input type="text" name="url" placeholder="Paste bloated URL target here..." style="width: 72%; padding: 6px; background:#000; color:#fff; border:1px solid #555; font-family:monospace;" value="{{ target_url }}">
                    <button type="submit" style="padding: 6px 15px; background:#e74c3c; color:#fff; border:none; font-family:monospace; font-weight:bold; cursor:pointer;">Scrape Site</button>
                </form>
            </div>
            
            <!-- Link Matrix Output Target -->
            <div id="tab-links" class="tab-content active">
                {% for item in links %}
                <div class="link-row item-container">
                    <a class="url-box" href="{{ item.url }}" target="_blank">{{ item.text }}</a>
                    <span class="slash">/</span>
                    <span class="desc">{{ item.desc }}</span>
                </div>
                {% else %}
                    {% if target_url %}
                    <p style="color: #e74c3c;">No core distribution targets mapped from this layout filter string.</p>
                    {% endif %}
                {% endfor %}
            </div>
            
            <!-- Picture Grid Output Target -->
            <div id="tab-pictures" class="tab-content">
                <div class="image-grid">
                    {% for img in images %}
                    <div class="image-card item-container">
                        <img src="{{ img.url }}" alt="Resource content" onerror="this.parentElement.style.display='none';">
                        <a href="{{ img.url }}" target="_blank">{{ img.alt or "View Image Target" }}</a>
                    </div>
                    {% else %}
                        {% if target_url %}
                        <p style="color: #e74c3c;">No readable picture formats fetched from target asset array.</p>
                        {% endif %}
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <!-- Scroll Back to Top Action Utility Box -->
    <a href="#topAnchor" class="scroll-top-btn">Scroll To The Top</a>

    <!-- Integrated Footer Information Map -->
    <div class="footer">
        site framework data dashboard • created by local user running framework v2.1 • targets local python loopback 127.0.0.1
    </div>

    <script>
        // Sub-section Tab Switch Logic
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.sidebar .menu-btn').forEach(el => {
                if(el.id.startsWith('btn-')) el.classList.remove('active');
            });
            document.getElementById('tab-' + tabName).classList.add('active');
            document.getElementById('btn-' + tabName).classList.add('active');
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

# Serve local assets like your hand-drawn images directly from the project directory
@app.route('/static/<filename>')
def serve_static(filename):
    import os
    from flask import send_from_directory
    return send_from_directory(os.getcwd(), filename)

@app.route('/', methods=['GET', 'POST'])
def index():
    extracted_links = []
    extracted_images = []
    target_url = ""
    if request.method == 'POST':
        target_url = request.form.get('url', '')
        if target_url:
            # FIX: Extract clean domain string without technical array brackets
            try:
                from urllib.parse import urlparse
                domain = urlparse(target_url).netloc
                if domain and domain not in SCRAPE_HISTORY:
                    SCRAPE_HISTORY.insert(0, domain)
            except Exception:
                pass
            
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36'}
                response = requests.get(target_url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                dl_patterns = re.compile(r'(\.(exe|msi|zip|7z|tar|gz|dmg|onnx|gguf|rar|pkg)$|/releases/|/download)', re.IGNORECASE)
                trash_patterns = re.compile(r'(sign in|log in|privacy|terms|about|contact|features|pricing|security|skip to content|blog|feedback|support)', re.IGNORECASE)

                # Link Parsing Filter Loop
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

                # Image Grid Parsing Filter Loop
                for img_tag in soup.find_all('img'):
                    img_src = img_tag.get('src') or img_tag.get('data-src')
                    if img_src:
                        img_url = urljoin(target_url, img_src)
                        alt_text = img_tag.get('alt', '').strip()
                        if not img_url.startswith('data:image') and not any(x in img_url.lower() for x in ['pixel', 'spacer']):
                            extracted_images.append({
                                'url': img_url, 
                                'alt': alt_text[:40] or img_url.split('/')[-1][:30]
                            })
            except Exception as e:
                extracted_links.append({'text': 'Error fetching site', 'url': '#', 'desc': str(e)})
                
    return render_template_string(HTML_TEMPLATE, links=extracted_links, images=extracted_images, target_url=target_url, history=SCRAPE_HISTORY[:5])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)
