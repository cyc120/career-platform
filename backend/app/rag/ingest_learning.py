"""Ingest learning resources into ChromaDB for the learning plan agent."""
from app.rag.vector_store import get_learning_collection
from app.rag.embedding import get_embeddings

# Seed learning resource data — in production this comes from a CMS or external API
SEED_RESOURCES = [
    {
        "id": "lr-1",
        "title": "Python 高级编程实战",
        "category": "Python",
        "level": "中级",
        "duration": "40小时",
        "source": "慕课网",
        "url": "",
    },
    {
        "id": "lr-2",
        "title": "分布式系统设计原理",
        "category": "系统设计",
        "level": "高级",
        "duration": "60小时",
        "source": "极客时间",
        "url": "",
    },
    {
        "id": "lr-3",
        "title": "MySQL 性能优化实战",
        "category": "数据库",
        "level": "中级",
        "duration": "30小时",
        "source": "掘金",
        "url": "",
    },
    {
        "id": "lr-4",
        "title": "Redis 深度实战",
        "category": "数据库",
        "level": "中级",
        "duration": "25小时",
        "source": "掘金",
        "url": "",
    },
    {
        "id": "lr-5",
        "title": "Vue 3 全家桶实战",
        "category": "前端",
        "level": "初级",
        "duration": "50小时",
        "source": "B站",
        "url": "",
    },
    {
        "id": "lr-6",
        "title": "React 18 原理与实战",
        "category": "前端",
        "level": "中级",
        "duration": "45小时",
        "source": "极客时间",
        "url": "",
    },
    {
        "id": "lr-7",
        "title": "机器学习入门与实战",
        "category": "AI/ML",
        "level": "初级",
        "duration": "80小时",
        "source": "Coursera",
        "url": "",
    },
    {
        "id": "lr-8",
        "title": "深度学习与 NLP",
        "category": "AI/ML",
        "level": "高级",
        "duration": "90小时",
        "source": "斯坦福CS224n",
        "url": "",
    },
    {
        "id": "lr-9",
        "title": "数据可视化 ECharts 实战",
        "category": "数据分析",
        "level": "初级",
        "duration": "20小时",
        "source": "官方文档",
        "url": "",
    },
    {
        "id": "lr-10",
        "title": "产品经理方法论",
        "category": "产品",
        "level": "初级",
        "duration": "35小时",
        "source": "人人都是产品经理",
        "url": "",
    },
    {
        "id": "lr-11",
        "title": "Docker & Kubernetes 从入门到精通",
        "category": "DevOps",
        "level": "中级",
        "duration": "55小时",
        "source": "极客时间",
        "url": "",
    },
    {
        "id": "lr-12",
        "title": "软件测试自动化框架",
        "category": "测试",
        "level": "中级",
        "duration": "35小时",
        "source": "慕课网",
        "url": "",
    },
]


async def ingest_learning_resources():
    """Ingest seed learning resources into ChromaDB."""
    collection = get_learning_collection()

    ids = [r["id"] for r in SEED_RESOURCES]
    documents = [
        f"{r['title']} | 分类: {r['category']} | 难度: {r['level']} | "
        f"时长: {r['duration']} | 来源: {r['source']}"
        for r in SEED_RESOURCES
    ]
    metadatas = [
        {
            "title": r["title"],
            "category": r["category"],
            "level": r["level"],
            "duration": r["duration"],
            "source": r["source"],
        }
        for r in SEED_RESOURCES
    ]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    print(f"[RAG] Ingested {len(SEED_RESOURCES)} learning resources into ChromaDB.")
