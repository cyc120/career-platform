<template>
  <div class="home">
    <div>
    <!-- 1. 顶部区域 -->
    <header class="home-header">
      <div class="header-content">
        <h1 class="main-title">
          {{ typedText }}<span class="cursor">|</span>
        </h1>
        
        <!-- 搜索框 -->
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="输入一个目标职业（如：UI设计师），查看我的匹配度与晋升路径"
            size="large"
            clearable
            @keydown.enter="handleSearch"
            class="search-input"
          />
            
          <el-button 
            type="primary" 
            size="large"
            @click="handleSearch"
            class="search-btn"
          >
            <el-icon><Search /></el-icon>
            搜索
          </el-button>         
         </div>

        <!-- 热门搜索提示 -->
        <div class="hot-search">
          <span class="label">热门搜索：</span>
          <el-tag
            v-for="tag in hotSearchTags"
            :key="tag"
            size="small"
            class="search-tag"
            @click="searchByTag(tag)"
          >
            {{ tag }}
          </el-tag>
        </div>
      </div>
    </header>

    <!-- 2. 核心三列布局 -->
    <main class="home-main">
      <!-- 左列：职业分类卡片 -->
      <section class="left-panel category-panel">
        <el-card class="panel-card">
          <template #header>
            <div class="card-header">
              <el-icon><Grid /></el-icon>
              <span>岗位动态监测哨</span>
            </div>
          </template>
<div class="category-list-container"> <div class="scrolling-wrapper">
    <div class="scroll-content" v-for="n in 2" :key="n">
      <div
        v-for="category in categories"
        :key="category.id + '-' + n"
        :class="['category-item', { active: currentCategory === category.id }]"
        @click="selectCategory(category.id)"
      >
        <el-popover
          placement="right"
          :width="280"
          trigger="hover"
          popper-class="ai-monitor-popover"
          :show-after="100"
        >
          <template #reference>
            <div class="category-item-inner">
              <el-icon class="category-icon">
                <component :is="category.icon" />
              </el-icon>
              <span class="category-name">{{ category.name }}</span>
              <el-tag v-if="category.tag" size="small" effect="plain" class="category-tag">
                {{ category.tag }}
              </el-tag>
              <el-icon class="category-arrow"><ArrowRight /></el-icon>
            </div>
          </template>

          <div class="popover-ai-content">
            <div class="pop-header">
              <el-icon class="ai-pulse"><MagicStick /></el-icon>
              <span>职能助手 · 入职预测</span>
            </div>

            <div class="prediction-main">
              <div class="predict-item">
                <div class="predict-label-row">
                  <span class="label">入职胜率预测</span>
                  <span class="value success-text">{{ calculateWinRate(category) }}%</span>
                </div>
                <el-progress 
                  :percentage="calculateWinRate(category)" 
                  :stroke-width="8" 
                  :show-text="false"
                  color="#67c23a" 
                />
                <p class="base-info">基于你的竞争力评分: <strong>{{ competitivenessScore }}</strong></p>
              </div>

              <div class="salary-forecast-card">
                <div class="forecast-item">
                  <span class="f-label">预估谈薪溢价</span>
                  <span class="f-value">+{{ calculateSalaryPremium(category) }}%</span>
                </div>
                <div class="scarcity-info">
                  <span class="s-label">核心稀缺度：</span>
                  <el-tag size="mini" type="warning" effect="dark">
                    {{ category.insight.scarcity || '高需求' }}
                  </el-tag>
                </div>
              </div>
            </div>

            <el-divider border-style="dashed" style="margin: 12px 0" />

            <div class="mentor-suggestion">
              <span class="suggestion-label">🤖 Agent 策略决策：</span>
              <p class="suggestion-text">
                {{ generateAgentDecision(category) }}
              </p>
            </div>
          </div>
        </el-popover>
      </div>
    </div>
  </div>
</div>
        </el-card>
      </section>

      <!-- 中列：双功能入口卡片 -->
      <section class="middle-panel">
        <!-- 卡片 A：探索岗位 -->
        <div class="feature-card explore-card" @click="goToJobs">
          <div class="card-bg" style="background-image: url('https://placehold.co/600x300/667eea/ffffff?text=Explore+Jobs');"></div>
          <div class="card-overlay"></div>
          <div class="card-content">
            <h2 class="card-title">分析职位画像</h2>
            <p class="card-desc">海量职位，智能匹配</p>
            <el-button type="primary" size="large" class="card-btn">
              <el-icon><Search /></el-icon>
              立即探索
            </el-button>
          </div>
        </div>

        <!-- 卡片 B：开始测评 -->
        <div class="feature-card assessment-card" @click="goToProfile">
          <div class="card-bg" style="background-image: url('https://placehold.co/600x300/764ba2/ffffff?text=Assessment');"></div>
          <div class="card-overlay"></div>
          <div class="card-content">
            <h2 class="card-title">诊断职业竞争力</h2>
            <p class="card-desc">职能助手评估，精准定位</p>
            <el-button type="success" size="large" class="card-btn">
              <el-icon><Document /></el-icon>
              立即测评
            </el-button>
          </div>
        </div>
      </section>

      <!-- 右列：个人画像面板 -->
      <section class="right-panel">
        <el-card class="panel-card roadmap-focus-card" @mouseenter="stopAutoPlay" @mouseleave="startAutoPlay">
          <!-- 顶部状态栏 -->
          <div class="rp-status-bar">
            <div class="pulse-dot"></div>
            <span>职能助手 · 职场导航</span>
          </div>

          <!-- 加载态 -->
          <div v-if="profileLoading" class="rp-loading">
            <el-skeleton :rows="5" animated />
          </div>

          <!-- 空态：未填写个人信息 -->
          <div v-else-if="!hasProfile" class="rp-empty">
            <div class="rp-empty-illustration">
              <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="60" cy="60" r="56" fill="#f0f5ff" stroke="#d6e4ff" stroke-width="2" stroke-dasharray="6 4"/>
                <path d="M60 30c-8 0-14 6-14 14s6 14 14 14 14-6 14-14-6-14-14-14z" fill="#bfcfff"/>
                <path d="M38 78c0-12 10-22 22-22s22 10 22 22" stroke="#97aaff" stroke-width="3" stroke-linecap="round" fill="none"/>
                <circle cx="88" cy="36" r="6" fill="#ffd6d6"/>
                <path d="M85 36h6M88 33v6" stroke="#ff9999" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="rp-empty-title">暂无个人画像</div>
            <div class="rp-empty-desc">前往个人中心填写简历信息，<br/>职能助手将为你生成职场画像与每日任务</div>
            <el-button type="primary" round class="rp-empty-btn" @click="router.push('/profile/info')">
              <el-icon><User /></el-icon> 前往个人中心
            </el-button>
          </div>

          <!-- 有数据：个人信息 + 每日任务 -->
          <div v-else class="rp-content">
            <!-- 第一页：画像概览 + 每日任务 -->
            <div :class="['rp-page rp-page-front', { 'is-back': !isFrontPage }]">
              <!-- 用户头像行 + 综合评分 -->
              <div class="rp-user-row">
                <el-avatar :size="36" :src="auth.user?.avatar || ''" />
                <div class="rp-user-info">
                  <div class="rp-user-name">
                    {{ auth.user?.name || auth.user?.username || '用户' }}
                    <el-tag size="small" type="success" effect="plain">就绪</el-tag>
                  </div>
                  <div class="rp-user-sub">{{ auth.user?.university || auth.user?.school || '' }} {{ auth.user?.major ? '· ' + auth.user.major : '' }}</div>
                </div>
                <div class="rp-score-badge">
                  <div class="rp-score-num">{{ overallScore }}</div>
                  <div class="rp-score-label">综合评定</div>
                </div>
              </div>

              <!-- 七维度网格 -->
              <div class="rp-radar-grid">
                <div v-for="(dim, idx) in RADAR_DIMS" :key="dim" class="rp-radar-cell">
                  <span class="rp-radar-val" :class="{ active: currentRadarData[idx] > 0 }">{{ currentRadarData[idx] || 0 }}</span>
                  <span class="rp-radar-name">{{ dim }}</span>
                </div>
              </div>

              <!-- 每日任务 -->
              <div class="rp-tasks">
                <div class="rp-tasks-header">
                  <el-icon><Calendar /></el-icon>
                  <span>每日待办</span>
                  <el-tag size="small" type="info" effect="plain" class="rp-tasks-tag">Agent 推荐</el-tag>
                </div>
                <div v-if="tasksLoading" class="rp-tasks-loading">
                  <div v-for="i in 3" :key="i" class="rp-task-skeleton">
                    <div class="skel-check"></div>
                    <div class="skel-line" :style="{ width: [85, 65, 75][i - 1] + '%' }"></div>
                  </div>
                </div>
                <div v-else class="rp-tasks-list">
                  <div v-for="task in dailyTasks" :key="task.id" class="rp-task-item">
                    <el-checkbox v-model="task.completed" />
                    <span :class="['rp-task-text', { done: task.completed }]">{{ task.text }}</span>
                  </div>
                  <div v-if="dailyTasks.length === 0" class="rp-tasks-empty">暂无待办任务</div>
                </div>
              </div>
            </div>

            <!-- 第二页：能力缺口 + Agent 建议 -->
            <div :class="['rp-page rp-page-back', { 'is-front': !isFrontPage }]">
              <div class="rp-gap-title">能力差距分析</div>
              <div class="rp-gap-list">
                <div v-for="gap in skillGaps" :key="gap.name" class="rp-gap-item">
                  <div class="rp-gap-head">
                    <span class="rp-gap-name">{{ gap.name }}</span>
                    <span :class="['rp-gap-tag', gap.level]">{{ gap.status }}</span>
                  </div>
                  <el-progress :percentage="gap.percent" :stroke-width="5" :show-text="false" :color="gap.color" />
                </div>
                <div v-if="skillGaps.length === 0" class="rp-tasks-empty">暂无缺口数据</div>
              </div>

              <div class="rp-advice">
                <div class="rp-advice-header">
                  <el-icon class="rp-advice-icon"><MagicStick /></el-icon>
                  <span>Agent 建议</span>
                </div>
                <p class="rp-advice-text">{{ shortAgentAdvice }}</p>
              </div>
            </div>
          </div>

          <!-- 底部入口 -->
          <el-button type="primary" class="rp-bottom-btn" round @click="$router.push('/growth-tracking')">
            查看完整全周期规划 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </el-card>
      </section>
    </main>

    <!-- 3. 底部区域：热门岗位推荐 -->
<section class="hot-jobs-section">
  
