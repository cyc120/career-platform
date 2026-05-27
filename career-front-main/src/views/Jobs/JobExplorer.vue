<template>
  <div class="job-explorer">
    <header class="search-header">
      <div class="search-container">
        <el-input
          v-model="searchQuery"
          placeholder="搜索职位、公司或关键词"
          :prefix-icon="Search"
          size="large"
          class="custom-search"
          @input="debounceSearch"
        />
        <el-button type="primary" size="large" class="search-btn" @click="handleSearch">搜索</el-button>
      </div>

      <div class="filter-categories">
        <span
          v-for="category in filterCategories"
          :key="category.type"
          class="category-item"
          @click="openFilterDialog(category.type)"
        >
          {{ category.label }}
          <el-icon><ArrowDown /></el-icon>
        </span>
      </div>

      <div class="tag-container" v-if="selectedTags.length > 0">
        <el-tag v-for="tag in selectedTags" :key="tag.value" closable round @close="removeTag(tag)">
          {{ tag.label }}
        </el-tag>
      </div>
    </header>

    <main class="main-content">
      <section class="job-list">
        <div v-if="filteredJobs.length === 0" class="empty-state">
          <el-empty description="未找到相关职位" />
        </div>

        <div 
          class="job-card-container" 
          v-infinite-scroll="loadMore" 
          :infinite-scroll-disabled="disabled"
          :infinite-scroll-distance="20"
        >
          <div
            v-for="job in displayedJobs"
            :key="job.id"
            :class="['elegant-job-card', { 'is-active': hoveredJob?.id === job.id }]"
            @mouseenter="hoveredJob = job"
            @mouseleave="hoveredJob = null"
            @click="goToJobDetail(job.id)"
          >
            <div class="card-main">
              <div class="title-row">
                <span class="job-name">{{ job.title }}</span>
                <span class="job-salary">{{ job.salary }}</span>
              </div>
              <div class="company-row">
                <span class="comp-name">{{ job.company }}</span>
                <span class="divider">|</span>
                <span class="comp-scale">{{ job.scale || '大厂' }}</span>
              </div>
              <div class="tag-row">
                <el-tag v-for="tag in job.tags" :key="tag" size="small" type="info" effect="plain" class="mini-tag">
                  {{ tag }}
                </el-tag>
              </div>
            </div>
            <div class="card-footer">
              <span class="time-stamp">{{ job.time || '1 小时前发布' }}</span>
              <span class="match-badge">职途无限</span>
            </div>
          </div>

          <div class="scroll-status">
            <p v-if="loading" class="loading-text"><el-icon class="is-loading"><Loading /></el-icon> 智能加载中...</p>
            <p v-if="noMore" class="no-more-text">没有更多职位了，已加载全部</p>
          </div>
        </div>
      </section>

      <aside :class="['preview-panel', { 'is-solid': hoveredJob }]">
        <div v-if="!hoveredJob" class="preview-default">
          <el-icon class="guide-icon"><Pointer /></el-icon>
          <p>悬停查看职位画像预览<br/>点击进入详细页面</p>
        </div>
        <div v-else class="preview-active">
          <div class="preview-header">
            <div class="logo-placeholder">{{ hoveredJob.company.charAt(0) }}</div>
            <div class="title-info">
              <h3>{{ hoveredJob.title }}</h3>
              <p class="company-name">{{ hoveredJob.company }}</p>
            </div>
          </div>
          <div class="highlight-box">
            <div class="h-item">
              <span class="label">薪资</span>
              <span class="val orange">{{ hoveredJob.salary }}</span>
            </div>
            <div class="h-item"><span class="label">地点</span><span class="val">{{ hoveredJob.city || '北京' }}</span></div>
          </div>
          <div class="preview-section">
            <h4 class="section-title">职位描述摘要</h4>
            <div class="desc-text">{{ hoveredJob.description || '核心业务系统开发...' }}</div>
          </div>
          <div class="click-tip">点击卡片查看深度画像</div>
        </div>
      </aside>
    </main>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" center>
      <div class="filter-dialog-content">
        <el-checkbox-group v-model="selectedOptions">
          <el-checkbox v-for="option in filterOptions[activeFilterType]" :key="option.value" :label="option.value" border>
            {{ option.label }}
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false" round>取消</el-button>
        <el-button type="primary" @click="confirmSelection" round>确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, ArrowDown, Pointer, Loading } from '@element-plus/icons-vue'
