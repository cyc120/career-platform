<template>
  <div class="job-detail">
    <!-- 顶部导航栏 -->
    <header class="header">
  <div class="header-left">
    <el-button class="back-btn" @click="goBack" link>
      <el-icon><ArrowLeft /></el-icon>
      <span>返回看板</span>
    </el-button>
  </div>
  
  <h1 class="page-title">岗位详情画像</h1>
  
  <div class="actions">
    <el-button @click="toggleFavorite" link>
      <el-icon :class="{ 'filled': isFavorited }">
        <StarFilled v-if="isFavorited" />
        <Star v-else />
      </el-icon>
    </el-button>
  </div>
</header>

    <!-- 主体内容区 -->
    <main class="main-content">
      <!-- 岗位基本信息 -->
      <el-card class="card">
        <div class="job-header">
          <h2>{{ job?.title || '加载中...' }}</h2>
          <div class="job-meta">
            <span>{{ job?.company }}</span>
            <span class="divider">|</span>
            <span>{{ job?.city }}</span>
            <span class="divider">|</span>
            <span class="salary">{{ job?.salary }}</span>
          </div>
        </div>
      </el-card>

      <el-card class="card intro-card"> <template #header>
          <span>岗位介绍</span>
        </template>
        
        <div v-if="loading" class="skeleton">
          <el-skeleton :rows="6" animated />
        </div>
        <div v-else-if="!job" class="empty-state">
          <el-empty description="未找到该职位">
            <el-button type="primary" @click="goBack">返回列表</el-button>
          </el-empty>
        </div>
        <div v-else class="description">
          <!-- 岗位详情（结构化展示） -->
          <div v-if="job.jobDetails" class="job-details-section">
            <template v-for="(block, bi) in parseJobDetails(job.jobDetails)" :key="bi">
              <div class="detail-block">
                <h4 class="block-title">
                  <span class="block-dot"></span>{{ block.title }}
                </h4>
                <ul class="block-list">
                  <li v-for="(item, ii) in block.items" :key="ii">{{ item }}</li>
                </ul>
              </div>
            </template>
          </div>
          <div v-else>
            <p>{{ formatDescription(job.description) || '暂无详细描述' }}</p>
          </div>
          <!-- 公司介绍 -->
          <div v-if="job.companyDescription" class="company-desc-section">
            <h4 class="section-subtitle">
              <el-icon><OfficeBuilding /></el-icon> 公司介绍
            </h4>
            <div class="company-desc-content">{{ job.companyDescription }}</div>
          </div>
          <img src="@/assets/3D programmer.png" class="card-decoration" />
        </div>
      </el-card>

      <!-- 岗位要求画像 -->
      <el-card class="card">
        <template #header>
          <span>岗位要求画像</span>
        </template>
        <JobKnowledgeGraph :job-title="job?.title" :key="job?.title" />
      </el-card>

      <el-card class="card promotion-card">
        <template #header>
          <div class="card-header">
            <el-icon><TrendCharts /></el-icon>
            <span>岗位换岗晋升图</span>
          </div>
        </template>
        
        <PromotionGraph :jobTitle="job?.title" />
      </el-card>

    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Star, StarFilled, OfficeBuilding } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { jobsApi } from '@/api/jobs'
import { favoritesApi } from '@/api/favorites'
import PromotionGraph from '@/components/PromotionGraph.vue'
import JobKnowledgeGraph from '@/components/JobKnowledgeGraph.vue'

const loading = ref(true)
const job = ref(null)
const router = useRouter()
const route = useRoute()
const isFavorited = ref(false)
const jobId = computed(() => route.params.id)

onMounted(async () => {
  const targetId = parseInt(route.params.id)
  try {
    const { data } = await jobsApi.detail(targetId)
    if (data.job) {
      const item = data.job
      job.value = {
        id: item.id,
        title: item.job_title || item.title,
        company: item.company_name || item.company,
        salary: item.salary_range || item.salary || '面议',
        city: item.city || item.location || '--',
        description: item.job_description || item.description || '暂无描述',
        companyDescription: item.company_description || '',
        jobDetails: item.job_details || '',
      }
    }
  } catch {
    // Job not found — keep null
  }

  try {
    const { data: favData } = await favoritesApi.list()
    const favIds = (favData.favorites || []).map((f) => f.job_id)
    isFavorited.value = favIds.includes(targetId)
  } catch {
    // ignore
  }

  loading.value = false
})

const goBack = () => router.back()

const formatDescription = (desc) => {
  if (!desc) return ''
  return desc.replace(/；/g, '\n').replace(/\\n/g, '\n')
}

