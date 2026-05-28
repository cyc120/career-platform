<template>
  <div class="job-match-container">
    <div class="job-match-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-section">
        <InteractiveLoading
          title="智能匹配分析中"
          description="正在融合多维数据，为你精准匹配最佳岗位"
          statusText="AI 匹配引擎运行中"
          :steps="loadingSteps"
          :currentStep="currentStep"
          :progress="progressPercent"
          :showProgress="true"
          :orbLabels="['前端', '后端', 'AI', '数据', '产品', '安全', '运维', '设计']"
        />
      </div>

      <!-- 无数据状态 -->
      <div v-else-if="!hasData" class="empty-section">
        <div class="empty-card glass-card">
          <div class="empty-icon">
            <el-icon :size="64"><Briefcase /></el-icon>
          </div>
          <h3>暂无匹配数据</h3>
          <p>请先在「个人信息」中完成 AI 对话分析，生成个人画像后系统将自动进行匹配</p>
        </div>
      </div>

      <!-- 匹配结果 -->
      <template v-else>
        <!-- 总览区域 -->
        <div class="overview-row">
          <!-- 左侧：最佳匹配雷达图 -->
          <div class="glass-card radar-card accent-blue">
            <h3 class="card-title">
              <el-icon><DataAnalysis /></el-icon>
              {{ selectedJob.job_title || '目标岗位' }} - 能力画像
            </h3>
            <div class="target-job-badge">
              <span class="company">{{ selectedJob.company }}</span>
              <span v-if="selectedJob.city" class="city">{{ selectedJob.city }}</span>
              <span v-if="selectedJob.salary_range" class="salary">{{ selectedJob.salary_range }}</span>
            </div>
            <div ref="radarRef" class="radar-chart"></div>
            <div class="total-score-display">
              <span class="score-num">{{ selectedJob.total_score }}</span>
              <span class="score-unit">分</span>
              <span :class="['score-badge', getScoreLevelClass(selectedJob.total_score)]">
                {{ getScoreLevel(selectedJob.total_score) }}
              </span>
            </div>
          </div>

          <!-- 右侧：匹配列表 -->
          <div class="glass-card list-card accent-green">
            <h3 class="card-title">
              <el-icon><List /></el-icon>
              匹配结果 ({{ rankedResults.length }} 个岗位)
            </h3>
            <div class="job-list">
              <div
                v-for="(job, idx) in rankedResults"
                :key="idx"
                :class="['job-item', { selected: selectedIndex === idx }]"
                @click="selectJob(idx)"
              >
                <div class="rank-badge" :class="getRankClass(idx)">{{ idx + 1 }}</div>
                <div class="job-info">
                  <div class="job-title-row">
                    <span class="job-title">{{ job.job_title }}</span>
                    <span class="job-company">{{ job.company }}</span>
                  </div>
                  <div class="job-meta">
                    <span v-if="job.city" class="meta-item">
                      <el-icon><Location /></el-icon> {{ job.city }}
                    </span>
                    <span v-if="job.salary_range" class="meta-item">
                      <el-icon><Money /></el-icon> {{ job.salary_range }}
                    </span>
                    <span v-if="job.industry" class="meta-item">
                      <el-icon><OfficeBuilding /></el-icon> {{ job.industry }}
                    </span>
                  </div>
                </div>
                <el-button
                  :type="isJobLocked(job) ? 'primary' : 'default'"
                  :icon="isJobLocked(job) ? Lock : Unlock"
                  :loading="lockingKey === getJobKey(job)"
                  :disabled="!!lockingKey && lockingKey !== getJobKey(job)"
                  size="small"
                  :class="['lock-btn', { locked: isJobLocked(job) }]"
                  @click.stop="lockJob(idx)"
                >
                  {{ isJobLocked(job) ? '已锁定' : '锁定' }}
                </el-button>
                <el-icon
                  v-if="job.job_id"
                  class="detail-icon"
                  @click.stop="router.push(`/job/${job.job_id}`)"
                ><Link /></el-icon>
                <div class="job-score">
                  <span class="score-value">{{ job.total_score }}</span>
                  <span class="score-label">分</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 选中岗位的详细分析 -->
        <div class="detail-section">
          <!-- AI 简评 -->
          <div class="glass-card summary-card accent-orange">
            <h3 class="card-title">
              <el-icon><ChatDotRound /></el-icon>
              AI 匹配简评
            </h3>
            <p class="summary-text">{{ selectedJob.summary || '暂无简评' }}</p>
          </div>

          <!-- 维度评分明细 -->
          <div class="glass-card dimensions-card">
            <h3 class="card-title">
              <el-icon><Histogram /></el-icon>
              七维度匹配详情
            </h3>
            <img src="@/assets/3D grow.png" class="dim-decoration" />
            <div class="dimensions-grid">
              <div
                v-for="(dim, idx) in dimensionList"
                :key="idx"
                class="dim-item"
              >
                <div class="dim-header">
                  <span class="dim-name">{{ dim.name }}</span>
                  <span class="dim-score" :class="getScoreClass(dim.score)">
                    {{ dim.score }}<small>分</small>
                  </span>
                </div>
                <el-progress
                  :percentage="dim.score"
                  :stroke-width="8"
                  :show-text="false"
                  :color="getProgressColor(dim.score)"
                  class="dim-progress"
                />
                <div v-if="dim.gap" class="dim-gap">
                  <el-icon><Warning /></el-icon>
                  <span>{{ dim.gap }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 改进建议 -->
          <div v-if="selectedJob.recommendations && selectedJob.recommendations.length > 0" class="glass-card recommend-card accent-green">
            <h3 class="card-title">
              <el-icon><Aim /></el-icon>
              改进建议
            </h3>
            <div class="recommend-list">
              <div
                v-for="(rec, idx) in selectedJob.recommendations"
                :key="idx"
                class="recommend-item"
              >
                <span class="rec-index">{{ idx + 1 }}</span>
                <span class="rec-text">{{ rec }}</span>
              </div>
            </div>
          </div>

          <!-- 查看岗位详情按钮 -->
          <div class="action-footer">
            <el-button
              :type="isJobLocked(selectedJob) ? 'primary' : 'success'"
              size="large"
              class="lock-main-btn"
              :icon="isJobLocked(selectedJob) ? Lock : Unlock"
              :loading="lockingKey === getJobKey(selectedJob)"
              :disabled="!!lockingKey && lockingKey !== getJobKey(selectedJob)"
              @click="lockJob(selectedIndex)"
            >
              {{ isJobLocked(selectedJob) ? '取消锁定当前岗位' : '锁定为目标岗位' }}
            </el-button>
            <el-button
              v-if="selectedJob.job_id"
              size="large"
              class="detail-btn"
              @click="goToJobDetail"
            >
              <el-icon class="el-icon--right"><Link /></el-icon>
              查看岗位详情
            </el-button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, List, Location, Money,
  ChatDotRound, Histogram, Warning, Aim, Link,
  Briefcase, OfficeBuilding, Lock, Unlock
} from '@element-plus/icons-vue'
import { matchingApi } from '@/api/matching'
import { currentRadarData, dimensionDetailsRaw, matchVersion } from './profileState.js'
import InteractiveLoading from '@/components/InteractiveLoading.vue'