import { jobsApi } from '@/api/jobs'

const router = useRouter()
const searchQuery = ref('')
const activeFilterType = ref(null)
const dialogVisible = ref(false)
const selectedOptions = ref([])
const selectedTags = ref([])
const hoveredJob = ref(null)
const allJobs = ref([])
const currentPage = ref(1)
let searchTimer = null

const loadJobs = async (reset = true) => {
  try {
    const params = {}
    selectedTags.value.forEach((tag) => {
      if (tag.type === 'industry' || tag.type === 'city') {
        params[tag.type] = tag.value
      }
    })

    let data
    if (searchQuery.value) {
      // Use list endpoint with keyword — supports RAG search + industry/city filters
      const resp = await jobsApi.list({ ...params, keyword: searchQuery.value, page: 1, page_size: 200 })
      data = resp.data
    } else {
      const resp = await jobsApi.list({ ...params, page: currentPage.value, page_size: 200 })
      data = resp.data
    }

    const mapped = (data.jobs || []).map((item, index) => ({
      ...item,
      id: item.id || index + 1,
      title: item.job_title || item.title,
      company: item.company_name || item.company,
      salary: item.salary_range || item.salary || '面议',
      scale: item.company_scale || '--',
      city: item.city || '--',
      tags: item.industry ? item.industry.split(',') : [],
      description: item.job_description || item.description,
    }))

    if (reset) {
      allJobs.value = mapped
    } else {
      allJobs.value = [...allJobs.value, ...mapped]
    }
  } catch {
    if (reset) allJobs.value = []
  }
}

onMounted(() => {
  loadJobs()
})

// --- Infinite scroll ---
const loading = ref(false)
const count = ref(20)
const step = 20

const salaryFilteredJobs = computed(() => {
  const salaryTags = selectedTags.value.filter(t => t.type === 'salary')
  if (salaryTags.length === 0) return allJobs.value
  return allJobs.value.filter(job => {
    return salaryTags.some(tag => salaryInRange(job.salary, tag.value))
  })
})

const filteredJobs = computed(() => {
  return salaryFilteredJobs.value
})

const displayedJobs = computed(() => {
  return filteredJobs.value.slice(0, count.value)
})

const noMore = computed(() => count.value >= filteredJobs.value.length)
const disabled = computed(() => loading.value || noMore.value)

const loadMore = () => {
  if (disabled.value) return
  loading.value = true
  setTimeout(() => {
    count.value += step
    loading.value = false
  }, 300)
}

const handleSearch = () => {
  count.value = 20
  currentPage.value = 1
  loadJobs()
}

const debounceSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    count.value = 20
    currentPage.value = 1
    loadJobs()
  }, 300)
}

// --- Filter functions ---
const openFilterDialog = (type) => {
  activeFilterType.value = type
  selectedOptions.value = []
  dialogVisible.value = true
}

const confirmSelection = () => {
  if (selectedOptions.value.length === 0) {
    dialogVisible.value = false
    return
  }
  const options = filterOptions[activeFilterType.value]
  const newTags = selectedOptions.value.map(val => ({
    type: activeFilterType.value,
    value: val,
    label: options.find(o => o.value === val)?.label || val
  }))

  // For industry/city: replace existing tags of same type (single select)
  if (activeFilterType.value === 'industry' || activeFilterType.value === 'city') {
    selectedTags.value = selectedTags.value.filter(t => t.type !== activeFilterType.value)
  }
  selectedTags.value.push(...newTags)
  count.value = 20
  currentPage.value = 1
  dialogVisible.value = false
  // Reload from backend when industry or city changes
  if (activeFilterType.value === 'industry' || activeFilterType.value === 'city') {
    loadJobs()
  }
}

const removeTag = (tag) => {
  selectedTags.value = selectedTags.value.filter(t => t !== tag)
  currentPage.value = 1
  count.value = 20
  if (tag.type === 'industry' || tag.type === 'city') {
    loadJobs()
  }
}

const goToJobDetail = (id) => {
  router.push({ name: 'JobDetail', params: { id } })
}