<div class="data-particle-field" ref="particleContainer">
  <canvas ref="bgCanvas" class="bg-canvas"></canvas>
  
  <svg class="connection-lines" id="connection-lines">
    <defs>
      <linearGradient id="line-gradient">
        <stop offset="0%" stop-color="#409EFF" />
        <stop offset="100%" stop-color="#b18aff" />
      </linearGradient>
    </defs>
    <circle class="orbit-ring" cx="50%" cy="50%" fill="none" r="240" stroke="rgba(177, 138, 255, 0.15)" stroke-dasharray="8 8" stroke-width="1"></circle>
    <circle class="orbit-ring" cx="50%" cy="50%" fill="none" r="150" stroke="rgba(0, 219, 230, 0.1)" stroke-width="2"></circle>
    <g ref="dynamicLines"></g>
  </svg>

  <div class="center-text-block center-node" ref="centerNode">
    <div class="small-title">AURORA ENGINE 2.0</div>
    <div class="big-data">基于 <span class="highlight">10,000+</span> 岗位数据</div>
    <div class="ai-analysis">深度网络分析</div>
  </div>

  <div class="post-sphere data-node sphere-1" :ref="setNodeRef"><span class="label">前端开发</span></div>
  <div class="post-sphere data-node sphere-2" :ref="setNodeRef"><span class="label">产品经理</span></div>
  <div class="post-sphere data-node sphere-3" :ref="setNodeRef"><span class="label">AI 算法</span></div>
  <div class="post-sphere data-node sphere-4" :ref="setNodeRef"><span class="label">网络安全</span></div>
  <div class="post-sphere data-node sphere-5" :ref="setNodeRef"><span class="label">后端开发</span></div>
  <div class="post-sphere data-node sphere-6" :ref="setNodeRef"><span class="label">数据分析</span></div>
  <div class="post-sphere data-node sphere-7" :ref="setNodeRef"><span class="label">UI/UX</span></div>
  <div class="post-sphere data-node sphere-8" :ref="setNodeRef"><span class="label">运维 SRE</span></div>
  <div class="post-sphere data-node sphere-10" :ref="setNodeRef"><span class="label">全栈开发</span></div>
  <div class="post-sphere data-node sphere-11" :ref="setNodeRef"><span class="label">移动端</span></div>
  <div class="post-sphere data-node sphere-12" :ref="setNodeRef"><span class="label">云计算</span></div>
  <div class="post-sphere data-node sphere-13" :ref="setNodeRef"><span class="label">架构师</span></div>
  <div class="post-sphere data-node sphere-14" :ref="setNodeRef"><span class="label">交互设计</span></div>
  <div class="post-sphere data-node sphere-15" :ref="setNodeRef"><span class="label">游戏开发</span></div>
  <div class="post-sphere data-node sphere-16" :ref="setNodeRef"><span class="label">物联网 IOT</span></div>
</div>


<div class="jobs-list-container">
  <div class="section-header">
    <h2 class="section-title">🔥 高匹配度岗位推荐</h2>
  </div>

  <div class="infinite-scroll-wrapper">
    
    <div class="scroll-row row-left">
      <div class="scroll-track">
        <div class="scroll-group">
          <JobCard
            v-for="job in hotJobs"
            :key="'r1-' + job.id"
            :job="formatJobData(job)"
          />
        </div>
        <div class="scroll-group" aria-hidden="true">
          <JobCard
            v-for="job in hotJobs"
            :key="'r1-copy-' + job.id"
            :job="formatJobData(job)"
          />
        </div>
      </div>
    </div>

    <div class="scroll-row row-right">
      <div class="scroll-track">
        <div class="scroll-group">
          <JobCard
            v-for="job in [...hotJobs].reverse()"
            :key="'r2-' + job.id"
            :job="formatJobData(job)"
          />
        </div>
        <div class="scroll-group" aria-hidden="true">
          <JobCard
            v-for="job in [...hotJobs].reverse()"
            :key="'r2-copy-' + job.id"
            :job="formatJobData(job)"
          />
        </div>
      </div>
    </div>

  </div>
</div>

</section>

    <!-- 底部信息 -->
    <footer class="home-footer">
      <p>© 2026 职途无限 - 职能助手</p>
      <p class="footer-links">
        <el-link type="info">公司简介</el-link>
        <span class="divider">|</span>
        <el-link type="info">联系方式</el-link>
        <span class="divider">|</span>
        <el-link type="info">隐私政策</el-link>
        <span class="divider">|</span>
        <el-link type="info">服务条款</el-link>
      </p>
    </footer>
    </div>

    <!-- 悬浮球：提醒完善个人信息 -->
    <div v-if="!isProfileCompleted" class="floating-profile-ball" @click="router.push('/profile')">
      <button class="ball-close" @click.stop="dismissGuide">&times;</button>
      <div class="ball-icon">
        <el-icon :size="24"><UserFilled /></el-icon>
      </div>
      <span class="ball-text">完善信息</span>
      <span class="ball-badge">!</span>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search,
  User,
  Lock,
  Document,
  Grid,
  ArrowRight,
  ChatDotRound,
  ChatLineRound,
  Service
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { jobsApi } from '@/api/jobs'
import { resumeApi } from '@/api/resume'
import { learningPlanApi } from '@/api/learningPlan'
import { currentRadarData } from '@/views/Profile/profileState'
import { useAuthStore } from '@/stores/auth'
import JobCard from '@/components/JobCard.vue'
import gsap from 'gsap'
import { UserFilled } from '@element-plus/icons-vue'

const auth = useAuthStore()
const hotJobs = ref([])

const RADAR_DIMS = ['专业技能', '创新能力', '学习能力', '实习能力', '抗压能力', '沟通能力', '证书']
const RADAR_WEIGHTS = [0.18, 0.15, 0.18, 0.16, 0.10, 0.10, 0.13]

const overallScore = computed(() => {
  const radar = currentRadarData.value
  if (!radar || !radar.some(v => v > 0)) return 0
  let totalScore = 0, totalWeight = 0
  radar.forEach((score, i) => {
    if (score > 0) {
      totalScore += score * RADAR_WEIGHTS[i]
      totalWeight += RADAR_WEIGHTS[i]
    }
  })
  return totalWeight > 0 ? Math.round(totalScore / totalWeight) : 0
})

const loadHotJobs = async () => {
  try {
    const { data } = await jobsApi.list({ page_size: 10 })
    hotJobs.value = (data.jobs || []).map((item) => ({
      id: item.id,
      jobTitle: item.job_title || item.title,
      companyName: item.company_name || item.company,
      location: item.city || '--',
      matchRate: item.match_rate || 85,
      salary: item.salary_range || item.salary || '面议',
      tags: item.industry ? item.industry.split(',').slice(0, 3) : [],
      raw: { industry: item.industry || '' },
    }))
  } catch {
    // keep empty
  }
}

const userData = computed(() => auth.user || { name: 'user', skills: userDataFallback.skills })

const userDataFallback = {
  name: 'user',
  skills: {
    certificate: 70, digital: 75, teamwork: 80, learning: 90,
    professional: 85, internship: 65, communication: 80, pressure: 75, innovation: 85,
  },
}

const isProfileCompleted = ref(!!sessionStorage.getItem('is_profile_completed'))
const hasProfile = ref(false)
const profileLoading = ref(true)

const checkProfileStatus = async () => {
  try {
    // 1. 当前会话已填写（SPA 内 radar 数据非零）
    const hasRadar = currentRadarData.value && currentRadarData.value.some(v => v > 0)
    if (hasRadar) {
      hasProfile.value = true
      isProfileCompleted.value = true
      sessionStorage.setItem('is_profile_completed', 'true')
      return
    }
    // 2. 从个人中心保存后跳转过来（一次性标记，读后即删）
    if (sessionStorage.getItem('profile_saved') === 'true') {
      sessionStorage.removeItem('profile_saved')
      hasProfile.value = true
      isProfileCompleted.value = true
      sessionStorage.setItem('is_profile_completed', 'true')
      return
    }
    // 3. 未填写 → 显示空态
    hasProfile.value = false
  } catch {
    hasProfile.value = false
  } finally {
    profileLoading.value = false
  }
}

const dismissGuide = () => {
  isProfileCompleted.value = true
  sessionStorage.setItem('is_profile_completed', 'true')
}
// 计算胜率：个人分 / 岗位要求分 (假设 category 里有要求分)
const calculateWinRate = (category) => {
  const baseRate = 70; // 基础分
  const scoreDiff = (competitivenessScore.value - 700) / 10; 
  return Math.min(98, Math.max(40, Math.floor(baseRate + scoreDiff)));
};

// 计算溢价：基于稀缺度
const calculateSalaryPremium = (category) => {
  // 模拟：后端/AI 岗位溢价高，UI 岗位溢价平稳
  return category.name.includes('AI') || category.name.includes('后端') ? 25 : 12;
};

// 动态生成建议
const generateAgentDecision = (category) => {
  const winRate = calculateWinRate(category);
  if (winRate > 80) return "当前岗位与你画像高度契合，建议立即更新简历并投递。";
  return "检测到核心技能缺口，建议优先完成右侧‘技能诊断’中的学习任务后再试。";
};

const currentPage = ref(1)
const pageDirection = ref('slide-left')
let autoPlayTimer = null

const skillCompleteness = ref(0)
const competitivenessScore = ref(0)
const dailyTasks = ref([])
const skillGaps = ref([])
const shortAgentAdvice = ref('正在获取 Agent 建议...')
const tasksLoading = ref(true)

// 从 resume_analyzer + learning_plan + dailyTasks 获取数据
const fetchDashboardData = async () => {
  try {
    const [resumeRes, planRes, tasksRes] = await Promise.all([
      resumeApi.analyze({}),
      learningPlanApi.generate({ plan_type: '长期' }),
      learningPlanApi.dailyTasks({ phase_index: 0 }),
    ])
    // 竞争力评分 & 技能完整度
    const rData = resumeRes.data
    if (rData.competitiveness) {
      const score = rData.competitiveness.score || rData.competitiveness
      competitivenessScore.value = typeof score === 'number' && score <= 1
        ? Math.round(score * 100)
        : Math.round(score)
    }
    if (rData.completeness_flags) {
      const flags = rData.completeness_flags
      const total = Object.keys(flags).length || 7
      const filled = Object.values(flags).filter(Boolean).length
      skillCompleteness.value = Math.round((filled / total) * 100)
    }
    // 能力缺口
    if (rData.skill_analysis) {
      const s = rData.skill_analysis
      const gaps = []
      Object.entries(s).forEach(([key, val]) => {
        const score = typeof val === 'number' ? val : 75
        if (score < 80) {
          gaps.push({
            name: key,
            status: score < 50 ? '缺失' : score < 70 ? '尚浅' : '待加强',
            level: score < 50 ? 'danger' : score < 70 ? 'warning' : 'info',
            percent: score,
            color: score < 50 ? '#f56c6c' : score < 70 ? '#e6a23c' : '#409eff',
          })
        }
      })
      if (gaps.length > 0) skillGaps.value = gaps.slice(0, 4)
    }

    // Agent 建议
    const pData = planRes.data
    if (pData.learning_plan?.agent_advice) {
      shortAgentAdvice.value = pData.learning_plan.agent_advice
    } else if (pData.learning_plan?.summary) {
      shortAgentAdvice.value = pData.learning_plan.summary
    }

    // 每日待办（与 GrowthTracker 同源：learningPlanApi.dailyTasks）
    const tData = tasksRes.data
    if (tData.daily_tasks && tData.daily_tasks.length > 0) {
      dailyTasks.value = tData.daily_tasks.slice(0, 6).map((t, i) => ({
        id: t.id || i + 1,
        text: t.content || t.title || t.task || `任务 ${i + 1}`,
        completed: false,
      }))
    }
  } catch {
    // 静默降级，使用默认值
  } finally {
    tasksLoading.value = false
  }
}