const parseJobDetails = (text) => {
  if (!text) return []
  const blocks = []
  let currentBlock = null
  const lines = text.split('\n')
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue
    // 匹配大标题行，如 "1. 岗位职责" "2. 任职要求"
    const titleMatch = trimmed.match(/^[1-9]\d*[\.\、]\s*(.+)/)
    if (titleMatch) {
      currentBlock = { title: titleMatch[1], items: [] }
      blocks.push(currentBlock)
      continue
    }
    // 匹配子项，如 "1) xxx" "2) xxx" "- xxx" "• xxx" 或纯文本行
    const itemMatch = trimmed.match(/^(?:\d+[\)\.、]|[•\-–—]\s*)\s*(.+)/)
    if (itemMatch) {
      if (!currentBlock) {
        currentBlock = { title: '详情', items: [] }
        blocks.push(currentBlock)
      }
      currentBlock.items.push(itemMatch[1])
    } else if (currentBlock && !trimmed.match(/^[1-9]\d*[\.\、]/)) {
      // 普通文本行归入当前块
      currentBlock.items.push(trimmed)
    }
  }
  return blocks
}

const toggleFavorite = async () => {
  if (!job.value) return
  const id = parseInt(jobId.value)
  try {
    if (isFavorited.value) {
      await favoritesApi.remove(id)
      isFavorited.value = false
      ElMessage.success('已取消收藏')
    } else {
      await favoritesApi.add(id)
      isFavorited.value = true
      ElMessage.success('已添加收藏')
    }
  } catch {
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped lang="scss">




/* --- 2. 布局：双栏呼吸感 --- */
.main-content {
  display: grid;
  grid-template-columns: 1fr 380px; /* 🌟 7:3 比例 */
  gap: 30px;
  max-width: 1400px;
  margin: 40px auto;
  padding: 0 60px;

  @media (max-width: 1100px) {
    grid-template-columns: 1fr;
    padding: 20px;
  }
}

/* --- 3. 核心卡片组件 (Glass Card) --- */
.glass-card {
  background: #ffffff;
  border-radius: 24px; /* 🌟 大圆角更亲和 */
  padding: 32px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.8);
  margin-bottom: 24px;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.06);
  }
}