const router = useRouter()
const hasMatchData = inject('hasMatchData', ref(false))
const parentSelectedJob = inject('selectedJob', ref(null))

// ==================== 缓存 ====================
const CACHE_KEY = 'job_match_cache'

const saveToCache = (results, index, profileHash) => {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({ results, index, profileHash }))
  } catch { /* quota exceeded, ignore */ }
}

const loadFromCache = () => {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

const clearCache = () => sessionStorage.removeItem(CACHE_KEY)

const hashProfile = (radar) => JSON.stringify(radar || [])

// ==================== 状态 ====================
const loading = ref(false)
const rankedResults = ref([])
const selectedIndex = ref(0)
const radarRef = ref(null)
let radarInstance = null

const loadingSteps = ['加载用户画像', 'RAG 检索匹配岗位', 'Neo4j 知识图谱增强', 'LLM 多维度评分', '生成匹配报告']
const currentStep = ref(0)
const progressPercent = ref(0)
let stepTimer = null
let progressTimer = null

const hasData = computed(() => rankedResults.value.length > 0)
const selectedJob = computed(() => rankedResults.value[selectedIndex.value] || {})
const lockedJobKey = ref('')
const lockingKey = ref('')

const dimensionList = computed(() => {
  const scores = selectedJob.value.scores || {}
  return Object.entries(scores).map(([name, val]) => ({
    name,
    score: typeof val === 'object' ? val.score : val,
    gap: typeof val === 'object' ? val.gap : '',
  }))
})

// ==================== 匹配逻辑 ====================
const startMatch = async ({ resetLock = false } = {}) => {
  loading.value = true
  rankedResults.value = []
  selectedIndex.value = 0
  if (resetLock) {
    lockedJobKey.value = ''
    hasMatchData.value = false
    parentSelectedJob.value = null
    matchingApi.clearSelectedJob().catch(() => {})
  }
  clearCache()
  // 清除成长追踪缓存，触发重新加载
  sessionStorage.removeItem('growth_tracker_cache')
  matchVersion.value++
  currentStep.value = 0
  progressPercent.value = 0

  // 模拟步骤进度
  stepTimer = setInterval(() => {
    if (currentStep.value < loadingSteps.length - 1) currentStep.value++
  }, 3000)

  // 平滑进度条
  progressTimer = setInterval(() => {
    if (progressPercent.value < 90) {
      progressPercent.value += Math.random() * 12
    }
  }, 400)

  try {
    // Build profile data from current frontend state
    const profilePayload = {}
    if (currentRadarData.value && currentRadarData.value.some(v => v > 0)) {
      profilePayload.radar_data = currentRadarData.value
    }
    if (dimensionDetailsRaw.value) {
      profilePayload.dimension_details = dimensionDetailsRaw.value
    }

    // Guard: no profile data at all → don't call API
    if (!profilePayload.radar_data) {
      ElMessage.warning('请先在「职能助手」中完成对话分析，生成个人画像后再进行匹配')
      return
    }

    const { data } = await matchingApi.match(profilePayload)

    const payload = data.data || data

    if (data.error || payload.error) {
      ElMessage.error(data.error || payload.error)
      return
    }

    const results = payload.ranked_results || payload.match_results || payload.matches || []
    if (results.length === 0) {
      ElMessage.warning(payload.error || '未找到匹配的岗位，请先完善简历信息')
      return
    }

    rankedResults.value = results
    selectedIndex.value = 0
    currentStep.value = loadingSteps.length - 1
    progressPercent.value = 100
    saveToCache(results, 0, hashProfile(currentRadarData.value))
    ElMessage.success(`匹配完成，共找到 ${results.length} 个岗位`)

    await nextTick()
    requestAnimationFrame(() => {
      initRadarChart()
      if (!resetLock) restoreLockState()
    })
  } catch (err) {
    console.error('[JobMatch] match failed:', err)
    ElMessage.error('匹配请求失败，请稍后重试')
  } finally {
    clearInterval(stepTimer)
    clearInterval(progressTimer)
    loading.value = false
  }
}

// ==================== 选中切换 ====================
const selectJob = (idx) => {
  selectedIndex.value = idx
  // persist selection to cache
  const cached = loadFromCache()
  if (cached) saveToCache(cached.results, idx, cached.profileHash)
  nextTick(() => updateRadarChart())
}

// ==================== 锁定岗位 ====================
const getJobKey = (job = {}) => {
  if (!job || Object.keys(job).length === 0) return ''
  return String(job.job_id || `${job.job_title || ''}__${job.company || ''}`)
}

const isJobLocked = (job) => !!lockedJobKey.value && lockedJobKey.value === getJobKey(job)

const clearLocalLockState = () => {
  lockedJobKey.value = ''
  hasMatchData.value = false
  parentSelectedJob.value = null
  sessionStorage.removeItem('growth_tracker_cache')
}

const lockJob = async (idx) => {
  const job = rankedResults.value[idx]
  const key = getJobKey(job)
  if (!job || !key || lockingKey.value) return

  lockingKey.value = key
  try {
    if (isJobLocked(job)) {
      await matchingApi.clearSelectedJob()
      clearLocalLockState()
      ElMessage.info('已取消锁定')
      return
    }

    selectedIndex.value = idx
    await matchingApi.selectJob(job)
    lockedJobKey.value = key
    hasMatchData.value = true
    parentSelectedJob.value = job
    sessionStorage.removeItem('growth_tracker_cache')
    ElMessage.success(`已锁定「${job.job_title || '目标岗位'}」`)
  } catch (err) {
    console.error('[JobMatch] lock job failed:', err)
    ElMessage.error(isJobLocked(job) ? '取消锁定失败，请重试' : '锁定失败，请重试')
  } finally {
    lockingKey.value = ''
  }
}

// 恢复锁定状态
const restoreLockState = async () => {
  try {
    const { data } = await matchingApi.getSelectedJob()
    if (data.success && data.data) {
      const saved = data.data
      const idx = rankedResults.value.findIndex(
        j => getJobKey(j) === getJobKey(saved) || (j.job_title === saved.job_title && j.company === saved.company)
      )
      if (idx >= 0) {
        lockedJobKey.value = getJobKey(rankedResults.value[idx])
        hasMatchData.value = true
        parentSelectedJob.value = rankedResults.value[idx]
      } else {
        lockedJobKey.value = getJobKey(saved)
        hasMatchData.value = true
        parentSelectedJob.value = saved
      }
    }
  } catch { /* ignore */ }
}

// ==================== 雷达图 ====================
const radarColors = {
  primary: '#5098f9',
  bg: 'rgba(80, 152, 249, 0.15)',
  border: 'rgba(80, 152, 249, 0.6)',
}

const DIM_NAMES = ['专业技能', '证书资质', '创新能力', '学习能力', '抗压能力', '沟通能力', '实习/项目经验']

const initRadarChart = () => {
  if (!radarRef.value) return
  if (radarInstance) { radarInstance.dispose(); radarInstance = null }

  const el = radarRef.value
  // container may not have layout yet — wait for it
  if (el.offsetWidth === 0 || el.offsetHeight === 0) {
    const ro = new ResizeObserver(() => {
      if (el.offsetWidth > 0 && el.offsetHeight > 0) {
        ro.disconnect()
        if (!radarInstance && radarRef.value) {
          radarInstance = echarts.init(radarRef.value)
          updateRadarChart()
        }
      }
    })
    ro.observe(el)
    return
  }

  radarInstance = echarts.init(el)
  updateRadarChart()
}

const updateRadarChart = () => {
  if (!radarInstance) return

  const scores = selectedJob.value.scores || {}
  const indicators = DIM_NAMES.map(name => ({ name, max: 100 }))
  const values = DIM_NAMES.map(name => {
    const v = scores[name]
    return typeof v === 'object' ? v.score : (v || 0)
  })

  radarInstance.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: 'rgba(80,152,249,0.1)',
      textStyle: { color: '#3c4e68', fontSize: 13 },
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      radius: '70%',
      center: ['50%', '52%'],
      axisName: {
        color: '#64748b',
        fontSize: 12,
        fontWeight: 500,
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(80,152,249,0.02)',
            'rgba(80,152,249,0.05)',
            'rgba(80,152,249,0.02)',
            'rgba(80,152,249,0.05)',
            'rgba(80,152,249,0.02)',
          ],
        },
      },
      axisLine: { lineStyle: { color: 'rgba(80,152,249,0.1)' } },
      splitLine: { lineStyle: { color: 'rgba(80,152,249,0.1)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: selectedJob.value.job_title || '匹配度',
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(80,152,249,0.3)' },
            { offset: 1, color: 'rgba(80,152,249,0.05)' },
          ]),
        },
        lineStyle: { color: radarColors.border, width: 2 },
        itemStyle: { color: radarColors.primary, borderColor: '#fff', borderWidth: 2 },
        symbol: 'circle',
        symbolSize: 6,
      }],
    }],
  })
}