// 🌟 新增：层级切换逻辑
const isFrontPage = ref(true)
let stackTimer = null

const startAutoPlay = () => {
  if (stackTimer) clearInterval(stackTimer)
  stackTimer = setInterval(() => {
    isFrontPage.value = !isFrontPage.value
  }, 5000) // 每 5 秒切换一次前后位置
}

const stopAutoPlay = () => {
  if (stackTimer) clearInterval(stackTimer)
}

onMounted(() => {
  startAutoPlay()
})

onUnmounted(() => {
  stopAutoPlay()
})



const particleContainer = ref(null)
const bgCanvas = ref(null)
const centerNode = ref(null)
const dynamicLines = ref(null)
const dataNodes = ref([])

const setNodeRef = (el) => {
  if (el && !dataNodes.value.includes(el)) {
    dataNodes.value.push(el)
  }
}

let animationFrameId;
let canvasCtx;
let particles = [];
let mouse = { x: -1000, y: -1000 }; // 初始隐藏鼠标

// 1. 初始化 Canvas 粒子
const initCanvas = () => {
  if (!bgCanvas.value || !particleContainer.value) return;
  const rect = particleContainer.value.getBoundingClientRect();
  bgCanvas.value.width = rect.width;
  bgCanvas.value.height = rect.height;
  canvasCtx = bgCanvas.value.getContext('2d');
  
  particles = [];
  for (let i = 0; i < 500; i++) {
    particles.push({
      x: Math.random() * rect.width,
      y: Math.random() * rect.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 2 + 1,
      color: Math.random() > 0.5 ? 'rgba(64, 158, 255, 0.3)' : 'rgba(177, 138, 255, 0.3)'
    });
  }
}

// 2. 主渲染循环 (Canvas 粒子 + SVG 连线)
const renderLoop = () => {
  if (!canvasCtx || !bgCanvas.value || !particleContainer.value) return;
  const rect = particleContainer.value.getBoundingClientRect();
  
  // 清空画布
  canvasCtx.clearRect(0, 0, rect.width, rect.height);

  // 渲染粒子
  particles.forEach(p => {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0 || p.x > rect.width) p.vx *= -1;
    if (p.y < 0 || p.y > rect.height) p.vy *= -1;

    // 🌟 鼠标排斥效果 (Stitch 特效)
    let dx = mouse.x - p.x;
    let dy = mouse.y - p.y;
    let dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < 150) {
      p.x -= dx * 0.01;
      p.y -= dy * 0.01;
    }

    canvasCtx.fillStyle = p.color;
    canvasCtx.beginPath();
    canvasCtx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    canvasCtx.fill();
  });

  // 🌟 实时更新 SVG 动态连线 (从中心到每个球)
  if (centerNode.value && dynamicLines.value && dataNodes.value.length > 0) {
    const cRect = centerNode.value.getBoundingClientRect();
    const cx = cRect.left + cRect.width / 2 - rect.left;
    const cy = cRect.top + cRect.height / 2 - rect.top;

    // 获取之前生成的 path，如果没有则创建
    let paths = dynamicLines.value.querySelectorAll('path');
    if (paths.length === 0) {
      dataNodes.value.forEach(() => {
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("stroke", "url(#line-gradient)");
        path.setAttribute("fill", "none");
        path.setAttribute("stroke-width", "1.5");
        path.setAttribute("opacity", "0.25");
        path.setAttribute("stroke-dasharray", "5, 5");
        dynamicLines.value.appendChild(path);
      });
      paths = dynamicLines.value.querySelectorAll('path');
    }

    dataNodes.value.forEach((node, i) => {
      const nRect = node.getBoundingClientRect();
      const nx = nRect.left + nRect.width / 2 - rect.left;
      const ny = nRect.top + nRect.height / 2 - rect.top;
      // 绘制贝塞尔曲线增加科技感
      paths[i].setAttribute("d", `M ${cx} ${cy} Q ${cx} ${ny} ${nx} ${ny}`);
    });
  }

  animationFrameId = requestAnimationFrame(renderLoop);
}

// 3. 鼠标交互事件
const handleMouseMove = (e) => {
  if (!particleContainer.value) return;
  const rect = particleContainer.value.getBoundingClientRect();
  mouse.x = e.clientX - rect.left;
  mouse.y = e.clientY - rect.top;

  // 🌟 磁性吸引效果 (GSAP)
  dataNodes.value.forEach(node => {
    const nRect = node.getBoundingClientRect();
    const centerX = nRect.left + nRect.width / 2;
    const centerY = nRect.top + nRect.height / 2;
    const dx = e.clientX - centerX;
    const dy = e.clientY - centerY;
    const distance = Math.sqrt(dx*dx + dy*dy);

    if (distance < 200) {
      gsap.to(node, { 
        x: dx / 8, y: dy / 8, duration: 0.6, ease: 'power2.out', overwrite: 'auto'
      });
    } else {
      // 恢复原状
      gsap.to(node, { x: 0, y: 0, duration: 0.8, ease: 'elastic.out(1, 0.5)' });
    }
  });
}

// 4. GSAP 随机悬浮动画
const startGsapFloating = () => {
  dataNodes.value.forEach(node => {
    gsap.to(node, {
      y: `+=${(Math.random() - 0.5) * 30}`,
      x: `+=${(Math.random() - 0.5) * 20}`,
      duration: 3 + Math.random() * 2,
      ease: "sine.inOut",
      repeat: -1,
      yoyo: true
    });
  });
}

// ==========================================
// 🌟 升级版：个性化爆炸放射动画
// ==========================================
const runExplosionAnimation = () => {
  const tl = gsap.timeline();

  // 1. 中心文字块先显现 (稍微带一点点放大效果)
  if (centerNode.value) {
    tl.from(centerNode.value, {
      scale: 0.5,         // 从 0.5 倍大小开始
      opacity: 0,         // 从透明开始
      duration: 1.2,        // 持续 1.2 秒
      ease: "power4.out" // 带有弹性的出场缓动
    });
  }

  // 2. 🌟 核心：所有岗位球个性化、不同速放射
  if (dataNodes.value.length > 0) {
    // 技巧：我们遍历每个节点，为它们创建单独的 GSAP 动画
    dataNodes.value.forEach((node, index) => {
      
      // 🌟 生成随机参数，确保每个球都是独一无二的
      // 1. 速度随机：放射持续时间在 1.2秒 到 2.2秒 之间
      const randomDuration = 1.2 + Math.random() * 1.0;
      // 2. 延迟随机：每个球都在文字显现后 0 到 0.6秒 之间随机放射
      const randomDelay = Math.random() * 0.6;
      // 3. 缓动随机：大部分先快后慢，小部分稍微带一点弹性
      const randomEase = Math.random() > 0.8 ? "back.out(1.5)" : "power4.out";
      // 4. 景深随机：从不同的深远度发散出来
      const randomDepth = -300 - Math.random() * 300; 

      gsap.from(node, {
        // 初始状态：全部压制到容器中心
        x: 0, 
        y: 0, 
        z: randomDepth,    // 🌟 关键：景深随机

        opacity: 0,         // 从透明开始
        scale: 0,           // 从 0 大小开始
        
        // 应用随机生成的参数
        duration: randomDuration, // 🌟 关键：速度随机
        delay: 0.2 + randomDelay,   // 🌟 关键：启动时差随机
        ease: randomEase,         // 🌟 关键：缓动随机

        // 在最后一个球（随机到的最慢的球）完成时，交棒给漂浮动画
        // 技巧：这里使用一个标志位，只让最后一个动画触发回调
        onComplete: () => {
          if (index === dataNodes.value.length - 1) {
            // 确保漂浮动画在放射完成后才开始
            startGsapFloating(); 
          }
        }
      });
    });
  }
};

// ==========================================
// 生命周期管理
// ==========================================
onMounted(() => {
  startTyping();
  window.addEventListener('resize', handleResize);
  
  // 启动 Stitch 特效
  nextTick(() => {
    initCanvas();
    renderLoop();
    startGsapFloating();
    window.addEventListener('mousemove', handleMouseMove);

    const observerOptions = {
      root: null, // 默认使用浏览器视口
      threshold: 0.3 // 当 30% 的区域进入视口时触发
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        // 如果区域进入视口 且 动画尚未执行过
        if (entry.isIntersecting) {
          runExplosionAnimation(); // 执行放射动画
          observer.unobserve(entry.target); // 动画只跑一次，触发后停止观察
        }
      });
    }, observerOptions);

    if (particleContainer.value) {
      observer.observe(particleContainer.value);
    }
  });
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  window.removeEventListener('mousemove', handleMouseMove);
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
})

const router = useRouter()


const fullText = "职途虽远，智能无界；跨越方寸，预见无限"
const typedText = ref("")
const typingSpeed = 150 // 每个字的打字速度（毫秒）

// 修改你的 startTyping 函数
let typingTimer = null; // 在函数外部定义变量

const startTyping = () => {
  // 🌟 新增：如果已经在打字了，先停止之前的，防止重复
  if (typingTimer) clearInterval(typingTimer);
  typedText.value = ''; 
  
  let i = 0;
  typingTimer = setInterval(() => {
    typedText.value += fullText[i];
    i++;
    if (i >= fullText.length) {
      clearInterval(typingTimer);
      typingTimer = null;
    }
  }, 100);
};



// 搜索相关
const searchKeyword = ref('')
const hotSearchTags = ref(['Java 工程师', '前端开发', '算法专家', '产品经理', '数据分析师', 'AI 工程师'])

