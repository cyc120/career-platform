"""Import jobs from data.json into SQLite database."""
import json
import sqlite3
import re
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "data.json")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "career_platform.db")


def annual_to_monthly_salary(min_sal, max_sal):
    """Convert annual salary to monthly 'Xk-Yk' format."""
    if not min_sal and not max_sal:
        return "面议"
    min_monthly = int(min_sal / 12 / 1000) if min_sal else 0
    max_monthly = int(max_sal / 12 / 1000) if max_sal else 0
    if min_monthly <= 0:
        return f"{max_monthly}k以下"
    return f"{min_monthly}k-{max_monthly}k"


def parse_location(location_str):
    """Parse 'city-district' format, return city and full location."""
    if not location_str:
        return "", ""
    parts = location_str.split("-", 1)
    city = parts[0].strip() if parts else location_str.strip()
    return city, location_str.strip()


def extract_job_fields(job_details):
    """Extract job_description and requirements from structured job_details text."""
    desc_parts = []
    req_parts = []

    if not job_details:
        return "", ""

    lines = job_details.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if "岗位职责" in line or "1. 岗位职责" in line:
            current_section = "desc"
            continue
        elif "任职要求" in line or "2. 任职要求" in line:
            current_section = "req"
            continue
        elif "公司福利" in line or "其他说明" in line:
            current_section = None
            continue

        if current_section == "desc":
            clean = re.sub(r'^\s*\d+\)\s*', '', line).strip()
            if clean:
                desc_parts.append(clean)
        elif current_section == "req":
            clean = re.sub(r'^\s*\d+\)\s*', '', line).strip()
            if clean:
                req_parts.append(clean)

    description = "；".join(desc_parts) if desc_parts else job_details[:500]
    requirements = "；".join(req_parts) if req_parts else ""

    return description, requirements


def main():
    print(f"Loading data from: {DATA_PATH}")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Total records to import: {len(data)}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Clear existing seed data
    cur.execute("DELETE FROM jobs")
    print("Cleared existing jobs data.")

    batch = []
    batch_size = 500

    for item in data:
        title = (item.get("job_title") or "").strip()
        company = (item.get("company_name") or "").strip()
        industry = (item.get("industry") or "").strip()
        city, location = parse_location(item.get("location") or "")
        min_sal = item.get("min_salary", 0) or 0
        max_sal = item.get("max_salary", 0) or 0
        salary_range = annual_to_monthly_salary(min_sal, max_sal)
        company_scale = (item.get("company_scale") or "").strip()
        job_details = item.get("job_details") or ""
        company_desc = (item.get("company_description") or "").strip()
        description, requirements = extract_job_fields(job_details)

        batch.append((
            title, company, industry, city, salary_range,
            description, requirements, company_scale,
            company_desc, job_details
        ))

        if len(batch) >= batch_size:
            cur.executemany(
                """INSERT INTO jobs (job_title, company, industry, city, salary_range,
                   job_description, requirements, publish_date, company_scale,
                   company_description, job_details)
                   VALUES (?, ?, ?, ?, ?, ?, ?, DATE('now'), ?, ?, ?)""",
                batch
            )
            batch = []
            print(f"  Inserted {batch_size}...")

    if batch:
        cur.executemany(
            """INSERT INTO jobs (job_title, company, industry, city, salary_range,
               job_description, requirements, publish_date, company_scale,
               company_description, job_details)
               VALUES (?, ?, ?, ?, ?, ?, ?, DATE('now'), ?, ?, ?)""",
            batch
        )

    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    print(f"Import complete. Total jobs in DB: {count}")
    conn.close()


if __name__ == "__main__":
    main()