// ==================== 跳转 ====================
const goToJobDetail = () => {
  const jobId = selectedJob.value.job_id
  if (jobId) {
    router.push(`/job/${jobId}`)
  } else {
    ElMessage.info('暂无岗位详情链接')
  }
}

// ==================== 辅助函数 ====================
const getScoreLevel = (score) => {
  if (score >= 90) return '卓越匹配'
  if (score >= 80) return '高度匹配'
  if (score >= 70) return '良好匹配'
  if (score >= 60) return '基本匹配'
  return '匹配度较低'
}

const getScoreLevelClass = (score) => {
  if (score >= 80) return 'badge-success'
  if (score >= 70) return 'badge-warning'
  return 'badge-danger'
}

const getScoreClass = (score) => {
  if (score >= 85) return 'score-excellent'
  if (score >= 70) return 'score-good'
  return 'score-warning'
}

const getRankClass = (idx) => {
  if (idx === 0) return 'rank-gold'
  if (idx === 1) return 'rank-silver'
  if (idx === 2) return 'rank-bronze'
  return ''
}

const getProgressColor = (score) => {
  if (score >= 85) return '#6bd089'
  if (score >= 70) return '#5098f9'
  return '#e89e5a'
}

// ==================== 响应式 ====================
const handleResize = () => radarInstance?.resize()