// 职业分类
const categories = ref([
  { name: '前端开发 · 交互重构', icon: 'Monitor', tag: '职能增益', insight: { forecast: '18个月', deviation: '85%', decision: '建议强化 WebAssembly 实战，补齐高性能渲染画像。' } },
  { name: '后端开发 · 架构设计', icon: 'Cpu', tag: '高需求', insight: { forecast: '36个月', deviation: '92%', decision: '画像匹配度高，建议关注分布式一致性协议的深度原理。' } },
  { name: 'AI 算法 · 模型演进', icon: 'MagicStick', tag: '快迭代', insight: { forecast: '6个月', deviation: '70%', decision: '技术更迭极快，建议从模型调用转向垂直领域微调。' } },
  { name: '产品经理 · 数字转型', icon: 'User', tag: '跨界型', insight: { forecast: '24个月', deviation: '78%', decision: '缺乏数据驱动决策背书，建议关联个人中心的能力证明。' } },
  { name: '网络安全 · 攻防演练', icon: 'Lock', tag: '高门槛', insight: { forecast: '30个月', deviation: '65%', decision: 'AI 自动化攻击加剧，需提升零信任架构的规划能力。' } },
  { name: '数据分析 · 决策支持', icon: 'PieChart', tag: '核心岗', insight: { forecast: '22个月', deviation: '88%', decision: '建议掌握自动化报表工具，将精力转向业务价值挖掘。' } },
  { name: '移动开发 · 跨端框架', icon: 'Iphone', tag: '稳健型', insight: { forecast: '20个月', deviation: '80%', decision: '原生开发需求收缩，建议向 Flutter 或 HarmonyOS 演进。' } },
  { name: '运维开发 · SRE', icon: 'Setting', tag: '硬核岗', insight: { forecast: '28个月', deviation: '75%', decision: 'AIOps 普及中，建议学习如何利用大模型优化告警预测。' } },
  { name: 'UI/UX · 体验设计', icon: 'Brush', tag: '视觉系', insight: { forecast: '15个月', deviation: '82%', decision: '单纯绘图易被替代，需强化“交互逻辑与用户行为分析”。' } },
  { name: '测试开发 · 自动化', icon: 'CircleCheck', tag: '品质岗', insight: { forecast: '24个月', deviation: '90%', decision: '测试用例生成已 AI 化，建议向全链路压测与安全扫描转型。' } }
]);
const currentCategory = ref(1)

// 登录状态
const isLoggedIn = ref(false)
const loginLoading = ref(false)

// 登录表单
const loginForm = ref({
  username: '',
  password: ''
})

// 当前用户数据
const currentUser = ref({
  name: '',
  avatar: '',
  tags: ['#前端', '#高薪', '#远程', '#AI', '#创新', '#成长']
})

// 格式化岗位数据
const formatJobData = (job) => ({
  jobTitle: job.title || job.jobTitle,
  companyName: job.company || job.companyName,
  salary: job.salary || '面议',
  city: job.city || job.location,
  matchRate: job.matchRate || 0,
  tags: job.tags || []
})

// 搜索处理
const handleSearch = () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.info({
    message: '请输入搜索关键词',
    duration: 1500 // 设置为 1.5 秒 (1500ms)，你可以改成 1000, 800 等更短的时间
})
    return
  }
  router.push(`/jobs?keyword=${encodeURIComponent(searchKeyword.value)}`)
}

// 标签搜索
const searchByTag = (tag) => {
  searchKeyword.value = tag
  handleSearch()
}

// 选择分类
const selectCategory = (categoryId) => {
  currentCategory.value = categoryId
  const category = categories.value.find(c => c.id === categoryId)
  console.log('选择分类:', category?.name)
  // 预留跳转或筛选逻辑
  router.push(`/jobs?category=${categoryId}`)
}

// 处理登录
const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loginLoading.value = true

  // 模拟异步请求
  await new Promise(resolve => setTimeout(resolve, 1000))

  loginLoading.value = false
  isLoggedIn.value = true

  currentUser.value = {
    name: loginForm.value.username,
    avatar: `https://ui-avatars.com/api/?name=${loginForm.value.username}&background=667eea&color=fff`,
    tags: ['#前端', '#高薪', '#远程', '#AI', '#创新', '#成长']
  }

  ElMessage.success('登录成功')
}

// 处理退出
const handleLogout = () => {
  isLoggedIn.value = false
  loginForm.value = {
    username: '',
    password: ''
  }
  currentUser.value = {
    name: '',
    avatar: '',
    tags: []
  }
  ElMessage.success('已退出登录')
}

// 路由跳转
const goToJobs = () => router.push('/jobs')
const goToProfile = () => router.push('/profile/info')

// 生命周期
onMounted(() => {
  loadHotJobs()
  checkProfileStatus()
  fetchDashboardData()
  window.addEventListener('resize', handleResize)
})

onMounted(() => {
  // 打字机动画已在第一个 onMounted 中启动
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const handleResize = () => {
  // 响应式处理
}
</script>

<style scoped lang="scss">
.home {
  min-height: 100vh;
  background: #c4d1f617;
  
}

/* 找到 Home.vue 中的 .main-title 进行替换 */
.main-title {
  /* 🌟 大气点：巨大的字号配合极大的字间距 */
  font-size: 56px; 
  font-weight: 800;
  letter-spacing: 6px; /* 产生一种跨越感 */
  

  
  /* 选用更硬朗的字体 */
  font-family: "Inter", "PingFang SC", "Source Han Sans CN", "Microsoft YaHei", sans-serif;
  
  /* 增加一点文字阴影的深度感（非常淡） */
  text-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
  
  line-height: 1.3;
}

/* 悬浮球：提醒完善个人信息 */
.floating-profile-ball {
  position: fixed;
  bottom: 40px;
  right: 40px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px 14px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50px;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: ballPulse 2s ease-in-out infinite;

  &:hover {
    transform: translateY(-3px) scale(1.05);
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.5);
    animation: none;
  }

  .ball-close {
    position: absolute;
    top: -6px;
    right: -6px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.3);
    border: 2px solid #fff;
    color: #fff;
    font-size: 12px;
    line-height: 16px;
    text-align: center;
    cursor: pointer;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;

    &:hover {
      background: rgba(0, 0, 0, 0.5);
    }
  }

  .ball-icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .ball-text {
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .ball-badge {
    position: absolute;
    top: -4px;
    left: -4px;
    width: 20px;
    height: 20px;
    background: #ff4757;
    border-radius: 50%;
    font-size: 11px;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #fff;
    animation: badgeBounce 1.5s ease-in-out infinite;
  }
}

@keyframes ballPulse {
  0%, 100% { box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4); }
  50% { box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4), 0 0 0 8px rgba(102, 126, 234, 0.15); }
}

@keyframes badgeBounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

// ========== 1. 顶部区域 (修正了布局与层级) ==========
// ========== 1. 顶部区域 ==========
.home-header {
  background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #afcaf4, #b1efbf);
  background-size: 400% 400%;
  animation: gradientBG 8s ease infinite; 
  padding: 5px 40px 100px; 
  color: #ffffff;
  position: relative;
  overflow: hidden;

 &::before { 
    content: "";
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background-image: radial-gradient(circle at 20% 30%, rgba(64, 158, 255, 0.15) 0%, transparent 50%);
    pointer-events: none;
    z-index: 1;
  }

  // 2. 🔥 新增：底部融合渐变层
  &::after {
    content: "";
    position: absolute;
    left: 0;
    bottom: 0;
    width: 100%;
    height: 150px; // 渐变过渡的高度，可以根据视觉效果调整
    /* 这里的 #f4f7fe 是根据你 .home 的 background: #bfcdf62e 计算出的近似底色 */
    background: linear-gradient(to bottom, transparent, #f4f7fe); 
    z-index: 2;
    pointer-events: none;
  }

  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    position: relative;
    z-index: 3; // 确保文字内容在渐变层之上，不会变淡
  }

  .main-title {
    font-size: 52px;
    font-weight: 800;
    text-align: left;
    margin-bottom: 40px;
    min-height: 70px; 
    .cursor {
      margin-left: 8px;
      color: #409EFF;
      animation: blink 0.8s infinite;
    }
  }

  /* 🌟 搜索框样式块开始 */
/* ========================================================== */
/* 🔍 搜索组件深度美化：更精致、更协调、更有重点 */
/* ========================================================== */
.search-box {
  display: flex;
  align-items: stretch; /* 🌟 关键：确保按钮和输入框高度完美一致 */
  max-width: 1100px;      /* 🌟 稍微加宽，更显大气 */
  margin-bottom: 25px;
  position: relative;
  z-index: 10;

  /* -------------------------- */
  /* A. 左侧输入框：轻盈毛玻璃感 (虚) */
  /* -------------------------- */
  .search-input {
    flex: 1; /* 占满剩余空间 */

    :deep(.el-input__wrapper) {
      /* 1. 核心：轻量毛玻璃质感 (不破坏背景感) */
      background-color: rgba(255, 255, 255, 0.45) !important; 
      backdrop-filter: blur(12px); /* 🌟 核心：模糊后方背景 */
      
      /* 2. 圆角处理：左侧大圆角，右侧直角对接按钮 */
      border-radius: 24px 0 0 24px !important; 
      
      /* 3. 精致细节：极淡的描边与大阴影增加精致感 */
      border: 1px solid rgba(255, 255, 255, 0.4) !important;
      box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05) !important;
      padding-left: 18px;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

      /* 控制输入框高度 (🌟 如果你用大字号，建议也增高) */
      .el-input__inner {
        height: 56px; 
        font-size: 16px;
        color: #334455;
        font-weight: 500;
        
        /* 占位符文字调淡 */
        &::placeholder {
          color: rgba(51, 68, 85, 0.4);
        }
      }
    }

    /* 4. 聚焦时的发光交互：更通透 */
    :deep(.el-input__wrapper.is-focus) {
      background-color: rgba(255, 255, 255, 0.9) !important; /* 聚焦时变清晰 */
      box-shadow: 0 8px 32px rgba(64, 158, 255, 0.15) !important;
      border-color: rgba(64, 158, 255, 0.5) !important;
    }
  }

  /* -------------------------- */
  /* B. 右侧按钮：坚实渐变色 (实 - 全场焦点) */
  /* -------------------------- */
  .search-btn {
    /* 1. 修改圆角：左侧直角对接输入框，右侧保留大圆角 */
    border-radius: 0 24px 24px 0 !important; 
    
    /* 2. 核心修改：坚实、饱和的渐变色 (钉在界面上) */
    background: linear-gradient(135deg, #77b1f8 0%, #8c97f6 100%) !important;
    color: white !important; /* 🌟 保证文字必须是纯白 */
    
    /* 3. 尺寸与字号优化 */
    padding: 0 45px !important; /* 增加点击区域和视觉分量 */
    font-weight: 700;           /* 🎨 加粗标题 */
    font-size: 18px;            /* 🎨 调大字号 */
    letter-spacing: 1px;        /* 字间距增加精致感 */
    height: auto;               /* 跟随容器高度，确保无缝 */
    border: none !important;
    
    /* 4. 重点：亮蓝色立体投影 (增加点击欲) */
    box-shadow: 4px 6px 15px rgba(64, 158, 255, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    cursor: pointer;

    /* 调整图标大小 */
    .el-icon {
      font-size: 20px;
      margin-right: 6px;
      vertical-align: middle;
    }

    /* 5. 悬停时的灵动交互 */
    &:hover {
      filter: brightness(1.1); /* 稍微变亮 */
      transform: translateY(-1px); /* 🎨 轻微上浮，产生交互反馈 */
      box-shadow: 4px 8px 25px rgba(64, 158, 255, 0.4) !important;
    }
    
    /* 按下时的反馈 */
    &:active {
      transform: translateY(1px); /* 轻微按下 */
      filter: brightness(1);
    }
  }
}

  .hot-search {
    display: flex;
    align-items: center;
    gap: 12px;
    .label { font-size: 14px; opacity: 0.8; }
    .search-tag {
      background: rgba(255, 255, 255, 0.1);
      color: #fff;
      cursor: pointer;
    }
  }
} // 闭合 .home-header
// ========== 2. 核心三列布局 (修正层级遮挡) ==========
.home-main {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  align-items: stretch;     /* 🌟 确保所有网格项（左中右）高度拉伸一致 */
  gap: 24px;
  max-width: 1400px;
  margin: -60px auto 10px; 
  padding: 0 40px;
  position: relative;
  z-index: 10; 

  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
    margin-top: 20px;
  }
}

