from flask import Flask, request, jsonify
import subprocess, os, tempfile, uuid

app = Flask(__name__)
UPLOAD_DIR = os.path.expanduser("~/derjiao_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/parse', methods=['POST'])
def parse_file():
    """接收文件路径或URL，返回解析后的文本内容"""
    data = request.json
    filepath = data.get('filepath', '')
    
    if not filepath or not os.path.exists(os.path.expanduser(filepath)):
        return jsonify({"error": "文件不存在", "filepath": filepath}), 400
    
    full_path = os.path.expanduser(filepath)
    ext = os.path.splitext(full_path)[1].lower()
    
    try:
        if ext in ['.pdf']:
            # 使用 pdftotext 解析PDF
            result = subprocess.run(['pdftotext', full_path, '-'], capture_output=True, text=True, timeout=30)
            content = result.stdout
        
        elif ext in ['.docx']:
            # 使用 python-docx 解析Word文档
            try:
                from docx import Document
                doc = Document(full_path)
                content = '\n'.join([p.text for p in doc.paragraphs])
            except ImportError:
                # 备选方案：用 LibreOffice 转换
                tmp_dir = tempfile.mkdtemp()
                subprocess.run(['libreoffice', '--headless', '--convert-to', 'txt', '--outdir', tmp_dir, full_path], timeout=30)
                txt_file = os.path.join(tmp_dir, os.path.basename(full_path).replace(ext, '.txt'))
                if os.path.exists(txt_file):
                    with open(txt_file, 'r') as f:
                        content = f.read()
                else:
                    content = "Word文档解析失败"
        
        elif ext in ['.txt', '.md', '.py', '.html', '.css', '.js']:
            # 文本文件直接读取
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        
        elif ext in ['.png', '.jpg', '.jpeg']:
            # 图片OCR识别
            result = subprocess.run(['tesseract', full_path, 'stdout', '-l', 'chi_tra+eng'], capture_output=True, text=True, timeout=30)
            content = result.stdout.strip()
        
        else:
            content = f"暂不支持的格式：{ext}"
        
        # 截断过长内容
        if len(content) > 10000:
            content = content[:10000] + "\n... (内容过长，已截断)"
        
        return jsonify({"status": "ok", "content": content, "length": len(content), "filepath": filepath})
    
    except Exception as e:
        return jsonify({"error": str(e), "filepath": filepath}), 500

@app.route('/list', methods=['GET'])
def list_files():
    """列出上传目录中的所有文件"""
    files = os.listdir(UPLOAD_DIR)
    return jsonify({"files": files, "count": len(files)})

if __name__ == '__main__':
    print("📂 衍教文件解析服务已启动 (端口5002)...")
    app.run(host='127.0.0.1', port=5002)