onMounted(() => {
  window.addEventListener('resize', handleResize)

  // restore cached results if profile hasn't changed
  const cached = loadFromCache()
  if (cached && cached.results?.length && hashProfile(currentRadarData.value) === cached.profileHash) {
    rankedResults.value = cached.results
    selectedIndex.value = cached.index || 0
    nextTick(() => {
      requestAnimationFrame(() => initRadarChart())
      restoreLockState()
    })
  } else if (currentRadarData.value && currentRadarData.value.some(v => v > 0) && rankedResults.value.length === 0) {
    // Auto-trigger matching when profile data exists and no valid cache
    nextTick(() => startMatch())
  }
})

onUnmounted(() => {
  clearInterval(stepTimer)
  clearInterval(progressTimer)
  radarInstance?.dispose()
  window.removeEventListener('resize', handleResize)
})

watch(selectedIndex, () => {
  nextTick(() => updateRadarChart())
})

// Profile changed → auto re-match
watch(currentRadarData, (newVal, oldVal) => {
  if (!newVal || !oldVal) return
  if (JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
    rankedResults.value = []
    selectedIndex.value = 0
    clearCache()
    if (radarInstance) {
      radarInstance.dispose()
      radarInstance = null
    }
    nextTick(() => startMatch({ resetLock: true }))
  }
})
</script>

