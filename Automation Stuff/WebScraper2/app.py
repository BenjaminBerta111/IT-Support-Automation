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

        
        .toggle-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            margin-top: 8px;
            padding: 2px 5px;
        }

        .toggle-label {
            color: #ffffff;
            font-size: 13px;
        }

        .switch {
            position: relative;
            display: inline-block;
            width: 38px;
            height: 20px;
        }

        .switch input { 
            opacity: 0; width: 0; height: 0; 
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: #222222;
            border: 1px solid #444444;
            transition: .2s;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 12px;
            width: 12px;
            left: 3px;
            bottom: 3px;
            background-color: #555555;
            transition: .2s;
        }

        input:checked + .slider {
            border-color: #f1c40f; /* Uses your high-prominence yellow border variable */
        }

        input:checked + .slider:before {
            transform: translateX(18px);
            background-color: #f1c40f; /* Turns knob yellow when flipped ON */
        }



        body { font-family: monospace; background: var(--bg-color); color: var(--text-color); margin: 0; display: flex; flex-direction: column; min-height: 100vh; }
        
        /* Top Banner Theme Styling */
        .top-banner { background: var(--header-bg); height: 60px; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; border-bottom: 3px solid #2980b9; position: relative; }
        .logo-area { display: flex; align-items: center; gap: 15px; color: #fff; font-size: 24px; font-weight: bold; }
        .duck-mascot { font-size: 14px; background: #f1c40f; color: #000; padding: 5px 10px; border-radius: 10px; font-weight: bold; cursor: help; }
        
        /* /* Workspace Setup */
        .workspace { 
            display: flex; 
            flex-grow: 1; 
            position: relative; 
            width: 100%;
            overflow-x: hidden; /* Prevents any ugly horizontal scrollbars */
        }

        /* /* Sticky Sidebar Setup */
        .sidebar { 
            width: 180px; 
            min-width: 180px; /* This absolutely forces the sidebar to NEVER shrink or move */
            max-width: 180px; /* Keeps it exactly this size permanently */
            border-right: 3px solid var(--border-color); 
            padding: 15px; 
            box-sizing: border-box; 
            position: sticky; 
            top: 0; 
            height: calc(100vh - 60px); 
            display: flex;
            flex-direction: column;
        }



        .search-box { width: 100%; padding: 5px; font-family: monospace; box-sizing: border-box; background: var(--input-bg); color: var(--text-color); border: 1px solid var(--border-color); }
        .menu-btn { display: block; width: 100%; padding: 6px; font-family: monospace; cursor: pointer; text-align: left; background: var(--input-bg); color: var(--text-color); border: 1px solid var(--border-color); font-size: 13px; }
        .menu-btn.active { border-left: 5px solid #e74c3c; font-weight: bold; background: #2c3e50; }
        
        .history-list { font-size: 11px; color: #888; max-height: 100px; overflow-y: auto; padding-left: 5px; list-style-type: square; margin: 5px 0; }
        
        /* Main Payload Container */
        .main { flex-grow: 1; padding: 20px; max-width: 900px; border: 3px solid var(--main-box-border); margin: 20px; background: #080808; position: relative; }
        .header-labels { border-bottom: 2px dashed var(--border-color); padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; font-size: 16px; font-weight: bold; }
        .input-bar { margin-bottom: 25px; padding: 15px; background: var(--input-bg); border: 1px solid var(--border-color); }
        
        /* Fixes the stretching layout glitch when expanding/collapsing sections */
        #text-view, .text-portal-container {
            flex: 1;
            min-width: 45%;
            max-width: 50%; /* Stops text from crowding the link portal */
            box-sizing: border-box;
        }

        .link-portal-container, #links-view {
            flex: 1;
            min-width: 45%;
            box-sizing: border-box;
        }



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
                
                <div class="toggle-container">
                    <span class="toggle-label">include text</span>
                    <label class="switch">
                        <input type="checkbox" id="textToggle" onchange="toggleTextView()">
                        <span class="slider"></span>
                    </label>
                </div>

            </div>
            
           
        </div>
        



        
        <div id="text-view" class="text-portal-container" style="display: none;">
            <h3>Structured Article Content</h3>
            {% for item in page_texts %}
                {% if item.type in ['h1', 'h2', 'h3'] %}
                    <!-- Render headers with a bold, distinct appearance -->
                    <h4 style="color: #ffcc00; margin-top: 15px;">{{ item.content }}</h4>
                {% else %}
                    <!-- Render paragraphs as standard body text block elements -->
                    <p style="color: #ffffff; line-height: 1.5;">{{ item.content }}</p>
                {% endif %}
            {% endfor %}
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
        
            <button onclick="downloadLinksText()" class="download-btn" style="margin-top: 10px; background: #f1c40f; color: #000; border: none; padding: 5px 10px; cursor: pointer; font-family: monospace; font-weight: bold;">
                Export Links (.txt)
            </button>            

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
    <button onclick="document.querySelector('.top-banner').scrollIntoView({behavior: 'smooth'})">Scroll To The Top</button>


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

        function toggleTextView() {
            const isChecked = document.getElementById('textToggle').checked;
            const textPanel = document.getElementById('text-view') || document.querySelector('.text-portal-container');
            
            if (isChecked) {
                textPanel.style.display = 'block';  // Show text panel when switch is ON
            } else {
                textPanel.style.display = 'none';   // Hide text panel when switch is OFF
            }
        }


        function downloadLinksText() {
            // 1. Gather all links from your dashboard portal
            var links = document.querySelectorAll('.main a, .workspace a, #links-view a');

            var textData = '--- SCRAPED LINKS LOG ---\\n\\n';
            
            // 2. Safe, old-school loop to process the logs
            for (var i = 0; i < links.length; i++) {
                var item = links[i];
                if (item.href && item.href.indexOf('javascript:') === -1) {
                    var title = item.innerText ? item.innerText.trim() : 'Link';
                    var position = i + 1;
                    textData += '[' + position + '] ' + title + '\\nURL: ' + item.href + '\\n\\n';
                }
            }
            
            // 3. Create the file without using bracketed properties that confuse Python
            var fileData = [];
            fileData.push(textData);
            var blob = new Blob(fileData); 
            
            var anchor = document.createElement('a');
            anchor.download = 'scraped_links.txt';
            anchor.href = window.URL.createObjectURL(blob);
            
            // 4. Force download trigger
            document.body.appendChild(anchor);
            anchor.click();
            document.body.removeChild(anchor);
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
    extracted_text = []
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
                    href = a_tag['href']
                    link_text = a_tag.get_text(strip=True).lower()

                    if href.startswith('#') or href.startswith('javascript:'):
                         continue

                    if (dl_patterns.search(href) or dl_patterns.search(link_text)) and not trash_patterns.search(link_text):
                        parent_text = a_tag.parent.get_text(strip=True)
                        description = parent_text.replace(link_text, "")[:100].strip() or "Direct download file link detected"
                        extracted_links.append({
                            'text': link_text[:60] or "Direct Payload File Target", 
                            'url': href, 
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


                for element in soup.find_all(['h1', 'h2', 'h3', 'p']):
                    text_content = element.get_text(strip=True)
                    
                    # Skip empty elements or strings that are too short to be useful
                    if len(text_content) > 3:
                        extracted_text.append({
                            'type': element.name, # Stores whether it is an h1, h2, or p tag
                            'content': text_content
                        })     

            except Exception as e:
                extracted_links.append({'text': 'Error fetching site', 'url': '#', 'desc': str(e)})
                        
    return render_template_string(HTML_TEMPLATE, links=extracted_links, images=extracted_images, target_url=target_url, page_texts=extracted_text, history=SCRAPE_HISTORY[:5])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)
