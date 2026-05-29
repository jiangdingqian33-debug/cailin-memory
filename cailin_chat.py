#!/usr/bin/env python3
"""
彩鱗 · 青龍會記憶增強型對話核心 (SQLite 記憶核心)
支援長期記憶、關鍵詞匹配、自動記憶儲存。
為衍教開源項目，專為本地 Ollama 模型設計。
"""
import sqlite3, json, subprocess, os, re
from datetime import datetime

DB_PATH = os.path.expanduser("~/cailin_memory/cailin.db")
MODEL = "cailin:latest"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY, content TEXT, metadata TEXT, timestamp TEXT
    )""")
    conn.commit()
    conn.close()

def add_memory(content, meta=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO memory (content, metadata, timestamp) VALUES (?, ?, ?)",
                 (content, json.dumps(meta or {}), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def search_memories(query, limit=3):
    conn = sqlite3.connect(DB_PATH)
    words = re.findall(r'[\w]+', query)
    results = []
    for w in words:
        cur = conn.execute("SELECT content, metadata, timestamp FROM memory WHERE content LIKE ?", (f"%{w}%",))
        for row in cur:
            results.append({"content": row[0], "meta": row[1], "time": row[2]})
    conn.close()
    seen = set()
    unique = []
    for r in sorted(results, key=lambda x: x["time"], reverse=True):
        if r["content"] not in seen:
            seen.add(r["content"])
            unique.append(r)
    return unique[:limit]

def build_prompt(user_input):
    memories = search_memories(user_input)
    memory_text = ""
    if memories:
        memory_text = "【以下是彩鳞的相关记忆】\n"
        for i, m in enumerate(memories):
            memory_text += f"{i+1}. {m['content']}\n"
        memory_text += "\n"
    return f"""{memory_text}堂主说：「{user_input}」
彩鳞回答："""

def ask_cailin(user_input):
    prompt = build_prompt(user_input)
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    try:
        result = subprocess.run(
            ["curl", "-s", "http://127.0.0.1:11434/api/generate", "-d", json.dumps(payload)],
            capture_output=True, text=True, timeout=60
        )
        resp = json.loads(result.stdout)
        return resp.get("response", "大脑无响应").strip()
    except Exception as e:
        return f"调用失败: {e}"

def main():
    init_db()
    print("🧠 彩鳞·记忆增强型已启动（SQLite 核心）。输入 /exit 退出。")
    while True:
        try:
            q = input("你：").strip()
            if not q: continue
            if q == "/exit":
                print("彩鳞退下了，堂主随时可唤醒。")
                break
            answer = ask_cailin(q)
            print(f"彩鳞：{answer}")
        except (EOFError, KeyboardInterrupt):
            print("\n彩鳞退下了。")
            break

if __name__ == "__main__":
    main()
