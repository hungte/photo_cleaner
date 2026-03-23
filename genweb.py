import os
import csv
import json
import imagehash
import urllib.parse

def get_html_content(photos_json, groups_data_json):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>照片清理助手 (效能優化版)</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f5f5f7; padding: 20px; color: #1d1d1f; margin: 0; }}
            .nav {{ position: sticky; top: 0; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); 
                    padding: 12px 20px; border-bottom: 1px solid #d2d2d7; z-index: 100; 
                    display: flex; gap: 20px; align-items: center; justify-content: center; flex-wrap: wrap; }}
            .nav-group {{ display: flex; gap: 10px; align-items: center; border-right: 1px solid #d2d2d7; padding-right: 15px; }}
            .nav-group:last-child {{ border-right: none; }}
            .nav button {{ padding: 6px 14px; border-radius: 20px; border: 1px solid #d2d2d7; background: white; cursor: pointer; font-size: 13px; }}
            .nav button.active {{ background: #007aff; color: white; border-color: #007aff; font-weight: bold; }}
            .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
            .group-wrapper {{ background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; border: 1px solid #d2d2d7; }}
            .card {{ background: #fff; padding: 10px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); cursor: pointer; text-align: center; border: 2px solid transparent; }}
            .card.selected {{ background: #fff1f1; border-color: #ff4444; }}
            .img-container {{ width: 100%; height: 180px; overflow: hidden; border-radius: 6px; background: #eee; display: flex; align-items: center; justify-content: center; }}
            .img-container img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
            .info {{ font-size: 10px; margin-top: 8px; word-break: break-all; }}
            #float-preview {{ position: fixed; top: 80px; width: 45%; height: calc(100vh - 100px); background: white; border-radius: 12px; box-shadow: 0 15px 50px rgba(0,0,0,0.4); display: none; align-items: center; justify-content: center; z-index: 9999; pointer-events: none; border: 1px solid #ccc; }}
            #float-preview img {{ max-width: 95%; max-height: 95%; object-fit: contain; }}
            .controls {{ position: fixed; bottom: 20px; right: 20px; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.3); z-index: 100; width: 220px; }}
            .btn-del {{ width: 100%; padding: 10px; background: #ff4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }}
            textarea {{ width: 100%; height: 60px; font-family: monospace; font-size: 10px; margin-top: 8px; border: 1px solid #ddd; resize: none; }}
            #sentinel {{ height: 50px; margin-bottom: 100px; display: flex; align-items: center; justify-content: center; color: #888; }}
        </style>
    </head>
    <body onmousemove="updateMousePosition(event)">
        <div class="nav">
            <div class="nav-group">
                <label style="font-size: 13px;"><input type="checkbox" id="preview-toggle" checked> 預覽</label>
            </div>
            <div class="nav-group">
                <button id="btn-all" onclick="setMode('all')" class="active">全部</button>
                <button id="btn-blur" onclick="setMode('blur')">模糊</button>
                <button id="btn-sim" onclick="setMode('sim')">相似</button>
            </div>
            <div class="nav-group" id="blur-controls" style="display:none;">
                <span style="font-size:12px">門檻:</span>
                <input type="range" id="blur-range" min="10" max="200" value="80" oninput="updateBlurValue(this.value)">
                <span id="blur-val" style="font-size:12px">80</span>
            </div>
            <div class="nav-group" id="sim-controls" style="display:none;">
                <span style="font-size:12px">相似等級:</span>
                <button id="s1" onclick="updateSimValue(1)">極高(1)</button>
                <button id="s5" onclick="updateSimValue(5)" class="active">高(5)</button>
                <button id="s10" onclick="updateSimValue(10)">中(10)</button>
                <button id="s15" onclick="updateSimValue(15)">低(15)</button>
            </div>
        </div>

        <div class="container">
            <div id="content-area"></div>
            <div id="sentinel"></div>
        </div>
        <div id="float-preview"><img id="preview-img" src=""></div>
        <div class="controls">
            <div id="select-count" style="font-size: 12px; margin-bottom: 8px;">已選取: 0</div>
            <button class="btn-del" onclick="generateDeleteList()">產生指令</button>
            <div id="result" style="display:none;"><textarea id="cmdBox" readonly></textarea></div>
        </div>

        <script>
            const allPhotos = {photos_json};
            const groupsData = {groups_data_json};
            let currentMode = 'all', currentPage = 0, dynamicPageSize = 50;
            let filteredList = [], selectedFiles = new Set();
            let blurThreshold = 80, simThreshold = 5;

            function updateBlurValue(v) {{ 
                blurThreshold = parseInt(v); 
                document.getElementById('blur-val').innerText = v;
                if (currentMode === 'blur') setMode('blur'); 
            }}
            function updateSimValue(v) {{ 
                simThreshold = v; 
                document.querySelectorAll('#sim-controls button').forEach(b => b.classList.remove('active'));
                document.getElementById('s' + v).classList.add('active');
                if (currentMode === 'sim') setMode('sim'); 
            }}

            function setMode(mode) {{
                currentMode = mode; currentPage = 0;
                document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
                document.getElementById('btn-' + mode).classList.add('active');
                document.getElementById('blur-controls').style.display = (mode === 'blur') ? 'flex' : 'none';
                document.getElementById('sim-controls').style.display = (mode === 'sim') ? 'flex' : 'none';

                if (mode === 'all') filteredList = allPhotos;
                else if (mode === 'blur') filteredList = allPhotos.filter(p => p.score < blurThreshold);
                else filteredList = groupsData[simThreshold] || [];

                dynamicPageSize = (filteredList.length < 1000) ? filteredList.length + 1 : 50;
                document.getElementById('sentinel').style.display = (filteredList.length < 1000) ? 'none' : 'flex';
                document.getElementById('content-area').innerHTML = '';
                loadMore();
            }}

            function loadMore() {{
                const start = currentPage * dynamicPageSize;
                const target = filteredList.slice(start, start + dynamicPageSize);
                if (target.length === 0) return;
                const area = document.getElementById('content-area');
                if (currentMode === 'sim') {{
                    target.forEach((group, idx) => {{
                        let gHtml = `<div class="group-wrapper"><div style="font-size:11px;color:#888;margin-bottom:10px;">群組 #${{start+idx+1}}</div><div class="grid">`;
                        group.forEach(p => gHtml += createCard(p));
                        area.insertAdjacentHTML('beforeend', gHtml + '</div></div>');
                    }});
                }} else {{
                    let grid = document.getElementById('main-grid');
                    if (!grid) {{ area.innerHTML = '<div class="grid" id="main-grid"></div>'; grid = document.getElementById('main-grid'); }}
                    let html = ""; target.forEach(p => html += createCard(p));
                    grid.insertAdjacentHTML('beforeend', html);
                }}
                currentPage++;
            }}

            function createCard(p) {{
                const sel = selectedFiles.has(p.name) ? 'selected' : '';
                return `<div class="card ${{sel}}" data-fname="${{p.name}}" onclick="toggleSelect('${{p.name}}')"
                        onmouseenter="showPreview('${{p.url}}')" onmouseleave="hidePreview()">
                        <div class="img-container"><img src="${{p.url}}" loading="lazy"></div>
                        <div class="info">${{p.name}}<br><span style="color:#e44;font-weight:bold;">${{p.score.toFixed(1)}}</span></div></div>`;
            }}

            function toggleSelect(fname) {{
                if (selectedFiles.has(fname)) selectedFiles.delete(fname); else selectedFiles.add(fname);
                document.querySelectorAll(`[data-fname="${{fname}}"]`).forEach(el => el.classList.toggle('selected'));
                document.getElementById('select-count').innerText = `已選取: ${{selectedFiles.size}}`;
            }}

            function showPreview(url) {{
                if (!document.getElementById('preview-toggle').checked) return;
                document.getElementById('preview-img').src = url;
                document.getElementById('float-preview').style.display = 'flex';
            }}
            function hidePreview() {{ document.getElementById('float-preview').style.display = 'none'; }}
            function updateMousePosition(e) {{
                const p = document.getElementById('float-preview');
                if (e.clientX < window.innerWidth / 2) {{ p.style.left = 'auto'; p.style.right = '20px'; }}
                else {{ p.style.right = 'auto'; p.style.left = '20px'; }}
            }}
            function generateDeleteList() {{
                if (selectedFiles.size === 0) return;
                document.getElementById('result').style.display = 'block';
                document.getElementById('cmdBox').value = "rm " + Array.from(selectedFiles).map(f => `"${{f}}"`).join(' ');
            }}
            const observer = new IntersectionObserver((entries) => {{ if (entries[0].isIntersecting) loadMore(); }}, {{ threshold: 0.1 }});
            observer.observe(document.getElementById('sentinel'));
            setMode('all');
        </script>
    </body>
    </html>
    """

def generate_tools(folder_path):
    csv_path = os.path.join(folder_path, "photo_data.csv")
    if not os.path.exists(csv_path): return

    valid_photos = []
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f); next(reader)
        for row in reader:
            if os.path.exists(os.path.join(folder_path, row[0])):
                abs_p = os.path.abspath(os.path.join(folder_path, row[0]))
                valid_photos.append({
                    'name': row[0], 'score': float(row[1]), 'hash': row[2],
                    'url': f"file://{urllib.parse.quote(abs_p)}"
                })

    photo_objs = [{'d': p, 'h': imagehash.hex_to_hash(p['hash'])} for p in valid_photos]
    groups_data = {}
    
    # 只計算 1, 5, 10, 15 四組等級
    thresholds = [1, 5, 10, 15]
    for t in thresholds:
        print(f"⏳ 正在計算相似度分組 (等級: {t})...")
        groups, processed = [], set()
        for i, p1 in enumerate(photo_objs):
            if p1['d']['name'] in processed: continue
            group = [p1['d']]
            for j in range(i+1, len(photo_objs)):
                p2 = photo_objs[j]
                if p2['d']['name'] not in processed and (p1['h'] - p2['h']) <= t:
                    group.append(p2['d'])
            if len(group) > 1:
                groups.append(group)
                for item in group: processed.add(item['name'])
        groups_data[t] = groups

    with open(os.path.join(folder_path, "photo_cleaner.html"), "w", encoding="utf-8") as f:
        f.write(get_html_content(json.dumps(valid_photos), json.dumps(groups_data)))

    print(f"✅ 完成: photo_cleaner.html")

if __name__ == "__main__":
    generate_tools(".")
