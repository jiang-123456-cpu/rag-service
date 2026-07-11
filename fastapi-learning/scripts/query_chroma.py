"""Utility script to inspect/query a Chroma sqlite database.

Usage examples:
  python scripts/query_chroma.py --db chroma_db/chroma.sqlite3 --tables
  python scripts/query_chroma.py --db chroma_db/chroma.sqlite3 --sample collections --limit 5
  python scripts/query_chroma.py --db chroma_db/chroma.sqlite3 --schema collections
  python scripts/query_chroma.py --db chroma_db/chroma.sqlite3 --query "SELECT * FROM collections LIMIT 10"

This script is read-only (it opens the sqlite file in readonly mode) and is intended
for debugging and exploring the on-disk Chroma store.
"""
import chromadb
import os

# 1. 连接到你的 Chroma 数据库
# 自动解析项目根目录下的 chroma_db 路径（基于本脚本的父目录）
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
chroma_path = os.path.join(project_root, "chroma_db")
client = chromadb.PersistentClient(path=chroma_path)

# 2. 查看数据库里所有的集合（表）
collections = client.list_collections()
print("数据库里的集合列表：")
for idx, col in enumerate(collections):
    print(f"{idx + 1}. 集合名：{col.name}，数据条数：{col.count()}")

# 3. 如果有集合，查看第一个集合的详细数据
if collections:
    # 获取第一个集合
    collection = client.get_collection(name=collections[0].name)

    # 查看前5条数据（包括文本、向量、元数据）
    print("\n集合数据预览（前5条）：")
    preview = collection.peek(limit=5)
    print(preview)

    # 如果你想按条件查询数据，可以用query
    # 比如查询和"你要查的文本"最相似的3条数据
    results = collection.query(
        query_texts=["你要查的文本"],
        n_results=3
    )
    print("\n查询结果：")
    print(results)