/* --- 4. 岗位标题与薪资 --- */
.job-main-info {
  .title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 { font-size: 32px; font-weight: 800; color: #1a1a1a; margin: 0; }
    .salary { 
      font-size: 28px; 
      font-weight: 800; 
      color: #f77c38; /* 🌟 珊瑚橙，呼应你的匹配度颜色 */
    }
  }

  .job-tags {
    margin-bottom: 24px;
    .el-tag { margin-right: 10px; border: none; background: #f0f7ff; color: #409eff; }
  }

  .job-meta {
    font-size: 15px;
    color: #8899aa;
    display: flex;
    align-items: center;
    .company-name { font-weight: 700; color: #409eff; }
    .divider { width: 1px; height: 14px; background: #ddd; margin: 0 15px; }
  }
}

/* --- 5. 详情内容区 --- */
.section-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 24px;
  color: #334455;
  display: flex;
  align-items: center;
  &::before {
    content: ""; width: 4px; height: 20px; background: #409eff;
    border-radius: 2px; margin-right: 12px;
  }
}

.description-content {
  line-height: 2;
  color: #556677;
  font-size: 16px;
  white-space: pre-line;
}

/* --- 6. 右侧画像与按钮 --- */
.portrait-card {
  position: sticky;
  top: 100px; /* 随滚动悬浮 */
  background: linear-gradient(135deg, #ffffff 0%, #f9fcff 100%);

  .req-item {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    color: #556677;
    .check-icon { color: #67C23A; font-size: 18px; }
  }

  .apply-btn {
    width: 100%;
    height: 54px;
    border-radius: 16px;
    font-size: 18px;
    font-weight: 700;
    margin-top: 20px;
    background: linear-gradient(90deg, #409EFF, #66b1ff);
    box-shadow: 0 8px 20px rgba(64, 158, 255, 0.3);
    border: none;
    &:hover { transform: translateY(-2px); box-shadow: 0 12px 25px rgba(64, 158, 255, 0.4); }
  }
}

/* --- 统一后的根容器样式 --- */
.job-detail {
  min-height: 100vh;
  /* 不限制总高度，让内容自然撑开页面滚动 */
  background: linear-gradient(
    135deg,
    #faf9ed 0%,    /* 浅蓝灰 */
    #e8eef9 50%,   /* 淡紫色 */
    #f3e5f55a 100%   /* 浅藕荷色 */
  ) !important;
  background-attachment: fixed; /* 背景固定，滑动时更有质感 */
}

/* 顶部导航栏：增加阴影和内边距 */
/* --- 顶部导航栏彻底重构 --- */
.header {
  /* 1. 移除背景和边框，实现清爽感 */
  background: transparent !important; 
  border: none !important;
  
  /* 2. 布局调整 */
  height: 90px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  position: relative;
  z-index: 100;
}

/* 3. 岗位详情文字美化：字号加大 + 渐变质感 */
.header h1 {
  font-size: 32px; /* 💡 字号显著加大 */
  font-weight: 700;
  letter-spacing: 3px;
  margin: 0;
  /* 科技感渐变色 */
  background: linear-gradient(135deg, #d49bb3 0%, #366da4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 4. 返回按钮美化 */
.back-btn {
  font-size: 17px;
  color: #606266 !important;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
  
  &:hover {
    color: #11365c !important;
    transform: translateX(-5px); /* 悬停微动，更有灵动感 */
  }
}

/* 5. 五角星收藏图标美化 */
/* --- 五角星收藏图标美化 --- */
.actions .el-button {
  font-size: 28px;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  padding: 0;
  border: none;

  &:hover {
    transform: scale(1.2) rotate(10deg);
  }

  /* 💡 使用 :deep 穿透组件，确保能抓到图标内部的颜色 */
  :deep(.el-icon) {
    color: #909399; /* 默认灰色 */
    transition: all 0.3s ease;

    /* 当 class 包含 filled 时（注意这里去掉了前面的空格，表示同级匹配） */
    &.filled {
      color: #FFD700 !important; 
      filter: drop-shadow(0 0 8px rgba(255, 215, 0, 0.6)) !important;
    }
    
    /* 针对 SVG 内部路径强制染色 */
    &.filled svg {
      fill: #FFD700 !important;
    }
  }
}
/* --- 2. 主体内容区：取消高度限制，让内容自然撑开 --- */
.main-content {
  padding: 0px 30px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  box-sizing: border-box;
  margin-top: 3px;
  /* 关键：不设 flex:1，让所有卡片按内容高度完整展开，页面整体滚动 */
}

/* --- 统一卡片基础美化 --- */
.card {
  /* 1. 变“重”为“轻”：使用半透明背景 */
  background: rgba(255, 255, 255, 0.65) !important;
  /* 2. 毛玻璃效果：让底部的三色渐变透上来 */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  
  /* 3. 边框微调：使用极细的浅色边框，模拟玻璃边缘 */
  border: 1px solid rgba(255, 255, 255, 0.5) !important;
  border-radius: 20px !important; /* 💡 更大的圆角看起来更现代 */
  
  /* 4. 阴影优化：使用柔和的浅蓝色扩散阴影 */
  box-shadow: 0 10px 30px rgba(100, 120, 150, 0.08) !important;
  
  margin-bottom: 0; /* 间距由 main-content 的 gap 控制 */
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  overflow: visible; /* 允许内部装饰溢出 */
}

/* 5. 鼠标悬停动效：产生轻微浮起感 */
.card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.8) !important;
  box-shadow: 0 15px 40px rgba(64, 158, 255, 0.12) !important;
}

/* --- 6. 强化卡片头部标题 --- */
:deep(.el-card__header) {
  border-bottom: 1px solid rgba(64, 158, 255, 0.1) !important;
  padding: 18px 25px !important;
  
  span {
    font-size: 18px;
    font-weight: 600;
    color: #2c3e50;
    position: relative;
    padding-left: 12px;
    
    /* 标题左侧的彩色装饰短线 */
    &::before {
      content: "";
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 4px;
      height: 16px;
      background: linear-gradient(to bottom, #409EFF, #7fb8ee);
      border-radius: 10px;
    }
  }
}

/* --- 7. 岗位介绍内容的间距微调 --- */
:deep(.el-card__body) {
  padding: 25px !important;
}

.job-header h2 {
  font-size: 26px;
  color: #1a1a1a;
  margin-bottom: 12px;
}

.job-meta {
  display: flex;
  align-items: center;
  gap: 15px;
  color: #606266;
  
  .salary {
    font-size: 20px;
    color: #fc8484; /* 醒目的薪资颜色 */
    font-weight: bold;
  }
}

/* 1. 岗位介绍卡片：完整展示，不裁剪内容 */
.intro-card {
  position: relative;
  overflow: visible !important;
  min-height: auto;
  :deep(.el-card__body) {
    height: auto !important;
    max-height: none !important;
    overflow: visible !important;
    padding: 25px 30px !important;
  }
}

/* 2. 岗位介绍文字：完整显示，自动换行 */
.description {
  position: relative;
  z-index: 2;
  padding-right: 40px;
  font-size: 15px;
  line-height: 2;
  color: #444;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: break-word;
  p {
    white-space: pre-wrap;
    margin: 0;
  }
}

.job-details-section {
  margin-bottom: 20px;
}

.detail-block {
  margin-bottom: 20px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.04) 0%, rgba(103, 194, 58, 0.04) 100%);
  border-radius: 12px;
  border: 1px solid rgba(64, 158, 255, 0.1);
}

.block-title {
  font-size: 16px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.block-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409EFF, #67C23A);
  flex-shrink: 0;
}

.block-list {
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    padding: 6px 0;
    padding-left: 18px;
    position: relative;
    font-size: 14px;
    color: #556677;
    line-height: 1.8;

    &::before {
      content: "▸";
      position: absolute;
      left: 0;
      color: #409EFF;
      font-size: 12px;
    }
  }
}

.company-desc-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.9;
  white-space: pre-wrap;
  word-break: break-word;
}

.company-desc-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px dashed #e0e0e0;
}

.section-subtitle {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 0 0 10px 0;
}

.details-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.9;
  color: #555;
}