function parseSalaryRange(salaryStr) {
  if (!salaryStr) return { min: 0, max: 0 }
  const cleaned = salaryStr.replace(/,/g, '')
  // Match patterns like "6k-8k", "10k-15k", "60k以上", "0k以下", "面议"
  const rangeMatch = cleaned.match(/([\d.]+)k?\s*[-~至到]\s*([\d.]+)k?/)
  if (rangeMatch) {
    return { min: parseFloat(rangeMatch[1]), max: parseFloat(rangeMatch[2]) }
  }
  const aboveMatch = cleaned.match(/([\d.]+)k?\s*以上/)
  if (aboveMatch) {
    return { min: parseFloat(aboveMatch[1]), max: Infinity }
  }
  const belowMatch = cleaned.match(/([\d.]+)k?\s*以下/)
  if (belowMatch) {
    return { min: 0, max: parseFloat(belowMatch[1]) }
  }
  const singleMatch = cleaned.match(/([\d.]+)k?/)
  if (singleMatch) {
    const v = parseFloat(singleMatch[1])
    return { min: v, max: v }
  }
  return { min: 0, max: 0 }
}

function salaryInRange(salaryStr, rangeValue) {
  if (!salaryStr || rangeValue === '0') return true
  const job = parseSalaryRange(salaryStr)
  if (job.min === 0 && job.max === 0) return true

  if (rangeValue.endsWith('+')) {
    const filterMin = parseInt(rangeValue)
    return job.max >= filterMin
  }
  const parts = rangeValue.split('-')
  if (parts.length !== 2) return true
  const filterMin = parseInt(parts[0].replace('k', ''))
  const filterMax = parseInt(parts[1].replace('k', ''))
  if (isNaN(filterMin) || isNaN(filterMax)) return true
  // Range overlap: job's range intersects with filter range
  return job.min <= filterMax && job.max >= filterMin
}

const filterCategories = [
  { type: 'industry', label: '行业' },
  { type: 'salary', label: '薪资' },
  { type: 'city', label: '城市' }
]

const filterOptions = {
  industry: [
    { value: '计算机软件', label: '计算机软件' },
    { value: 'IT服务', label: 'IT服务' },
    { value: '互联网', label: '互联网' },
    { value: '人工智能', label: '人工智能' },
    { value: '电子/半导体/集成电路', label: '电子/半导体' },
    { value: '通信/网络设备', label: '通信/网络' },
    { value: '仪器仪表制造', label: '仪器仪表' },
    { value: '计算机硬件', label: '计算机硬件' },
    { value: '学术/科研', label: '学术/科研' },
    { value: '电子设备制造', label: '电子设备制造' },
    { value: '企业服务', label: '企业服务' },
    { value: '工业自动化', label: '工业自动化' },
    { value: '医药制造', label: '医药制造' },
    { value: '物联网', label: '物联网' },
    { value: '新媒体', label: '新媒体' },
    { value: '咨询服务', label: '咨询服务' },
    { value: '生物工程', label: '生物工程' },
    { value: '专业技术服务', label: '专业技术服务' }
  ],

  salary: [
    { value: '0', label: '不限' },
    { value: '0-5k', label: '5k以下' },
    { value: '5k-10k', label: '5k-10k' },
    { value: '10k-15k', label: '10k-15k' },
    { value: '15k-25k', label: '15k-25k' },
    { value: '25k-40k', label: '25k-40k' },
    { value: '40k-60k', label: '40k-60k' },
    { value: '60k+', label: '60k以上' }
  ],

  city: [
    { value: '北京', label: '北京' },
    { value: '深圳', label: '深圳' },
    { value: '上海', label: '上海' },
    { value: '广州', label: '广州' },
    { value: '南京', label: '南京' },
    { value: '成都', label: '成都' },
    { value: '杭州', label: '杭州' },
    { value: '武汉', label: '武汉' },
    { value: '郑州', label: '郑州' },
    { value: '苏州', label: '苏州' },
    { value: '西安', label: '西安' },
    { value: '重庆', label: '重庆' },
    { value: '长沙', label: '长沙' },
    { value: '济南', label: '济南' },
    { value: '沈阳', label: '沈阳' },
    { value: '合肥', label: '合肥' },
    { value: '天津', label: '天津' },
    { value: '青岛', label: '青岛' }
  ]
}
</script>

<style scoped lang="scss">

/* ========================================================== */
/* ✨ 筛选弹窗重构：极简 AI 雾面质感 */
/* ========================================================== */

