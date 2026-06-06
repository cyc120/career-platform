<template>
  <div class="job-match-container">
    <!-- 顶部标题栏 -->
    <div class="action-bar">
      <h2 class="page-title">
        <el-icon><Briefcase /></el-icon>
        人岗匹配
      </h2>
      <p class="page-desc">职能助手融合多维数据，为你精准匹配最佳岗位</p>
    </div>

    <div class="job-match-content">
      <!-- 加载状态 -->
      <transition name="loading-fade">
        <div v-if="loading" class="loading-section">
        <InteractiveLoading
          title="匹配分析中"
          description="正在融合多维数据，为你精准匹配最佳岗位"
          statusText="职能助手匹配引擎运行中"
          :steps="loadingSteps"
          :currentStep="currentStep"
          :progress="progressPercent"
          :showProgress="true"
          :orbLabels="['前端', '后端', '算法', '数据', '产品', '安全', '运维', '设计']"
        />
      </div>
      </transition>

      <!-- 无数据状态 -->
      <div v-if="!loading && !hasData" class="empty-section">
        <div class="empty-card glass-card">
          <div class="empty-icon">
            <el-icon :size="64"><Briefcase /></el-icon>
          </div>
          <h3>暂无匹配数据</h3>
          <p>请先在「个人信息」中完成对话分析，生成个人画像后系统将自动进行匹配</p>
        </div>
      </div>

      <!-- 匹配结果 -->
      <template v-if="!loading && hasData">
        <!-- 匹配概览 Hero 区 -->
        <div class="hero-stats">
          <div class="stat-card">
            <div class="stat-icon"><el-icon><List /></el-icon></div>
            <div class="stat-body">
              <span class="stat-num">{{ rankedResults.length }}</span>
              <span class="stat-label">匹配岗位</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon icon-score"><el-icon><DataAnalysis /></el-icon></div>
            <div class="stat-body">
              <span class="stat-num">{{ selectedJob.total_score || '--' }}</span>
              <span class="stat-label">最高评分</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon icon-industry"><el-icon><OfficeBuilding /></el-icon></div>
            <div class="stat-body">
              <span class="stat-num text-sm">{{ selectedJob.industry || '--' }}</span>
              <span class="stat-label">目标行业</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon icon-level"><el-icon><Aim /></el-icon></div>
            <div class="stat-body">
              <span class="stat-num text-sm">{{ getScoreLevel(selectedJob.total_score || 0) }}</span>
              <span class="stat-label">匹配等级</span>
            </div>
          </div>
        </div>

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
                :style="{ animationDelay: `${idx * 0.06}s` }"
                @click="selectJob(idx)"
              >
                <div class="rank-badge" :class="getRankClass(idx)">{{ idx + 1 }}</div>
                <div class="job-info">
                  <div class="job-title-row">
                    <span class="job-title">{{ job.job_title }}</span>
                    <span class="job-company">{{ job.company }}</span>
                    <span :class="['match-level-tag', getScoreLevelClass(job.total_score)]">
                      {{ getScoreLevel(job.total_score) }}
                    </span>
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
                  <el-progress
                    :percentage="job.total_score"
                    :stroke-width="4"
                    :show-text="false"
                    :color="getProgressColor(job.total_score)"
                    class="job-score-bar"
                  />
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
              匹配简评
            </h3>
            <p class="summary-text" v-html="highlightedSummary"></p>
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
                <div class="dim-dual-bar">
                  <div class="bar-track">
                    <div class="bar-fill bar-user" :style="{ width: `${dim.score}%`, background: getProgressColor(dim.score) }"></div>
                  </div>
                  <div v-if="dim.expected > 0" class="bar-track bar-expected-track">
                    <div class="bar-fill bar-expected" :style="{ width: `${dim.expected}%` }"></div>
                  </div>
                </div>
                <div class="bar-legend">
                  <span class="legend-user"><i></i> 当前</span>
                  <span v-if="dim.expected > 0" class="legend-expected"><i></i> 期望 {{ dim.expected }}</span>
                </div>
                <div v-if="dim.gap" :class="['dim-gap', getGapClass(dim.score, dim.expected)]">
                  <el-icon><Warning /></el-icon>
                  <span>{{ dim.gap }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 岗位要求展开面板 -->
          <div v-if="selectedJob.job_description || selectedJob.requirements" class="glass-card job-desc-card">
            <h3 class="card-title" @click="descExpanded = !descExpanded" style="cursor: pointer;">
              <el-icon><Document /></el-icon>
              岗位要求
              <el-icon class="expand-arrow" :class="{ expanded: descExpanded }"><ArrowDown /></el-icon>
            </h3>
            <el-collapse-transition>
              <div v-show="descExpanded" class="desc-content">
                <div v-if="selectedJob.job_description" class="desc-section">
                  <h4>岗位描述</h4>
                  <p>{{ selectedJob.job_description }}</p>
                </div>
                <div v-if="selectedJob.requirements" class="desc-section">
                  <h4>任职要求</h4>
                  <p>{{ selectedJob.requirements }}</p>
                </div>
              </div>
            </el-collapse-transition>
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
  Briefcase, OfficeBuilding, Lock, Unlock,
  Document, ArrowDown
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
  return Object.entries(scores).map(([name, val]) => {
    const score = typeof val === 'object' ? val.score : val
    const gap = typeof val === 'object' ? val.gap : ''
    return {
      name,
      score,
      gap,
      expected: parseExpectedScore(gap),
    }
  })
})