<style scoped lang="scss">
.job-match-container {
  padding: 10px;
  background: transparent;
  min-height: calc(100vh - 60px);
  overflow-x: hidden;
}

.job-match-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 100px);
}

/* 玻璃卡片通用 */
.glass-card {
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(20px) saturate(1.1);
  -webkit-backdrop-filter: blur(20px) saturate(1.1);
  border-radius: 20px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
  margin-bottom: 24px;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.07);
    background: rgba(255, 255, 255, 0.5);
  }

  &.accent-blue .card-title .el-icon { color: #667eea; }
  &.accent-green .card-title .el-icon { color: #6bd089; }
  &.accent-orange .card-title .el-icon { color: #e89e5a; }
  &.accent-purple .card-title .el-icon { color: #945fb9; }

  .card-title {
    margin: 0 0 20px 0;
    font-size: 16px;
    font-weight: 600;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 10px;
    .el-icon { font-size: 19px; }
  }
}

/* 加载状态 - 自适应容器大小 */
.loading-section {
  flex: 1;
  min-height: 400px;
  border-radius: 20px;
  overflow: hidden;
}

/* 空状态 */
.empty-section {
  .empty-card {
    text-align: center;
    padding: 80px 24px;

    .empty-icon {
      color: #cbd5e1;
      margin-bottom: 20px;
    }
    h3 {
      margin: 0 0 10px;
      font-size: 18px;
      color: #64748b;
    }
    p {
      margin: 0;
      font-size: 13px;
      color: #94a3b8;
    }
  }
}

/* 总览行 */
.overview-row {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;

  .radar-card {
    flex: 0 0 420px;

    .target-job-badge {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
      flex-wrap: wrap;

      .company, .city, .salary {
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
      }
      .company { background: rgba(80, 152, 249, 0.1); color: #5098f9; }
      .city { background: rgba(107, 208, 137, 0.1); color: #6bd089; }
      .salary { background: rgba(232, 158, 90, 0.1); color: #e89e5a; }
    }

    .radar-chart {
      width: 100%;
      height: 280px;
    }

    .total-score-display {
      display: flex;
      align-items: baseline;
      justify-content: center;
      gap: 4px;
      margin-top: 8px;

      .score-num {
        font-size: 42px;
        font-weight: 800;
        background: linear-gradient(135deg, #a1c4fd 0%, #5098f9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
      }
      .score-unit {
        font-size: 14px;
        color: #94a3b8;
        font-weight: 600;
      }
      .score-badge {
        margin-left: 10px;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 700;
        color: #fff;

        &.badge-success { background: linear-gradient(135deg, #87dd9a, #6bd089); }
        &.badge-warning { background: linear-gradient(135deg, #fcd37e, #e89e5a); }
        &.badge-danger { background: linear-gradient(135deg, #f87a71, #f44c4c); }
      }
    }
  }

  .list-card {
    flex: 1;

    .job-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-height: 500px;
      overflow-y: auto;
      padding-right: 4px;

      &::-webkit-scrollbar { width: 4px; }
      &::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.08); border-radius: 10px; }
    }

    .job-item {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 14px 16px;
      background: rgba(255, 255, 255, 0.3);
      border-radius: 14px;
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.25s;

      &:hover {
        background: rgba(255, 255, 255, 0.5);
        border-color: rgba(80, 152, 249, 0.15);
        transform: translateY(-1px);
      }

      &.selected {
        background: rgba(80, 152, 249, 0.08);
        border-color: rgba(80, 152, 249, 0.25);
        box-shadow: 0 4px 16px rgba(80, 152, 249, 0.1);
      }

      .rank-badge {
        width: 28px;
        height: 28px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 700;
        color: #94a3b8;
        background: #f1f5f9;
        flex-shrink: 0;

        &.rank-gold { background: linear-gradient(135deg, #ffd700, #ffaa00); color: #fff; }
        &.rank-silver { background: linear-gradient(135deg, #c0c0c0, #a0a0a0); color: #fff; }
        &.rank-bronze { background: linear-gradient(135deg, #cd7f32, #b06c2a); color: #fff; }
      }

      .job-info {
        flex: 1;
        min-width: 0;

        .job-title-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;

          .job-title {
            font-size: 14px;
            font-weight: 600;
            color: #1e293b;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .job-company {
            font-size: 12px;
            color: #94a3b8;
            white-space: nowrap;
          }
        }

        .job-meta {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;

          .meta-item {
            display: flex;
            align-items: center;
            gap: 3px;
            font-size: 11px;
            color: #94a3b8;
            .el-icon { font-size: 12px; }
          }
        }
      }

      .job-score {
        display: flex;
        align-items: baseline;
        gap: 2px;
        flex-shrink: 0;

        .score-value {
          font-size: 22px;
          font-weight: 800;
          background: linear-gradient(135deg, #a1c4fd, #5098f9);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .score-label {
          font-size: 11px;
          color: #94a3b8;
          font-weight: 600;
        }
      }

      .lock-btn {
        flex-shrink: 0;
        width: 82px;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s;

        &.locked {
          box-shadow: 0 4px 12px rgba(80, 152, 249, 0.22);
        }
      }

      .detail-icon {
        flex-shrink: 0;
        cursor: pointer;
        color: var(--el-text-color-secondary);
        font-size: 16px;
        transition: color 0.2s;
        &:hover {
          color: var(--el-color-primary);
        }
      }
    }
  }
}

/* 详细分析区 */
.detail-section {
  animation: fadeIn 0.4s ease-out;
}

.summary-card {
  .summary-text {
    margin: 0;
    font-size: 14px;
    line-height: 1.8;
    color: #3c4e68;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    padding: 16px 20px;
    border-left: 4px solid #e89e5a;
  }
}

.dimensions-card {
  position: relative;
  overflow: hidden;

  .dim-decoration {
    position: absolute;
    bottom: -50px;
    right: -50px;
    width: 800px;
    height: 300px;
    opacity: 0.12;
    pointer-events: none;
    z-index: 0;
    -webkit-mask-image: radial-gradient(ellipse at center, rgba(0,0,0,1) 30%, rgba(0,0,0,0) 75%);
    mask-image: radial-gradient(ellipse at center, rgba(0,0,0,1) 30%, rgba(0,0,0,0) 75%);
  }

  .dimensions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 14px;
  }

  .dim-item {
    background: rgba(255, 255, 255, 0.3);
    padding: 16px;
    border-radius: 12px;
    transition: all 0.2s;

    &:hover {
      background: rgba(255, 255, 255, 0.5);
      transform: translateY(-1px);
    }

    .dim-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;

      .dim-name {
        font-size: 14px;
        font-weight: 600;
        color: #1e293b;
      }
      .dim-score {
        font-size: 18px;
        font-weight: 800;
        small { font-size: 11px; color: #94a3b8; margin-left: 1px; font-weight: 600; }
        &.score-excellent { color: #6bd089; }
        &.score-good { color: #5098f9; }
        &.score-warning { color: #e89e5a; }
      }
    }

    .dim-progress {
      margin-bottom: 6px;
      :deep(.el-progress-bar__outer) {
        background-color: rgba(60, 78, 104, 0.05);
      }
      :deep(.el-progress-bar__inner) {
        border-radius: 10px;
      }
    }

    .dim-gap {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #e89e5a;
      margin-top: 4px;
      .el-icon { font-size: 13px; }
    }
  }
}

.recommend-card {
  .recommend-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .recommend-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 10px;
    transition: all 0.2s;

    &:hover { background: rgba(255, 255, 255, 0.5); }

    .rec-index {
      width: 22px;
      height: 22px;
      border-radius: 6px;
      background: rgba(107, 208, 137, 0.15);
      color: #6bd089;
      font-size: 12px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .rec-text {
      font-size: 13px;
      color: #3c4e68;
      line-height: 1.6;
    }
  }
}

.action-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
  padding: 16px 0;

  .lock-main-btn,
  .detail-btn {
    border-radius: 12px;
    padding: 12px 32px;
    font-weight: 600;
    transition: all 0.3s;

    &:hover {
      transform: translateY(-2px);
    }
  }

  .lock-main-btn {
    border: none;
    box-shadow: 0 4px 16px rgba(107, 208, 137, 0.25);
  }

  .detail-btn {
    background: linear-gradient(135deg, #a1c4fd 0%, #5098f9 100%);
    border: none;
    box-shadow: 0 4px 16px rgba(80, 152, 249, 0.3);

    &:hover {
      box-shadow: 0 6px 24px rgba(80, 152, 249, 0.4);
    }
  }
}

/* 动画 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 900px) {
  .overview-row {
    flex-direction: column;

    .radar-card {
      flex: none;
    }
  }

  .dimensions-card .dimensions-grid {
    grid-template-columns: 1fr;
  }

}
</style>
