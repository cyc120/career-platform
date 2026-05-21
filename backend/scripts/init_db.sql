-- Career Service AI Platform - SQLite Schema

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    industry VARCHAR(255),
    city VARCHAR(100),
    salary_range VARCHAR(100),
    company_scale VARCHAR(50),
    job_description TEXT,
    requirements TEXT,
    publish_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    profile_data TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    match_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS career_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    target_position VARCHAR(255),
    target_company VARCHAR(255),
    timeline_months INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    plan_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS job_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    profile_data TEXT,
    summary VARCHAR(1024),
    core_skills TEXT,
    career_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS promotion_transition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    current_role VARCHAR(255) NOT NULL,
    next_role VARCHAR(255) NOT NULL,
    required_skills TEXT,
    years_exp INTEGER,
    transition_type VARCHAR(50) DEFAULT 'promotion',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS matching_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    industry VARCHAR(255),
    city VARCHAR(100),
    match_score REAL,
    report_data TEXT,
    publish_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS learning_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    target_job VARCHAR(255),
    plan_type VARCHAR(50) DEFAULT '长期',
    phases TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS daily_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    phase_index INTEGER DEFAULT 0,
    task_date DATE,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(1024),
    duration VARCHAR(50),
    resources TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_daily_tasks_user_status ON daily_tasks(user_id, status);

CREATE TABLE IF NOT EXISTS agent_runs (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT CHECK(status IN ('pending','running','success','failed','cancelled')) DEFAULT 'pending',
    input_hash VARCHAR(64) NOT NULL,
    input_data TEXT NOT NULL,
    output_data TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    duration_ms INTEGER,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_user ON agent_runs(agent_id, user_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);

-- Seed data: test user (password = "password123", bcrypt hash)
INSERT OR IGNORE INTO users (username, email, password_hash) VALUES
('testuser', 'test@example.com', '$2b$12$LJ3m4ys3uz0Gv0gMOsYmNe8JI8k/.dRgRv0cOx5vGJy0fkKzJKHpy');

-- Seed data: sample jobs (use import_data.py for full 5000-job dataset)
INSERT OR IGNORE INTO jobs (job_title, company, industry, city, salary_range, job_description, requirements, company_scale, publish_date) VALUES
('Python后端开发工程师', '字节跳动', '互联网', '北京', '25k-50k', '负责后端服务的设计与开发，构建高可用、高并发的分布式系统。', '熟悉Python、Django/FastAPI、MySQL、Redis、分布式系统。3年以上后端开发经验。', '10000人以上', DATE('now')),
('前端开发工程师', '阿里巴巴', '互联网', '杭州', '20k-45k', '负责Web前端开发，与设计师和后端紧密协作，实现优秀的用户体验。', '熟悉Vue.js/React、TypeScript、CSS3、前端工程化。', '10000人以上', DATE('now')),
('数据分析师', '腾讯', '互联网', '深圳', '18k-35k', '负责数据收集、清洗、分析与可视化，为业务决策提供数据支持。', '熟悉Python/SQL、统计分析、机器学习基础、数据可视化工具。', '10000人以上', DATE('now')),
('产品经理', '美团', '互联网', '上海', '22k-40k', '负责产品规划、需求分析与项目管理，推动产品从概念到上线。', '熟悉产品设计方法论、数据分析、项目管理、优秀的沟通能力。', '10000人以上', DATE('now'));

-- Seed data: promotion paths
INSERT OR IGNORE INTO promotion_transition (job_id, current_role, next_role, required_skills, years_exp, transition_type) VALUES
(1, '初级Python开发', '中级Python开发', '["Python","Django","MySQL","Redis"]', 2, 'promotion'),
(1, '中级Python开发', '高级Python开发', '["系统设计","分布式","Docker","微服务"]', 3, 'promotion'),
(2, '初级前端开发', '中级前端开发', '["Vue.js","React","TypeScript","Webpack"]', 2, 'promotion'),
(2, '中级前端开发', '高级前端开发', '["架构设计","性能优化","工程化","Node.js"]', 3, 'promotion'),
(3, '初级数据分析师', '高级数据分析师', '["Python","机器学习","SQL","数据可视化"]', 3, 'promotion'),
(4, '产品助理', '产品经理', '["需求分析","竞品分析","原型设计","项目管理"]', 2, 'promotion');