const parseExpectedScore = (gap) => {
  if (!gap) return 0
  const m = gap.match(/(\d+)/)
  if (!m) return 0
  const val = parseInt(m[1])
  return val >= 10 && val <= 100 ? val : 0
}

const getGapClass = (score, expected) => {
  if (!expected) return ''
  if (score >= expected) return 'gap-good'
  if (score >= expected - 10) return 'gap-close'
  return 'gap-bad'
}

// ==================== AI 简评高亮 ====================
const highlightedSummary = computed(() => {
  const text = selectedJob.value.summary || '暂无简评'
  const dimNames = ['专业技能', '证书资质', '创新能力', '学习能力', '抗压能力', '沟通能力', '实习', '项目经验']
  const pattern = new RegExp(`(\\d+\\.?\\d*分|\\d+%|${dimNames.join('|')}|卓越|高度匹配|良好|不足|超出|需提升|建议)`, 'g')
  return text.replace(pattern, '<mark>$1</mark>')
})

// ==================== 岗位描述展开 ====================
const descExpanded = ref(false)

watch(selectedIndex, () => {
  descExpanded.value = false
  nextTick(() => updateRadarChart())
})

// ==================== 匹配逻辑 ====================
const startMatch = async () => {
  loading.value = true
  rankedResults.value = []
  selectedIndex.value = 0

  // 每次匹配自动清除旧锁定
  lockedJobKey.value = ''
  hasMatchData.value = false
  parentSelectedJob.value = null
  matchingApi.clearSelectedJob().catch(() => {})

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
    nextTick(() => startMatch())
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

/* 顶部操作栏 */
.action-bar {
  padding: 14px 20px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.5), rgba(240, 248, 255, 0.3));
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  margin-bottom: 16px;

  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 8px;
    .el-icon { color: #5098f9; font-size: 22px; }
  }
  .page-desc {
    margin: 5px 0 0;
    font-size: 13px;
    color: #94a3b8;
    font-weight: 500;
  }
}

/* 加载状态 - 自适应容器大小 */
.loading-section {
  height: 78vh;
  min-height: 580px;
  border-radius: 20px;
  overflow: hidden;
}

.loading-fade-enter-active,
.loading-fade-leave-active { transition: opacity 0.5s ease; }
.loading-fade-enter-from,
.loading-fade-leave-to { opacity: 0; }

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
    bottom: -150px;
    right: -50px;
    width: 800px;
    height: 500px;
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