/* 3. 图片的绝对定位样式 */
.card-decoration {
  position: absolute;
  top: -20px;    /* 稍微往上偏一点，更有设计感 */
  right: 30px;  /* 稍微往右偏一点 */
  width: 300px;  /* 根据你的图片大小调整 */
  height: auto;
  
  /* 💡 核心：透明度与混合模式 */
  opacity: 0.15;      /* 保持低透明度，作为背景点缀 */
  pointer-events: none; /* 鼠标可以穿透图片，不影响你选中文字 */
  z-index: 1;
  
  /* 💡 高级技巧：让图片左侧淡出，不干扰文字阅读 */
  -webkit-mask-image: linear-gradient(to left, rgba(0,0,0,1) 30%, rgba(0,0,0,0) 100%);
  mask-image: linear-gradient(to left, rgba(0,0,0,1) 30%, rgba(0,0,0,0) 100%);
  
  /* 增加一个丝滑的入场动画 */
  transition: all 0.5s ease;
}

/* 4. 交互：鼠标移入卡片时，图片稍微变亮或放大 */
.intro-card:hover .card-decoration {
  opacity: 0.25;
  transform: scale(1.05) rotate(-3deg);
}

/* --- 3. UI 细节增强：标题栏渐变与薪资 --- */
.job-main-card {
  /* 线性渐变背景，增加高级感 */
  background: linear-gradient(120deg, #ffffff 0%, #f0f7ff 100%);
  padding: 10px;
}

.job-header {
  .title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;

    h2 {
      font-size: 28px;
      margin: 0;
      color: #303133;
    }

    .salary {
      font-size: 26px;
      color: #F56C6C; /* 薪资高亮 */
      font-weight: bold;
    }
  }

  .job-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 15px;
    color: #606266;

    .divider {
      color: #dcdfe6;
      margin: 0 5px;
    }
    
    .company-tag {
      font-weight: 600;
      color: #409EFF;
    }
  }
}

/* --- 4. 卡片标题：增加蓝色左装饰条 --- */
:deep(.el-card__header) {
  padding: 15px 20px;
  border-bottom: 1px solid #f0f2f5;
  
  span {
    font-size: 18px;
    font-weight: bold;
    color: #303133;
    position: relative;
    padding-left: 15px;

    &::before {
      content: "";
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 4px;
      height: 18px;
      background: #8dc2f7; /* 蓝色装饰条 */
      border-radius: 2px;
    }
  }
}

/* --- 5. 列表样式：打钩图标与间距 --- */
.requirements ul {
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid #f5f7fa;
    color: #606266;
    font-size: 15px;

    /* 模拟打钩图标（如果没有引入图标组件，可以用伪元素实现） */
    &::before {
      content: "✓";
      color: #67C23A;
      font-weight: bold;
      font-size: 16px;
    }

    &:last-child {
      border-bottom: none;
    }
  }
}

.skeleton, .empty-state {
  padding: 40px;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .header {
    padding: 10px 15px;
  }
  
  .job-header .title-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .main-content {
    padding: 15px;
  }
}

/* --- 岗位换岗晋升图专属样式 --- */
.promotion-card :deep(.el-card__body) {
  padding: 20px;
  height: auto;
  overflow: visible; /* 允许内部画布正常测量高度 */
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-tag {
  border-radius: 10px;
  font-weight: 500;
}

.promotion-container {
  min-height: 400px;
  width: 100%;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  position: relative; /* 必须是 relative 保证 Canvas 定位正确 */
}

/* 确保 G6 生成的 canvas 样式正常 */
#promotion-graph-container canvas {
  display: block;
}

.graph-placeholder {
  width: 100%;
  height: 400px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .promotion-container {
    min-height: 300px;
  }
}


/* 兼容 Element Plus 卡片内部间距 */
:deep(.el-card__body) {
  padding: 15px;
}
</style>