// ========== 3. 通用卡片与面板样式 ==========
.panel-card {
  height: 100%;             /* 🌟 关键：让卡片填满整个网格区域的高度 */
  display: flex;            /* 开启 flex 布局以便内部内容分布 */
  flex-direction: column;   
  
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: none;

  // ... 其他代码 ...
  
  // 如果你想让里面的分类列表均匀撑开，可以给列表加这个：
  .category-list {
    flex: 1;                /* 🌟 让列表占据剩余的所有垂直空间 */
    display: flex;
    flex-direction: column;
    justify-content: space-around; /* 或者 space-between，取决于你想要的间距感 */
  }
}

/* 左列：职业分类 */
/* 左列：职业分类美化 */
/* ========================================================== */
/* 🎨 职业分类 (左列) 美化：毛玻璃质感与灵动交互 */
/* ========================================================== */
.category-panel {
  /* 1. 卡片主体材质美化 */
  .panel-card {
    border-radius: 20px !important;
    /* 🌟 修改点：透明度从 0.6 改为 0.92，增加实体感 */
    background: rgba(255, 255, 255, 0.72) !important; 
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.8); /* 边框也稍微白一点 */
    /* 🌟 修改点：阴影稍微加深，让它“压”住背景 */
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08) !important;
    height: 570px; /* 这个高度约等于原本容器的高度 */
    overflow: hidden; /* 确保溢出的卡片不可见，动画才能生效 */
    
    

    &:hover {
      box-shadow: 0 16px 50px rgba(64, 158, 255, 0.08); /* 悬停时阴影变深 */
    }

    /* 卡片头部标题美化 */
    :deep(.el-card__header) {
      padding: 22px 25px 15px; /* 增加内边距呼吸空间 */
      border-bottom: 1px solid rgba(0, 0, 0, 0.05); /* 调淡下划线 */

      .card-header {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 18px;          /* 🎨 调大标题：从 16px 改为 18px */
        font-weight: 700;         /* 🎨 加粗标题 */
        color: #334455;           /* 深灰蓝，非纯黑 */

        /* 标题图标美化 */
        i {
          font-size: 20px;
          color: #409EFF;         /* 使用 Header 强调色 */
        }
      }
    }
  }

/* 找到 .category-list-container 并替换为以下内容 */
/* 1. 找到并替换这部分代码 */
.category-list-container {
  /* 必须锁定一个比内容小的固定高度，overflow:hidden 才会生效 */
  height: 440px !important; 
  flex: none !important;    
  position: relative;
  padding: 10px 0;
  
  /* 核心：彻底切断用户的滚动交互（滚轮、触摸、拖拽） */
  overflow: hidden !important; 
  touch-action: none !important;   /* 禁用移动端/触摸板手势 */
  user-select: none;               /* 防止选取文字导致的拉拽滚动 */

  /* 2. 视觉：全浏览器兼容隐藏滚动条 */
  -ms-overflow-style: none !important;  /* IE/Edge */
  scrollbar-width: none !important;     /* Firefox */
  
  &::-webkit-scrollbar {
    display: none !important;           /* Chrome/Safari/Opera */
    width: 0 !important;
    height: 0 !important;
  }
}

/* 3. 动画执行层 */
.scrolling-wrapper {
  display: flex;
  flex-direction: column;
  /* 30秒滚完一圈，你可以根据体感调快（如20s）或调慢（如40s） */
  animation: scrollVertical 20s linear infinite;
}

/* 4. 关键交互：悬停时暂停滚动，方便用户查看 Popover */
.category-list-container:hover .scrolling-wrapper {
  animation-play-state: paused;
}

/* 5. 编写无缝滚动动画 */
@keyframes scrollVertical {
  0% {
    transform: translateY(0);
  }
  100% {
    /* 因为我们在 HTML 中 v-for="n in 2" 渲染了两组相同的数据 */
    /* 所以位移到 -50% 的位置时，视觉上正好回到起点，实现无缝连接 */
    transform: translateY(-50%);
  }
}

  /* 2. 职业分类列表通用美化 */
  .category-list {
    display: flex;
    flex-direction: column;
    gap: 6px;                     /* 🎨 调小间距：更紧凑、更有秩序感 */
    padding: 10px 12px 20px;     /* 🎨 底部留呼吸空间 */
  }

  /* 3. 职业分类单项交互美化 */
  .category-item {
    display: flex;
    align-items: center;
    padding: 8px 20px;          /* 🎨 增加点击区域和侧边空间 */
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); /* 🎨 高级缓动：更有弹性 */
    border: 1px solid transparent; /* 预留边框空间 */
    position: relative;
    overflow: hidden;

    

    /* A. 默认图标颜色微调 */
    .category-icon { 
      font-size: 18px; 
      margin-right: 14px; 
      color: #90a4ae;              /* 🎨 默认态调淡图标：灰蓝色，减少干扰 */
      transition: all 0.3s ease;
    }
    .category-name { 
      flex: 1; 
      font-size: 15px; 
      font-weight: 500;            /* 中等粗细 */
      transition: all 0.3s ease;
    }
    .category-arrow { 
      font-size: 12px; 
      color: #c0c4cc; 
      opacity: 0.5;                /* 🎨 调淡箭头：静态下不明显 */
      transition: all 0.3s ease;
    }

    /* B. 悬停态 (Hover)：灵动反馈 */
    &:hover {
      background: rgba(64, 158, 255, 0.08); /* 浅蓝色半透明背景 */
      color: #409EFF;              /* 文字和图标变蓝 */
      transform: translateX(6px);  /* 🎨 核心修改：整体分类项平滑向右移，更有灵性 */
      
      .category-icon { color: #409EFF; }
      .category-arrow { 
        transform: translateX(3px); /* 箭头多移一点点，增加视觉前推感 */
        opacity: 1;                /* 箭头变清晰 */
      }
    }

    /* C. 激活态 (Active)：呼吸渐变 */
    &.active {
      background: linear-gradient(135deg, #409EFF 0%, #0076FF 100%); /* 🎨 使用渐变色块：替换纯蓝色块，呼应全局配色 */
      color: #ffffff;
      box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3); /* 🎨 激活项微弱外发光，增加呼吸感 */

      /* 激活态文字与图标全部白色 */
      .category-icon, .category-name, .category-arrow { color: #ffffff; opacity: 1; }
      
      /* 🎨 激活态取消位移反馈 */
      &:hover { transform: none; } 
    }
  }
}

