"""Seed data script for development."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.security import hash_password
from app.db.mysql import AsyncSessionLocal
from sqlalchemy import text


SEED_USERS = [
    ("admin", "admin@career.com", "admin123"),
    ("demo", "demo@career.com", "demo123"),
]

SEED_JOBS = [
    ("Java开发工程师", "华为", "通信/IT", "深圳", "25k-50k",
     "负责Java后端服务开发与维护，参与系统架构设计。",
     "熟悉Java/Spring Boot、MySQL、Redis、微服务架构。"),
    ("测试工程师", "京东", "互联网/IT", "北京", "15k-30k",
     "负责软件测试工作，编写测试用例，搭建自动化测试框架。",
     "熟悉测试方法论、Selenium/Appium、Python/Shell脚本。"),
    ("运维工程师", "网易", "互联网/IT", "广州", "18k-35k",
     "负责服务器运维、自动化部署、监控告警系统搭建。",
     "熟悉Linux、Docker/K8s、CI/CD、Shell/Python。"),
    ("UI/UX设计师", "小米", "通信/硬件", "北京", "18k-35k",
     "负责产品界面设计与用户体验优化，制作交互原型。",
     "熟悉Figma/Sketch、设计系统、用户研究、交互设计。"),
    ("算法工程师", "百度", "互联网/IT", "北京", "30k-60k",
     "负责推荐/搜索/NLP算法研发，模型训练与调优。",
     "熟悉Python/C++、深度学习框架、推荐系统/NLP/CV。"),
    ("安全工程师", "360", "安全/IT", "北京", "25k-50k",
     "负责Web安全、渗透测试、安全审计与漏洞修复。",
     "熟悉Web安全攻防、渗透测试工具、WAF/IDS。"),
]

SEED_PROMOTIONS = [
    ("Java开发工程师", "Java架构师", '["系统架构","性能调优","分布式","团队管理"]', 5, "promotion"),
    ("Java开发工程师", "技术总监", '["技术战略","团队管理","项目管理","业务理解"]', 8, "promotion"),
    ("测试工程师", "测试主管", '["测试管理","自动化架构","性能测试","团队管理"]', 4, "promotion"),
    ("测试工程师", "质量保证工程师", '["质量体系","流程改进","风险管控"]', 3, "transfer"),
]


async def seed():
    async with AsyncSessionLocal() as db:
        for username, email, pwd in SEED_USERS:
            hashed = hash_password(pwd)
            await db.execute(
                text(
                    "INSERT OR IGNORE INTO users (username, email, password_hash) "
                    "VALUES (:u, :e, :h)"
                ),
                {"u": username, "e": email, "h": hashed},
            )

        for title, company, industry, city, salary, desc, reqs in SEED_JOBS:
            await db.execute(
                text(
                    "INSERT OR IGNORE INTO jobs (job_title, company, industry, city, "
                    "salary_range, job_description, requirements, publish_date) "
                    "VALUES (:t, :c, :i, :ci, :s, :d, :r, DATE('now'))"
                ),
                {"t": title, "c": company, "i": industry, "ci": city, "s": salary, "d": desc, "r": reqs},
            )

        for cur, nxt, skills, yrs, ttype in SEED_PROMOTIONS:
            await db.execute(
                text(
                    "INSERT OR IGNORE INTO promotion_transition "
                    "(current_role, next_role, required_skills, years_exp, transition_type) "
                    "VALUES (:cr, :nr, :sk, :yr, :tt)"
                ),
                {
                    "cr": cur, "nr": nxt,
                    "sk": skills, "yr": yrs, "tt": ttype,
                },
            )

        await db.commit()
        print("Seed data inserted successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