/* ========================================================== */
/* Hero Stats */
/* ========================================================== */
.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
  animation: fadeIn 0.4s ease-out;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(20px) saturate(1.1);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.07);
    background: rgba(255, 255, 255, 0.55);
  }

  .stat-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(80,152,249,0.12) 0%, rgba(80,152,249,0.06) 100%);
    color: #5098f9;
    font-size: 20px;
    flex-shrink: 0;

    &.icon-score { background: linear-gradient(135deg, rgba(107,208,137,0.12) 0%, rgba(107,208,137,0.06) 100%); color: #6bd089; }
    &.icon-industry { background: linear-gradient(135deg, rgba(232,158,90,0.12) 0%, rgba(232,158,90,0.06) 100%); color: #e89e5a; }
    &.icon-level { background: linear-gradient(135deg, rgba(148,95,185,0.12) 0%, rgba(148,95,185,0.06) 100%); color: #945fb9; }
  }

  .stat-body {
    display: flex;
    flex-direction: column;
  }

  .stat-num {
    font-size: 24px;
    font-weight: 800;
    color: #1e293b;
    line-height: 1.2;

    &.text-sm { font-size: 15px; }
  }

  .stat-label {
    font-size: 12px;
    color: #94a3b8;
    margin-top: 2px;
  }
}

/* ========================================================== */
/* Enhanced Job List Item */
/* ========================================================== */
@keyframes itemSlideIn {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}

.match-level-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 600;
  white-space: nowrap;
  margin-left: auto;

  &.badge-success { background: rgba(107,208,137,0.12); color: #6bd089; }
  &.badge-warning { background: rgba(232,158,90,0.12); color: #e89e5a; }
  &.badge-danger { background: rgba(244,76,76,0.12); color: #f44c4c; }
}

.job-score-bar {
  margin-top: 6px;
  :deep(.el-progress-bar__outer) { background-color: rgba(60,78,104,0.04); }
  :deep(.el-progress-bar__inner) { border-radius: 10px; }
}

.job-item {
  animation: itemSlideIn 0.35s cubic-bezier(0.23, 1, 0.32, 1) both;

  &.selected {
    position: relative;
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 8px;
      bottom: 8px;
      width: 3px;
      background: linear-gradient(180deg, #5098f9, #667eea);
      border-radius: 3px;
    }
  }
}

/* ========================================================== */
/* Job Description Card */
/* ========================================================== */
.job-desc-card {
  .expand-arrow {
    margin-left: auto;
    font-size: 14px;
    color: #94a3b8;
    transition: transform 0.3s ease;
    &.expanded { transform: rotate(180deg); }
  }

  .desc-content {
    padding-top: 8px;
  }

  .desc-section {
    margin-bottom: 16px;
    &:last-child { margin-bottom: 0; }

    h4 {
      font-size: 13px;
      font-weight: 700;
      color: #5098f9;
      margin: 0 0 8px;
      padding-left: 10px;
      border-left: 3px solid;
      border-image: linear-gradient(180deg, #5098f9, #667eea) 1;
    }

    p {
      margin: 0;
      font-size: 13px;
      color: #3c4e68;
      line-height: 1.9;
      white-space: pre-wrap;
      background: rgba(255, 255, 255, 0.3);
      padding: 12px 16px;
      border-radius: 10px;
    }
  }
}

/* ========================================================== */
/* Enhanced Dimension Dual Bar */
/* ========================================================== */
.dim-dual-bar {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 4px;
}

.bar-track {
  height: 6px;
  background: rgba(60, 78, 104, 0.06);
  border-radius: 10px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.6s cubic-bezier(0.23, 1, 0.32, 1);

  &.bar-expected {
    background: rgba(80, 152, 249, 0.2);
    border: 1px dashed rgba(80, 152, 249, 0.35);
  }
}

.bar-legend {
  display: flex;
  gap: 14px;
  margin-bottom: 4px;
  font-size: 10px;
  color: #94a3b8;

  span {
    display: flex;
    align-items: center;
    gap: 4px;

    i {
      display: inline-block;
      width: 14px;
      height: 3px;
      border-radius: 2px;
    }
  }

  .legend-user i { background: #5098f9; }
  .legend-expected i { background: rgba(80,152,249,0.2); border: 1px dashed rgba(80,152,249,0.35); }
}

.dim-gap {
  &.gap-good { color: #6bd089; .el-icon { color: #6bd089; } }
  &.gap-close { color: #5098f9; .el-icon { color: #5098f9; } }
  &.gap-bad { color: #e89e5a; .el-icon { color: #e89e5a; } }
}

/* ========================================================== */
/* Enhanced Summary */
/* ========================================================== */
.summary-card .summary-text :deep(mark) {
  background: linear-gradient(135deg, rgba(80,152,249,0.12) 0%, rgba(140,151,246,0.12) 100%);
  color: #5098f9;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.summary-card .summary-text {
  border-image: linear-gradient(180deg, #e89e5a, #fcd37e) 1;
}

/* ========================================================== */
/* Animations */
/* ========================================================== */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ========================================================== */
/* Responsive */
/* ========================================================== */
@media (max-width: 900px) {
  .hero-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .overview-row {
    flex-direction: column;
    .radar-card { flex: none; }
  }

  .dimensions-card .dimensions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