.popover-ai-content {
  .ai-pulse {
    color: #409eff;
    animation: breath 2s infinite;
  }

  .prediction-main {
    .predict-item {
      margin-bottom: 15px;
      .predict-label-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin-bottom: 6px;
        .label { font-size: 13px; color: #606266; }
        .value { font-size: 20px; font-weight: bold; }
        .success-text { color: #67c23a; }
      }
      .base-info { font-size: 11px; color: #909399; margin-top: 5px; }
    }

    .salary-forecast-card {
      background: rgba(103, 194, 58, 0.08);
      border-radius: 8px;
      padding: 10px;
      .forecast-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        .f-label { color: #67c23a; font-size: 12px; font-weight: bold; }
        .f-value { color: #67c23a; font-size: 16px; font-weight: bold; }
      }
      .scarcity-info {
        font-size: 11px;
        color: #909399;
      }
    }
  }

  .mentor-suggestion {
    background: #f0f7ff;
    padding: 10px;
    border-radius: 6px;
    .suggestion-label { color: #409eff; font-weight: bold; font-size: 12px; }
    .suggestion-text { font-size: 12px; color: #606266; margin: 4px 0 0; }
  }
}

@keyframes breath {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

.middle-panel {
  display: flex;          /* 🌟 开启布局 */
  flex-direction: column; /* 纵向排列 */
  gap: 20px;              /* 🌟 这里的 gap 代替你之前的 margin-top */
  height: 100%;           /* 填满 Grid 容器高度 */
}

/* 卡片主体材质 */
.feature-card {
  position: relative;
  flex: 1;
  min-height: 200px;
  border-radius: 20px;       /* 🎨 调大圆角：增加柔和感，从 16px 改为 20px */
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s ease; /* 🎨 平滑过渡：增加时长 */
  
  background-color: rgba(255, 255, 255, 0.7) !important; 
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  /* 🌟 修改点：投影增强 */
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.06) !important;


  // 去掉背景图 (约第 348 行)
  .card-bg {
    display: none; 
  }

  // 修改遮罩为有色玻璃 (约第 356 行)
  .card-overlay {
    display: block; 
    position: absolute;
    width: 100%;
    height: 100%;
    /* 🎨 关键核心修改：有色玻璃！ */
    /* 我们不使用图片的遮罩，而是直接填充一个非常淡的背景过渡色，让玻璃呈现同色系质感 */
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(175, 202, 244, 0.1) 100%);
  }

  // 修改文字样式 (约第 362 行)
  .card-content {
    position: relative;
    padding: 25px 40px;
    z-index: 1;
    text-align: left;
    /* 🎨 标题：增加文字投影和行高 */
  .card-title {
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 12px;
    text-shadow: none;
    line-height: 1.2;
    max-width: 60%;
    
    /* --- 新增：让标题看起来更有设计感 --- */
    letter-spacing: -1px;  /* 紧凑的字间距更有现代感 */
    display: flex;
    align-items: center;
    
    &::before {
      content: "";
      display: inline-block;
      width: 4px;
      height: 24px;
      margin-right: 12px;
      border-radius: 4px;
      background: currentColor; /* 自动继承标题的颜色 */
      opacity: 0.6;
    }
  }

    /* 🎨 描述文字：调淡并增加行高 */
    .card-desc {
      font-size: 15px;   /* 🎨 调小描述：从 16px 改为 15px */
      opacity: 0.8;
      margin-bottom: 25px;
      line-height: 1.6;
      font-weight: 400; /* 使用普通粗细与标题形成对比 */
      max-width: 60%;
    }

    /* 🎨 修改按钮：不再使用纯色，而是使用渐变边框或半透明色 */
    .card-btn {
      padding: 10px 30px;
      font-size: 14px;
      border-radius: 25px;
      background: rgba(255, 255, 255, 0.8); /* 🎨 半透明白色按钮：增加轻盈感 */
      color: #334455;   /* 按钮文字深灰蓝 */
      border: 1px solid rgba(255, 255, 255, 0.9);
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03); /* 按钮轻阴影 */

      &:hover {
        transform: translateY(-2px); /* 悬停向上微动 */
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
      }
    }
  }
}

/* --- 以下是补充的独有样式 --- */

/* A. 探索岗位卡片 (粉橙色系) */
.explore-card {
  /* 标题颜色与之前保持一致 */
  .card-content .card-title {
    color: #a8b6ff;
  }

  /* 核心彩色插图代码 (使用伪元素 after) */
  &::after {
    content: "";
    position: absolute;
    top: 50%;
    right: -20px; /* 🎨 技巧：让插图稍微超出右边界，更灵动 */
    transform: translateY(-50%);
    width: 280px;  /* 🎨 稍微调大图片，占据更多右半部分 */
    height: 280px;
    
    /* 1. 设置插图背景：直接引入自带颜色的彩色图片 */
    background-image: url("@/assets/explore_color.png"); /* 🎨 请确保路径和文件名正确 */
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;

    /* 2. 核心：设置透明度蒙版 (实现靠近字越淡) */
    /* 我们用 CSS 写一个径向渐变：圆心在右侧，向左侧过渡到完全透明 */
    /* 在 CSS Mask 中，黑色代表可见，透明代表不可见 */
    -webkit-mask-image: radial-gradient(circle at 80% 50%, black 0%, black 30%, rgba(0, 0, 0, 0) 100%);
    mask-image: radial-gradient(circle at 80% 50%, black 0%, black 30%, rgba(0, 0, 0, 0) 100%);
    
    opacity: 0.8; /* 🎨 技巧：静态下保持较低透明度，作为背景装饰，不抢文字 */
    transition: all 0.5s ease;
    z-index: 0;   /* 🎨 关键：确保在内容文字下方 */
  }

  /* 🎨 悬停效果优化 */
  &:hover {
    background-color: rgba(231, 209, 236, 0.15); 
    border-color: rgba(200, 164, 214, 0.4);
    
    /* 悬停时，图片整体变清晰，并向左微动 */
    &::after {
      opacity: 0.6; /* 🎨 调高悬停透明度 */
      transform: translateY(-50%) translateX(-10px);
    }

    /* 按钮变色 */
    .card-btn {
      background: linear-gradient(135deg, #eaaef9 0%, #fad0c4 100%);
      color: #fff;
      border-color: transparent;
    }
  }
}

/* --- B. 开始测评卡片 (蓝绿色系) --- */
.assessment-card {
  /* 标题颜色与之前保持一致 */
  .card-content .card-title {
    color: #b1efbf;
  }

  /* 核心彩色插图代码 (使用伪元素 after) */
  &::after {
    content: "";
    position: absolute;
    top: 50%;
    right: -20px;
    transform: translateY(-50%);
    width: 280px;
    height: 280px;
    
    /* 1. 设置插图背景 */
    background-image: url("@/assets/assessment_color.png"); /* 🎨 请确保路径和文件名正确 */
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;

    /* 2. 核心：透明度蒙版 */
    -webkit-mask-image: radial-gradient(circle at 70% 50%, black 0%, black 40%, rgba(0, 0, 0, 0) 100%);
    mask-image: radial-gradient(circle at 70% 50%, black 0%, black 40%, rgba(0, 0, 0, 0) 100%);
    opacity: 0.8;
    transition: all 0.5s ease;
    z-index: 0;
  }

  /* 🎨 悬停效果优化 */
  &:hover {
    background-color: rgba(72, 187, 98, 0.699);
    border-color: rgba(177, 239, 191, 0.4);

    &::after {
      opacity: 0.6;
      transform: translateY(-50%) translateX(-10px);
    }

    /* 按钮变色 */
    .card-btn {
      background: linear-gradient(135deg, #afcaf4 0%, #b1efbf 100%);
      color: #fff;
      border-color: transparent;
    }
  }
}

/* B. 开始测评卡片 (蓝绿色系) */
.assessment-card {
  /* 标题变色 */
  .card-content .card-title {
    color: #88d098; /* 呼应背景的 #b1efbf */
  }

  /* 悬停时：卡片背景呈现淡淡的蓝绿色 */
  &:hover {
    background-color: rgba(177, 239, 191, 0.15);
    border-color: rgba(177, 239, 191, 0.4);

    .card-btn {
      background: linear-gradient(135deg, #afcaf4 0%, #b1efbf 100%);
      color: #fff;
      border-color: transparent;
    }
  }
}

/* 右列：登录面板 */
/* ========================================================== */
/* 🎨 登录面板美化：AI 科技感 + 毛玻璃材质 */
/* ========================================================== */

/* ========================================================== */
/* 🎨 登录面板美化：AI 科技感 + 毛玻璃材质 */
/* ========================================================== */


.auth-card {
  border-radius: 24px !important;
  background: rgba(255, 255, 255, 0.65) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);

  .login-form {
    padding: 20px;

    /* 顶部标题区域 */
    .form-header {
      text-align: center;
      margin-bottom: 30px;
      
      .user-avatar {
        background: linear-gradient(135deg, #409EFF 0%, #667eea 100%);
        box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
        margin-bottom: 12px;
      }
      .welcome-text {
        display: block;
        font-size: 22px;
        font-weight: 700;
        color: #303133;
      }
      .sub-text {
        font-size: 13px;
        color: #909399;
        margin-top: 6px;
      }
    }

    /* 登录按钮 */
    .submit-btn {
      width: 100%;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #409EFF 0%, #0076FF 100%);
      border: none;
      font-weight: 600;
      margin-top: 10px;
      transition: all 0.3s;
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(64, 158, 255, 0.3);
      }
    }

    /* 底部页脚区域 - 解决“混乱”的关键 */
    .form-footer {
      margin-top: 25px;
      display: flex;
      flex-direction: column;
      align-items: center; /* 居中所有内容 */

      .register-tip {
        font-size: 12px; /* 🎨 缩小字号 */
        color: #909399;
        margin-bottom: 20px;
        
        .register-link {
          color: #409EFF;
          font-weight: 500;
          margin-left: 4px;
          cursor: pointer;
          &:hover { text-decoration: underline; }
        }
      }

      .divider-text {
        width: 100%;
        font-size: 12px; /* 🎨 缩小字号 */
        color: #c0c4cc;
        text-align: center;
        margin-bottom: 15px;
        position: relative;
        
        /* 辅助线装饰 */
        &::before, &::after {
          content: "";
          position: absolute;
          top: 50%;
          width: 25%;
          height: 1px;
          background: rgba(0, 0, 0, 0.06);
        }
        &::before { left: 5%; }
        &::after { right: 5%; }
      }

      /* 第三方图标 */
      .social-icons {
        display: flex;
        justify-content: center; /* 🌟 核心：让三个圆圈在登录面板水平居中 */
        gap: 18px;               /* 圆圈之间的间距 */
        width: 100%;             /* 占满宽度以确保居中基准 */
        
        .icon-item {
          width: 38px;           /* 稍微调大一点点，更精致 */
          height: 38px;
          border-radius: 50%;
          background: #fff;
          border: 1px solid rgba(0, 0, 0, 0.05);
          display: flex;
          align-items: center;   /* 图标垂直居中 */
          justify-content: center; /* 图标水平居中 */
          color: #606266;
          transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
          cursor: pointer;
          
          /* 🌟 对内部 Element Plus 图标的微调 */
          .el-icon {
            font-size: 18px; 
          }
          
          &:hover {
            color: #409EFF;
            border-color: #409EFF;
            transform: translateY(-3px) scale(1.1); /* 悬停时轻微上浮 */
            background: rgba(64, 158, 255, 0.04);
            box-shadow: 0 4px 10px rgba(64, 158, 255, 0.1);
          }
        }
      }
    }
  }
}


// ========== 4. 动画定义 ==========
@keyframes gradientBG {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ========================================================== */
/* 🔥 5. 热门岗位推荐深度美化：精致网格与高级质感 */
/* ========================================================== */
/* ========================================================== */
/* 🔥 5. 热门岗位推荐美化：方案一 - “浮雕白”卡片 */
/* ========================================================== */
.hot-jobs-section {
  max-width: 1400px;
  margin: 60px auto 100px; /* 🌟 增加上下间距，拉开层级呼吸感 */
  padding: 0 40px;
  position: relative;
  z-index: 5;

  /* A. 标题区域美化 (保持之前的高级感) */
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    margin-top: 50px; 
    padding-left: 10px;
    border-left: 4px solid #409EFF; 
    
    .section-title { 
      font-size: 26px; font-weight: 800; color: #334455; letter-spacing: 1px;
    }

    :deep(.el-link) {
      font-size: 15px; font-weight: 600; color: rgba(51, 68, 85, 0.6); transition: all 0.3s;
      .el-icon { font-size: 14px; margin-left: 5px; transition: transform 0.3s ease; }
      &:hover { color: #409EFF; .el-icon { transform: translateX(4px); } }
    }
  }

  /* B. 网格布局 */
  /* 容器：隐藏溢出并确保全屏感 */
.infinite-scroll-wrapper {
  display: flex;
  flex-direction: column;
  gap: 30px; /* 两行之间的间距 */
  overflow: hidden;
  padding: 20px 0;
  width: 100%;
}

/* 滚动轨道容器 */
.scroll-row {
  width: 100%;
  height:210px; /* 固定高度，确保卡片完全显示 */
  overflow: hidden;
  background-color: #fafbfc00;
}

/* 实际滑动的长条 */
.scroll-track {
  display: flex;
  width: max-content; /* 核心：由内容撑开总宽度 */
  will-change: transform;
  transition: animation-play-state 0.3s ease;
}

/* 每一组卡片的包裹 */
.scroll-group {
  display: flex;
  gap: 30px; /* 卡片之间的间距 */
  padding-right: 30px; /* 确保克隆组拼接时间距一致 */
  padding-top: 5px;
}

/* 🌟 第一行动画：向左 */
.row-left .scroll-track {
  animation: scrollLeft 12s linear infinite;
}

/* 🌟 第二行动画：反向（向右） */
.row-right .scroll-track {
  animation: scrollLeft 14s linear infinite reverse;
}

.scroll-row {
  width: 100%;
  overflow: hidden;
  /* 确保 hover 判定范围覆盖整行 */
  padding: 10px 0; 
  
  /* 当鼠标悬停在这一行时，仅这一行的轨道停止动画 */
  &:hover {
    .scroll-track {
      animation-play-state: paused;
    }
  }
}

/* 定义无限滚动关键帧 */
@keyframes scrollLeft {
  0% {
    transform: translateX(0);
  }
  100% {
    /* 移动总宽度的一半（即移动完一整组卡片） */
    transform: translateX(-50%);
  }
}

/* 🌟 核心：针对每个卡片容器的深度美化 */
:deep(.job-card) {
  /* 基础形状与尺寸 */
  flex: 0 0 340px; 
  width: 340px;
  height: 150px; /* 固定高度保持整齐 */
  margin: 10px 15px; /* 给阴影留出扩散空间 */
  
  /* 玻璃拟态质感 */
  background: rgba(255, 255, 255, 0.65) !important;
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  
  /* 精致边框：模拟玻璃边缘亮光 */
  border: 1px solid rgba(255, 255, 255, 0.5) !important;
  border-radius: 20px !important;
    /* 弥散投影：极其轻微，防止浅色页面显得脏 */
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.04) !important;
  
  /* 动画过渡 */
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
  cursor: pointer;
  position: relative;
  overflow: hidden;

  /* 悬停效果：保持滚动的同时增强视觉反馈 */
  &:hover {
    background: rgba(255, 255, 254, 0.538) !important;
    transform: translateY(-8px) scale(1.03) !important; /* 向上轻微浮起 */
    box-shadow: 0 15px 45px rgba(137, 233, 250, 0.15) !important; /* 浅蓝色光晕 */
    border-color: rgba(70, 168, 171, 0.4) !important;
    
    /* 装饰：悬停时左侧出现彩色亮条 */
    &::after {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      height: 100%;
      width: 5px;
      background: linear-gradient(to bottom, #b9f2fc, #e599f857);
    }
  }

  /* 内部内容排版美化建议 */
  .el-card__body {
    padding: 20px 24px !important;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  /* 职位名称 */
  .job-name {
    font-size: 17px;
    font-weight: 700;
    color: #2c3e50;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
  }

  /* 公司与薪资行 */
  .job-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .company-name {
      font-size: 13px;
      color: #909399;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    
    .salary-tag {
      font-size: 15px;
      font-weight: 800;
      color: #f39c12; /* 高级感的琥珀色 */
      background: rgba(243, 156, 18, 0.08);
      padding: 2px 10px;
      border-radius: 8px;
    }
  }
}

/* 🌟 优化轨道遮罩，让两端消失感更自然 */
.infinite-scroll-wrapper {
  mask-image: linear-gradient(
    to right,
    transparent 0%,
    black 15%,
    black 85%,
    transparent 100%
  );
  -webkit-mask-image: linear-gradient(
    to right,
    transparent 0%,
    black 15%,
    black 85%,
    transparent 100%
  );
}


}

/* ========================================================== */
/* 右侧面板 right-panel 完整样式                            */
/* ========================================================== */

.roadmap-focus-card {
  background: rgba(255, 255, 255, 0.85) !important;
  backdrop-filter: blur(15px);
  border-radius: 24px !important;
  border: 1px solid rgba(64, 158, 255, 0.15) !important;
  height: 570px;
  display: flex;
  flex-direction: column;
}

.roadmap-focus-card :deep(.el-card__body) {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px 22px !important;
}

/* 顶部状态栏 */
.rp-status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 16px;

  .pulse-dot {
    width: 6px;
    height: 6px;
    background: #409eff;
    border-radius: 50%;
    box-shadow: 0 0 8px #409eff;
    animation: blink 1.5s infinite;
  }
}

/* 加载态 */
.rp-loading {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 20px 0;
}

/* ---- 空态 ---- */
.rp-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 20px;

  .rp-empty-illustration {
    width: 110px;
    height: 110px;
    animation: rpFloat 4s ease-in-out infinite;
    border-radius: 50%; /* 确保阴影的外形是完美的圆形 */
    box-shadow: 0 8px 24px rgba(149, 215, 247, 0.777); /* 核心阴影代码 */
    svg { width: 100%; height: 100%; }
  }

  .rp-empty-title {
    font-size: 17px;
    font-weight: 700;
    color: #303133;
  }

  .rp-empty-desc {
    font-size: 13px;
    color: #909399;
    text-align: center;
    line-height: 1.7;
  }

  .rp-empty-btn {
    margin-top: 4px;
    padding: 10px 28px;
    font-size: 14px;
    border-radius: 20px;
    background: linear-gradient(135deg, #98c8f7 0%, #f0cbe5 100%) !important;
    border: none !important;
    color: #fffff8 !important;
    box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
    transition: all 0.3s;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(64, 158, 255, 0.4);
    }
  }
}

@keyframes rpFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* ---- 有数据内容区 ---- */
.rp-content {
  flex: 1;
  position: relative;
  perspective: 1200px;
  overflow: hidden;
}

/* 翻页卡片 */
.rp-page {
  position: absolute;
  inset: 0;
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  transition: all 0.7s cubic-bezier(0.34, 1.56, 0.64, 1);
  background: #fff;
  border-radius: 14px;

  &.rp-page-front.is-back {
    transform: translateZ(-100px) translateY(20px) scale(0.88);
    opacity: 0.25;
    filter: blur(3px);
    pointer-events: none;
    z-index: 1;
  }

  &.rp-page-back {
    transform: translateZ(-100px) translateY(20px) scale(0.88);
    opacity: 0.25;
    filter: blur(3px);
    pointer-events: none;
    z-index: 1;

    &.is-front {
      transform: translateZ(0) translateY(0) scale(1);
      opacity: 1;
      filter: blur(0);
      pointer-events: auto;
      z-index: 2;
    }
  }

  &.rp-page-front:not(.is-back) {
    z-index: 2;
  }
}

/* 用户头像行 + 综合评分 */
.rp-user-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #ebeef5;
}

.rp-user-info {
  flex: 1;
  min-width: 0;
}

.rp-user-name {
  font-size: 15px;
  font-weight: 700;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.rp-user-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rp-score-badge {
  text-align: center;
  flex-shrink: 0;
}

.rp-score-num {
  font-size: 32px;
  font-weight: 900;
  line-height: 1;
  background: linear-gradient(135deg, #409EFF 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.rp-score-label {
  font-size: 10px;
  color: #909399;
  margin-top: 2px;
}

/* 七维度网格 */
.rp-radar-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  padding: 10px;
  background: rgba(64, 158, 255, 0.04);
  border-radius: 10px;
}

.rp-radar-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 5px 0;
}

.rp-radar-val {
  font-size: 15px;
  font-weight: 700;
  color: #c0c4cc;

  &.active { color: #409eff; }
}

.rp-radar-name {
  font-size: 10px;
  color: #909399;
}

/* 每日任务 */
.rp-tasks {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.rp-tasks-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;

  .el-icon { color: #409eff; }
}

.rp-tasks-tag {
  margin-left: auto;
}

.rp-tasks-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  max-height: 180px;
  overflow-y: auto;
  padding-right: 2px;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background: #dcdfe6;
    border-radius: 4px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

.rp-task-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  background: #fafafa;
  border-radius: 8px;
  transition: all 0.2s;

  &:hover {
    background: #f0f5ff;
    transform: translateX(3px);
  }
}

.rp-task-text {
  font-size: 13px;
  color: #303133;
  flex: 1;

  &.done {
    color: #c0c4cc;
    text-decoration: line-through;
  }
}

.rp-tasks-empty {
  font-size: 12px;
  color: #c0c4cc;
  text-align: center;
  padding: 20px 0;
}

/* 任务加载骨架屏 */
.rp-tasks-loading {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0;
}

.rp-task-skeleton {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: #fafafa;
  border-radius: 8px;

  .skel-check {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: rpShimmer 1.5s infinite;
    flex-shrink: 0;
  }

  .skel-line {
    height: 14px;
    border-radius: 4px;
    background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: rpShimmer 1.5s infinite;
  }
}

@keyframes rpShimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ---- 第二页：能力缺口 + Agent 建议 ---- */
.rp-gap-title {
  font-size: 14px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.rp-gap-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rp-gap-item {
  .rp-gap-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
  }

  .rp-gap-name {
    font-size: 13px;
    color: #303133;
    font-weight: 500;
  }

  .rp-gap-tag {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;

    &.danger { background: #fef0f0; color: #f56c6c; }
    &.warning { background: #fdf6ec; color: #e6a23c; }
    &.info { background: #f4f4f5; color: #909399; }
  }
}

/* Agent 建议 */
.rp-advice {
  margin-top: auto;
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
  border: 1px solid #d1e9ff;
  border-left: 4px solid #409eff;
  border-radius: 8px;
  padding: 12px;
}

.rp-advice-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
}

.rp-advice-icon {
  animation: rpBreath 2s infinite ease-in-out;
}

@keyframes rpBreath {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.7; }
}

.rp-advice-text {
  font-size: 12px;
  line-height: 1.7;
  color: #606266;
  margin: 6px 0 0;
}

/* 底部按钮 */
.rp-bottom-btn {
  width: 100%;
  margin-top: auto;
  font-size: 13px;
  background: transparent !important;
  color: #409eff !important;
  border-color: #409eff !important;

  &:hover {
    background: rgba(64, 158, 255, 0.05) !important;
  }
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(64, 158, 255, 0); }
  100% { box-shadow: 0 0 0 0 rgba(64, 158, 255, 0); }
}
@keyframes blink { 50% { opacity: 0.3; } }


/* ========================================================== */
/* 🔥 底部区域重构：Mobbin 数据粒子放射风 */
/* ========================================================== */

.hot-jobs-section {
  max-width: 1600px; /* 🌟 稍微加宽，给放射球更多呼吸空间 */
  margin: 120px auto 120px;
  padding: 0 40px;
  position: relative;
  z-index: 5;
  overflow: visible; /* 核心：隐藏溢出的球 */


}

/* 🌟 核心：数据粒子放射板块 */
.data-particle-field {
  position: relative;
  width: 100%;
  height: 700px; /* 🌟 核心：手动锁定高度，形成一个放射场 */
  margin-top: -100px;
  margin-bottom: 20px; /* 🎨 技巧：让下方的列表向上融合进去，产生流动感 */
  display: flex;
  align-items: center;
  justify-content: center;
  perspective: 1000px; /* 🎨 高级：增加 3D 透视感，让球看起来有远近 */

  .bg-canvas {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: -3;
    pointer-events: none;
    background: radial-gradient(circle at center, #f8faff 0%, transparent 50%);
  }


  
  /* SVG 连线层 */
  .connection-lines {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: -1;
    pointer-events: none;
    overflow: visible;

    .orbit-ring {
      transform-origin: center;
      animation: rotateRing 60s linear infinite;
    }
    
    path {
      animation: pulse-dash 2s linear infinite;
    }
  }

  &::before {
    content: "";
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 100%; /* 🌟 铺满整个屏幕宽度 */
    height: 100%;
    z-index: -2; /* 在最底层 */
    background: 
      radial-gradient(circle at 45% 25%, rgba(202, 229, 253, 0.654) 0%, transparent 35%), 
      radial-gradient(circle at 60% 65%, rgba(201, 163, 244, 0.267) 0%, transparent 30%);
    filter: blur(10px); /* 稍微减小模糊值，让色彩焦点更凝聚 */
    animation: quantumGlow 15s ease-in-out infinite alternate;
  }

  /* 🌟 第二层：流动的量子微粒（这就是你说的微小量子） */
  &::after {
    content: "";
    position: absolute;
    top: -100px; left: 0; width: 100%; height: calc(100% + 200px);
    z-index: -1;
    /* 🌟 使用更明显的颜色点，并增加密度 */
    background-image: 
      radial-gradient(circle at 1.5px 1.5px, rgba(64, 158, 255, 0.15) 1px, transparent 0);
    background-size: 40px 40px; /* 🌟 缩小尺寸以增加量子点数量 */
    mask-image: radial-gradient(circle at center, black 30%, transparent 90%);
    opacity: 0.6;
    animation: quantumParticles 25s linear infinite;
  }
}

.post-sphere {
  position: absolute; 
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  
  /* 🌟 原本的 transition 不要了！因为会和 GSAP 冲突导致卡顿 */
  /* transition: all 0.4s; -> 删除 */
  
  /* 极致毛玻璃材质 (Stitch 风格) */
  background: rgba(255, 255, 255, 0.4) !important; 
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6) !important;
  
  /* 发光内阴影与悬浮外阴影 */
  box-shadow: 
    inset 0 1px 1px rgba(255, 255, 255, 0.8),
    0 10px 40px -10px rgba(177, 138, 255, 0.15) !important;

  .label {
    font-size: 13px; font-weight: 700; color: #303133; text-align: center;
    padding: 10px;
    transition: color 0.3s;
  }

  /* 悬停时的光效爆发现果 */
  &:hover {
    background: rgba(255, 255, 255, 0.8) !important;
    box-shadow: 0 0 35px rgba(0, 219, 230, 0.3) !important;
    z-index: 20; /* 悬停时置顶 */
    .label { color: #409EFF; }
  }
}

/* 轨道与流光动画 */
@keyframes pulse-dash {
  to { stroke-dashoffset: -20; }
}
@keyframes rotateRing {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* --- 注意：请删除原 CSS 中给 .sphere-1 到 sphere-16 写的 animation: floatRandomly ... --- */
/* 因为现在我们使用更强大、更平滑的 GSAP 来接管它们的浮动了！ */

/* A. 中间核心文字样式 */
.center-text-block {
  text-align: center;
  z-index: 10;
  color: #334455;
  
  .small-title {
    font-size: 14px; color: #90a4ae; font-weight: 500; margin-bottom: 8px;
    letter-spacing: 2px;
  }
  .big-data {
    font-size: 52px; font-weight: 800; line-height: 1.2; margin-bottom: 12px;
    letter-spacing: -2px; /* 🎨 技巧：紧凑字间距增加精致感 */
    
    .highlight { 
      background: linear-gradient(135deg, #409EFF 0%, #0076FF 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      font-weight: 900;
    }
  }
  .ai-analysis {
    font-size: 26px; font-weight: 600; color: rgba(51, 68, 85, 0.7);
    text-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); /* 微弱投影 */
  }
}

/* B. 周围发散出去的“岗位球”通用样式 */
.post-sphere {
  position: absolute; /* 🌟 核心：全绝对定位 */
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  
  /* 🌟 修改点：透明度从 0.6 改为 0.92，增加实体感 */
  background: rgba(255, 255, 255, 0.15) !important; 
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.2);  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05) !important;
  cursor: pointer;
  overflow: hidden;

  box-shadow: 
    0 8px 32px 0 rgba(31, 38, 135, 0.1),
    inset 0 0 10px rgba(255, 255, 255, 0.2);
    
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  /* 文字样式微调 */
  .label {
    font-size: 13px; font-weight: 600; color: #409EFF; text-align: center;
    padding: 10px;
  }

  /* 悬停交互美化 (Hover) */
  &:hover {
    background: rgba(64, 158, 255, 0.3) !important; /* 淡淡的品牌色主题 */
  border: 1px solid rgba(64, 158, 255, 0.5);
  transform: scale(1.2) translateY(-5px) !important;
  box-shadow: 0 0 20px rgba(64, 158, 255, 0.4);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
  }
}

.post-sphere::before {
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    45deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  transform: rotate(45deg);
  animation: shine 4s infinite linear;
}

@keyframes shine {
  0% { transform: translateX(-100%) rotate(45deg); }
  100% { transform: translateX(100%) rotate(45deg); }
}

/* C. 🌟 精细控制每一个球的位置、大小和动画时差 */
/* 参考 Mobbin 布局进行手动微调 */

/* sphere-1：左上 (前端) */
.sphere-1 {
  width: 90px; height: 90px;
  top: 18%; left: 28%;
  transform: translateZ(50px); /* 🎨 高级：利用 Z 轴拉近远近感 */
  background: linear-gradient(135deg, #f9d1c0 0%, #fcfbe3 100%) !important; /* 🌟 核心修改：使用同色系渐变替换纯白，更有 AI 玻璃感 */
}

/* sphere-2：左下 (产品) */
.sphere-2 {
  width: 100px; height: 100px;
  top: 60%; left: 20%;
  transform: translateZ(-20px);
  background: linear-gradient(135deg, #fffbeb 0%, #dffec7 100%) !important; /* 🌟 核心修改：使用同色系渐变替换纯白，更有 AI 玻璃感 */
}

/* sphere-3：上方 (AI算法 - 最核心) */
.sphere-3 {
  width: 120px; height: 120px;
  top: 10%; left: 45%;
  transform: translateZ(100px); /* 最靠前 */
  background: linear-gradient(135deg, #abcff6 0%, #c4efeb 100%) !important; 
}

/* sphere-4：右上 (网络安全) */
.sphere-4 {
  width: 85px; height: 85px;
  top: 18%; left: 75%;
  transform: translateZ(30px);
  background: linear-gradient(135deg, #fef2f2 0%, #fee4fa 100%) !important; /* 🌟 核心修改：使用同色系渐变替换纯白，更有 AI 玻璃感 */
}

/* sphere-5：右下 (后端) */
.sphere-5 {
  width: 95px; height: 95px;
  top: 60%; left: 78%;
  transform: translateZ(10px);
  background: linear-gradient(135deg, #f0f9eb 0%, #d8f3f3 100%) !important; /* 🌟 核心修改：使用同色系渐变替换纯白，更有 AI 玻璃感 */
}

/* sphere-6：中左 (数据分析) */
.sphere-6 {
  width: 75px; height: 75px;
  top: 35%; left: 10%;
  transform: translateZ(-50px); /* 🎨 高级：最远处的球，增加景深感 */
}

/* sphere-7：中右 (UI/UX) */
.sphere-7 {
  width: 80px; height: 80px;
  top: 38%; left: 85%;
  transform: translateZ(-40px); /* 🎨 高级：最远处的球，增加景深感 */
}

/* sphere-8：底部 (运维) */
.sphere-8 {
  width: 90px; height: 90px;
  top: 65%; left: 50%;
  transform: translateZ(-10px); /* 🎨 高级：最远处的球，增加景深感 */
}

.sphere-9 {
  width: 70px; height: 70px;
  top: 80%; left: 52%;
  transform: translateZ(-30px); /* 🌟 核心：translateZ 为负值，远景 */
  opacity: 0.7 !important; /* 🌟 淡出感 */
}

/* sphere-10：左上偏左 (全栈) */
.sphere-10 {
  width: 65px; height: 65px;
  top: 8%; left: 8%;
  transform: translateZ(-50px);
  opacity: 0.6 !important;
}

/* sphere-11：中右偏下 (移动端) */
.sphere-11 {
  width: 72px; height: 72px;
  top: 50%; left: 92%;
  transform: translateZ(-60px);
  opacity: 0.5 !important;
}

/* sphere-12：顶部偏右 (云计算) */
.sphere-12 {
  width: 60px; height: 60px;
  top: 2%; left: 62%;
  transform: translateZ(-80px);
  opacity: 0.4 !important; /* 🌟 最淡 */
}

/* sphere-13：底部偏左 (架构师) */
.sphere-13 {
  width: 75px; height: 75px;
  top: 78%; left: 28%;
  transform: translateZ(-40px);
  opacity: 0.7 !important;
}

/* sphere-14：底部偏右 (交互设计) */
.sphere-14 {
  width: 68px; height: 68px;
  top: 75%; left: 68%;
  transform: translateZ(-55px);
  opacity: 0.6 !important;
}

/* sphere-15：左中偏下 (游戏开发) */
.sphere-15 {
  width: 70px; height: 70px;
  top: 50%; left: 4%;
  transform: translateZ(-70px);
  opacity: 0.5 !important;
}

/* sphere-16：顶部中央偏左 (IOT) */
.sphere-16 {
  width: 62px; height: 62px;
  top: 3%; left: 32%;
  transform: translateZ(-90px);
  opacity: 0.4 !important;
}



/* D. 下方原本列表区域的样式修正 (移除了 header) */
.jobs-list-container {
  max-width: 1400px;
  margin: 0 auto;
}

/* ======= E. 动画定义 ======= */
/* 核心：模仿 Mobbin 的轻微随机漂浮感 */
/* 修改后的更大幅度浮动动画 */
@keyframes floatRandomly {
  0% { 
    transform: translateY(0) rotate(0deg) translateZ(0); 
  }
  33% { 
    /* 向上位移加大，增加左右摇摆 */
    transform: translateY(-35px) translateX(-10px) rotate(6deg) translateZ(10px); 
  }
  66% { 
    /* 向下位移加大，反向旋转 */
    transform: translateY(20px) translateX(15px) rotate(-5deg) translateZ(-5px); 
  }
  100% { 
    transform: translateY(0) rotate(0deg) translateZ(0); 
  }
}

@keyframes Blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ===== 通用投影补充 ===== */
:deep(.job-card) {
  /* 🌟 修改点：投影增强 */
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08) !important;
}

.home-footer {
  padding: 5px;
  text-align: center;
  color: #909399;
  border-top: 1px solid #e4e7ed;
  background: #fff;
}

/* 🌟 量子背景大团块的缓慢漂移 */
@keyframes quantumFlow {
  0% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(180deg) scale(1.1); }
  100% { transform: rotate(360deg) scale(1); }
}

/* 🌟 微小粒子的呼吸感和极小的位移 */
@keyframes particleDrift {
  0% { 
    transform: translate(0, 0); 
    opacity: 0.3;
  }
  50% { 
    transform: translate(-20px, 20px); 
    opacity: 0.6;
  }
  100% { 
    transform: translate(0, 0); 
    opacity: 0.3;
  }
}

/* 🌟 量子光晕的呼吸效果：让背景颜色深浅交替 */
@keyframes quantumGlow {
  0% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
  100% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
}

/* 🌟 微小量子的匀速流动：产生“数据流”的视觉感 */
@keyframes quantumParticles {
  from {
    background-position: 0 0;
  }
  to {
    /* 🌟 让背景坐标移动，产生粒子向下流动的错觉 */
    background-position: 0 1000px;
  }
}
</style>