/* 1. 修改弹窗主体 */
/* ========================================================== */
/* ✨ 幻彩雾面：低饱和度彩色浮层 */
/* ========================================================== */

:deep(.el-dialog) {
  border-radius: 24px !important;
  /* 1. 🌟 核心修改：将纯白背景改为低饱和度的淡蓝色，增加色彩倾向 */
  background: #f0f7ff !important; 
  /* 2. 🌟 核心修改：增加一层极薄的毛玻璃，透出后面的渐变底色 */
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  /* 3. 🌟 核心修改：使用带蓝色的彩色阴影，让它“漂浮”在背景上 */
  box-shadow: 0 20px 60px rgba(64, 158, 255, 0.12) !important; 
  border: 1px solid rgba(255, 255, 255, 0.6) !important;
  transition: all 0.3s ease;

  .el-dialog__header {
    padding: 25px 30px 5px;
    text-align: left;
    .el-dialog__title {
      font-size: 19px;
      color: #303133;
      font-weight: bold;
      letter-spacing: 0.5px;
    }
  }

  .filter-dialog-content {
    padding: 20px 25px; // 增加内边距，让内容呼吸感更好
    
    .el-checkbox-group {
      display: grid;
      /* 🌟 核心修改：每行固定 3 列，并自动填充宽度 */
      grid-template-columns: repeat(3, 1fr); 
      gap: 12px;
      justify-items: stretch;
    }

    :deep(.el-checkbox) {
      margin-right: 0;
      height: 44px; // 固定高度，视觉更统一
      padding: 0 !important; // 取消原本的 padding
      border-radius: 12px !important;
      background: rgba(255, 255, 255, 0.7) !important;
      border: 1px solid rgba(255, 255, 255, 0.9) !important;
      transition: all 0.25s ease;
      
      display: flex;
      align-items: center;
      justify-content: center; /* 文字居中 */

      /* 隐藏原本的小方框 */
      .el-checkbox__input { display: none; }
      
      .el-checkbox__label { 
        padding-left: 0; 
        color: #606266; 
        font-size: 14px;
        text-align: center;
        width: 100%;
      }

      /* 选中态：由生硬的深蓝改为更有质感的浅蓝渐变 */
      &.is-checked {
        background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%) !important;
        border-color: transparent !important;
        box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
        .el-checkbox__label { 
          color: #fff !important; 
          font-weight: 600; 
        }
      }

      &:hover:not(.is-checked) {
        background: #ffffff !important;
        transform: translateY(-2px);
        border-color: #409eff !important;
        box-shadow: 0 4px 10px rgba(64, 158, 255, 0.1);
      }
    }
  }

  /* 适配小屏幕：如果选项太窄，自动改为 2 列 */
  @media (max-width: 500px) {
    .filter-dialog-content .el-checkbox-group {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  /* 底部按钮区域微调 */
  .el-dialog__footer {
    padding: 15px 30px 25px;
    background: rgba(255, 255, 255, 0.2); /* 底部微亮 */
    border-top: 1px solid rgba(255, 255, 255, 0.4);
    
    .el-button {
      height: 40px;
      border-radius: 12px;
      font-weight: bold;
      transition: all 0.3s ease;
      
      &.el-button--primary {
        /* 使用你搜索按钮的渐变色 */
        background: linear-gradient(135deg, #77b1f8 0%, #8c97f6 100%) !important;
        border: none !important;
        box-shadow: 0 6px 15px rgba(140, 151, 246, 0.3);
        &:hover { opacity: 0.9; transform: scale(1.02); }
      }
      
      &:not(.el-button--primary) {
        background: transparent;
        border: 1px solid rgba(0, 0, 0, 0.1);
        color: #909399;
        &:hover { background: rgba(255, 255, 255, 0.4); }
      }
    }
  }
}

.job-explorer {
  padding: 30px 60px;
  width: 100%;
  height: calc(100vh - 60px);
  
  /* 🌟 核心修改：增加色彩饱和度，从左上角的深冰蓝色向右下角的纯白过渡 */
  background: 
    radial-gradient(at 0% 0%, #d4e4ff 0%, transparent 40%),
  radial-gradient(at 50% 50%, #fadbbdd1 0%, transparent 80%),
  radial-gradient(at 100% 100%, #a0ece778 0%, transparent 40%),
  #fcfdfe;
    
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* --- 1. 顶部搜索区：精致简约 --- */
.search-header {
  margin-bottom: 30px;
  flex-shrink: 0;

  .search-container {
    display: flex;
    justify-content: center;
    gap: 15px;
    margin-bottom: 20px;
    .custom-search {
      width: 800px;
      transition: all 0.3s ease;
  
  :deep(.el-input__wrapper) {
    transition: all 0.3s ease;
    border-radius: 24px;
  }

  /* 🌟 当搜索框被聚焦时，增加一个宽阔的蓝色光晕 */
  &.is-focus :deep(.el-input__wrapper),
  :deep(.el-input__wrapper):hover {
    box-shadow: 0 0 20px rgba(64, 158, 255, 0.15) !important;
    border-color: rgba(64, 158, 255, 0.4) !important;
  }
}
    .search-btn {
  /* 🌟 修改点：使用渐变色，视觉更丝滑 */
  border-radius: 24px;
  background: linear-gradient(135deg, #77b1f8 0%, #8c97f6 100%) !important;
  border: none !important;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3) !important;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 6px 16px rgba(64, 158, 255, 0.45) !important;
    transform: translateY(-1px);
  }
}
  }
  .filter-categories {
    display: flex;
    justify-content: center;
    gap: 25px;
    .category-item {
      cursor: pointer; font-size: 14px; color: #606266; display: flex; align-items: center; gap: 4px;
      &:hover { color: #409EFF; }
    }
  }
  .tag-container { display: flex; justify-content: center; gap: 8px; margin-top: 15px; }
}

/* --- 2. 主体分栏布局：大圆角与呼吸感 --- */
.main-content {
  display: flex;
  flex: 1;
  gap: 30px; /* gap 增加，增加呼吸感 */
  overflow: hidden; /* 保证布局不塌陷 */
}

/* --- 左侧职位列表面板 --- */
.job-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.6) !important; /* 🌟 核心点：降低透明度到 0.6，呼应中间卡片风格 */
  backdrop-filter: blur(20px); /* 🎨 保留模糊背景：毛玻璃模糊效果 */
  border-radius: 20px; /* 🎨 调大圆角：更润、更高级 */
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.03); /* 🎨 超淡灰蓝阴影：增加悬浮感 */
  border: 1px solid rgba(255, 255, 255, 0.5); /* 白色描边：调淡，营造玻璃边缘感 */
}

.job-card-container {
  flex: 1;
  overflow-y: auto; /* 重点：滚动条在这里 */
  padding-right: 10px;
  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb { background: #eee; border-radius: 10px; }
}

/* --- C. 🌟 核心美化：自定义精致 JobCard 样式 --- */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.elegant-job-card {
  background: #fff;
  border-radius: 16px; /* 🎨 调大圆角：更润、更现代 */
  padding: 24px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  border: 1px solid rgba(255, 255, 255, 0.7) !important; /* 白色边框 */
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.03), 
    inset 0 0 12px rgba(255, 255, 255, 0.5) !important; /* 关键：内发光 */
  /* 🌟 核心交互反馈：重力反馈感美化 (Hover) */
  &:hover, &.is-active {
    transform: translateY(-5px); /* 🎨 向上浮起，更有灵性 */
    box-shadow: 
      0 20px 40px rgba(64, 158, 255, 0.1), 
      0 0 0 2px rgba(64, 158, 255, 0.05) !important; /* 悬停时的呼吸圈 */
    border-color: rgba(64, 158, 255, 0.2); /* 🌟 悬停时增加蓝色发光描边 */
  }

  .title-row {
    display: flex; justify-content: space-between; margin-bottom: 8px;
    .job-name { font-size: 18px; font-weight: bold; color: #303133; }
    /* 🌟 匹配度色彩心理：使用珊瑚橙引导 */
    .job-salary { font-size: 17px; font-weight: bold; color: #f77c38; /* 珊瑚橙 */ }
  }

  .company-row { font-size: 14px; color: #909399; margin-bottom: 12px; .divider { margin: 0 8px; color: #eee; } }
  
  /* 🌟 标签精致化：药丸样式微胶囊 */
  .tag-row { display: flex; gap: 8px; margin-bottom: 15px; .mini-tag { font-size: 11px; padding: 2px 8px; background: #fdf6ec; color: #e6a23c; border-radius: 4px; } }
  
  .card-footer { display: flex; justify-content: space-between; font-size: 12px; color: #abb2bb; .match-badge { color: #67C23A; font-weight: bold; } }
  animation: fadeInUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

/* 只针对前 6 个（首屏渲染）设置延迟，后续滚动加载的保持一致 */
.elegant-job-card:nth-child(1) { animation-delay: 0.05s; }
.elegant-job-card:nth-child(2) { animation-delay: 0.1s; }
.elegant-job-card:nth-child(3) { animation-delay: 0.15s; }
.elegant-job-card:nth-child(4) { animation-delay: 0.2s; }
.elegant-job-card:nth-child(5) { animation-delay: 0.25s; }
.elegant-job-card:nth-child(6) { animation-delay: 0.3s; }

/* 替换原本 .match-badge 或直接添加 */
.match-badge {
  background: rgba(103, 194, 58, 0.08); /* 极淡的 AI 绿 */
  color: #67C23A !important;
  padding: 4px 12px;
  border-radius: 8px;
  font-weight: bold;
  font-size: 12px;
  border: 1px solid rgba(103, 194, 58, 0.2);
  display: flex;
  align-items: center;
  gap: 5px;
  
  /* 前置一个小圆点，增加科技感 */
  &::before {
    content: '';
    width: 6px;
    height: 6px;
    background: #67C23A;
    border-radius: 50%;
    box-shadow: 0 0 6px #67C23A; /* 呼吸灯效果 */
  }
}

/* --- D. 右侧预览面板（重点美化） --- */
.preview-panel {
  width: 400px;
  border-radius: 24px;
  padding: 30px;
  display: flex;
  flex-direction: column;
  
  /* 🌟 核心：添加过渡动画 */
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1); 
  
  /* 1. 默认状态：半透明毛玻璃 */
  background: rgba(255, 255, 255, 0.45) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5) !important;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.03);

  /* 2. 🌟 内容显示状态：颜色变实 */
  &.is-solid {
    background: rgba(255, 255, 255, 1) !important; /* 变为纯白不透明 */
    backdrop-filter: blur(0px); /* 变实后不需要模糊了 */
    border: 1px solid rgba(64, 158, 255, 0.1) !important; /* 边缘微微发蓝 */
    box-shadow: 0 25px 50px rgba(64, 158, 255, 0.08); /* 投影更有呼吸感 */
  }
}

/* 预览内容展示时的渐显动画 */
.preview-active {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.preview-default {
  height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; color: #909399;
  .guide-icon {
    font-size: 56px;
    color: #409EFF;
    margin-bottom: 20px;
    opacity: 0.4; /* 图标也调透明，显得更轻盈 */
  }
  
  p {
    line-height: 1.8;
    font-size: 15px;
    letter-spacing: 0.5px;
  }
}

.preview-active {
  .preview-header {
    display: flex; gap: 15px; align-items: center; margin-bottom: 25px;
    /* 公司 Logo 圆角矩形占位 */
.logo-placeholder {
  width: 64px;
  height: 64px;
  /* 使用带有深度的蓝色渐变 */
  background: linear-gradient(135deg, #409EFF 0%, #2a7cdb 100%) !important;
  color: #ffffff;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: bold;
  /* 增加一个外侧的浅蓝发光层 */
  box-shadow: 0 8px 16px rgba(64, 158, 255, 0.2);
}
  }
  
  /* 信息层级视觉重组：网格化统计区域 */
  .highlight-box {
    display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; padding: 15px; background: #f9fbff; border-radius: 12px;
    .label { font-size: 12px; color: #909399; display: block; margin-bottom: 4px; }
    .val { font-size: 16px; font-weight: bold; color: #303133; &.orange { color: #f77c38; } }
  }

  /* 呼吸感排版 */
  .section-title { font-size: 16px; font-weight: bold; margin-bottom: 15px; padding-left: 10px; border-left: 4px solid #409EFF; }
  .desc-text { font-size: 14px; color: #606266; line-height: 1.8; white-space: pre-wrap; /* 保留换行符 */ }
  .click-tip { margin-top: auto; text-align: center; color: #409EFF; padding-top: 20px; font-weight: bold; }
}
</style>