from flask import Flask, request, jsonify
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import requests, uuid

app = Flask(__name__)
COLLECTION = "derjiao_memory"
client = QdrantClient(host="127.0.0.1", port=6333)

if not client.collection_exists(COLLECTION):
    client.create_collection(COLLECTION, VectorParams(size=1024, distance=Distance.COSINE))

def get_embedding(text: str):
    resp = requests.post("http://127.0.0.1:11434/api/embeddings", json={"model": "bge-m3", "prompt": text})
    return resp.json()["embedding"]

@app.route('/add', methods=['POST'])
def add():
    data = request.json
    emb = get_embedding(data['content'])
    client.upsert(COLLECTION, [PointStruct(id=str(uuid.uuid4()), vector=emb, payload={"content": data['content'], "meta": data.get('meta', {})})])
    return jsonify({"status": "ok"})

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    emb = get_embedding(query)
    # 使用 query_points 方法进行语义检索
    results = client.query_points(collection_name=COLLECTION, query=emb, limit=5)
    return jsonify([{"content": r.payload['content'], "score": r.score} for r in results.points])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
