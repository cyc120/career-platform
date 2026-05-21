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
          <p>{{ formatDescription(job.description) || '暂无详细描述' }}</p>
          <img src="@/assets/3D programmer.png" class="card-decoration" />
        </div>
      </el-card>

      <!-- 岗位要求画像 -->
      <el-card class="card">
        <template #header>
          <span>岗位要求画像</span>
        </template>
        <div class="graph-wrapper">
          <div ref="graphContainer" class="graph-canvas"></div>
          <el-button class="reset-btn" @click="resetView" circle icon="Refresh" />
        </div>
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
import { ref, computed, onMounted, nextTick, onBeforeUnmount, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Star, StarFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { jobsApi } from '@/api/jobs'
import { favoritesApi } from '@/api/favorites'
import ForceGraph from 'force-graph'
import neo4j from 'neo4j-driver'
import * as d3 from 'd3';
import * as G6 from '@antv/g6';
import PromotionGraph from '@/components/PromotionGraph.vue'
// --- 1. 引用和状态 ---
const graphContainer = ref(null)
let graphInstance = null

// --- 2. Neo4j 连接配置 ---
// 这里等同学发地址后，替换成 'bolt://xxx.cpolar.top:xxx'
const NEO4J_URL = 'bolt://localhost:7687' 
const driver = neo4j.driver(NEO4J_URL, neo4j.auth.basic('', ''))

const NODE_CONFIG = {
  Job: { color: '#6fb1fc', size: 10 },        // 中心岗位：蓝色，最大
  Skill: { color: '#f79767', size: 7 },      // 技能：橙色，中等
  Requirement: { color: '#57c7e3', size: 6 }, // 要求：青色
  Default: { color: '#d3d3d3', size: 5 }      // 其他：灰色
};

// --- 3. 初始化图谱函数 ---
const initGraph = async () => {

  // JobDetail.vue 约 160 行 initGraph 函数内
const LEVEL_COLORS = {
  1: '#FF8C00', // 第一级：深橙色，突出中心岗位
  2: '#E6E6FA', // 第二级：深天蓝色，与第一级有明显色差
};

// 第三级：随机彩色池（淡雅色系，保证文字清晰）
const THIRD_LEVEL_COLORS = ['#7fb8ee', '#76d7ea', '#8de3c0', '#b6e39a', '#f3d999', '#f7a8a8'];  if (!graphContainer.value || !job.value) return;

  const nameMap = {
    "软件测试": "软件测试工程师（专项方向）",
    "C/C++": "C++",
    "前端开发": "前端开发工程师",
    "Java": "Java开发工程师", 
    "硬件测试": "硬件测试工程师",
    "测试工程师": "测试工程师（软件方向）",
    // 你可以根据需要继续在这里添加剩下的岗位映射
  };

  // 2. 获取最终用于查询的字符串
  // 如果在 map 里找到了就用映射后的，没找到就直接用原标题
  const searchTitle = nameMap[job.value.title] || job.value.title;

  if (graphInstance) graphInstance._destructor();

  // 2. 初始化实例（不依赖外部 d3 变量）
graphInstance = ForceGraph()(graphContainer.value)
.backgroundColor('rgba(0,0,0,0)')
.nodeCanvasObject((node, ctx, globalScale) => {
  const label = node.name;
  
  // 💡 第一步：修正半径逻辑，手动覆盖 node.val
  let currentRadius;
  if (node.level === 1) {
    currentRadius = 24; // 显著放大核心球
  } else if (node.level === 2) {
    currentRadius = 18; // 中等放大分类球
  } else {
    // 第三层保留原有的 val 或者根据字数自适应
    currentRadius = node.val || 10; 
  }

  // 1. 绘制圆形背景
  ctx.beginPath();
// 💡 这里直接根据 level 判断，强制给 1、2 层大半径，其他用原来的 node.val
  ctx.arc(node.x, node.y, node.level == 1 ? 70 : (node.level === 2 ? 45 : node.val), 0, 2 * Math.PI, false);  
  // 为第一二层增加呼吸发光感（可选，增加突出度）
  if (node.level <= 2) {
    ctx.shadowColor = node.color;
    ctx.shadowBlur = 10 / globalScale;
  }
  
  ctx.fillStyle = node.color;
  ctx.fill();
  
  // 恢复阴影并画白边
  ctx.shadowBlur = 0;
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 1.5 / globalScale;
  ctx.stroke();

// 2. 文字配置 - 随球体大小动态调整字号
// 💡 修改点：第一层 18px (中心)，第二层 14px (分类)，第三层 11px (细分)
const fontSize = node.level === 1 ? 18 : (node.level === 2 ? 14 : 11);

// 保持粗细逻辑：第一二层加粗(600)，第三层正常(500)
ctx.font = `${node.level <= 2 ? '600' : '500'} ${fontSize}px Sans-Serif`;

ctx.textAlign = 'center';
ctx.textBaseline = 'middle';

// 💡 建议：中心球文字颜色设为白色，增强对比度
ctx.fillStyle = node.level === 1 ? '#ffffff' : '#001f3f';
  
  // 第一层核心球建议用白色字，对比更强烈
  ctx.fillStyle = node.level === 1 ? '#ffffff' : '#001f3f';

  // 3. 💡 智能换行逻辑 (偏移量改用动态的 fontSize)
  if (label.length > 6) { 
    const mid = Math.ceil(label.length / 2);
    const line1 = label.substring(0, mid);
    const line2 = label.substring(mid);
    
    // 这里的 0.6 是根据字号动态计算行高，保证在球体正中心
    ctx.fillText(line1, node.x, node.y - fontSize * 0.6);
    ctx.fillText(line2, node.x, node.y + fontSize * 0.6);
  } else {
    ctx.fillText(label, node.x, node.y);
  }
})
    .linkDirectionalArrowLength(3)
    .linkDirectionalArrowRelPos(1)
    // .linkColor(() => '#E4E7ED');
    .d3Force('charge', d3.forceManyBody().strength(-2500))  // 💡 减弱排斥力（从 -1000 改为 -300），让节点聚拢
    .d3Force('link', d3.forceLink().distance(d => 120 + d.source.val + d.target.val))
    .d3Force('collide', d3.forceCollide(node => node.val + 15)) // 💡 防止球体重叠
    .d3Force('center', d3.forceCenter(0, 0))             // 💡 增加中心引力，确保整体在原点附近
    .d3VelocityDecay(0.2)
    

  try {
    const session = driver.session();
    // 使用模糊匹配，增加查询范围
    const cypher = `
      MATCH (j:Job)-[r*1..2]-(m) 
      WHERE j.title = $jobTitle OR j.name CONTAINS $jobTitle
      RETURN j,r,m LIMIT 300
    `;
    const result = await session.run(cypher, { jobTitle: searchTitle });

    const nodes = [];
    const links = [];

    result.records.forEach(record => {
      ['j', 'm'].forEach(key => {
        const node = record.get(key);
        if (!node) return;

        const id = node.identity.toString();
        if (!nodes.find(n => n.id === id)) {
          const label = node.labels[0] || 'Default';
      const labelText = node.properties.title || node.properties.name || label;
      // 💡 判断是否为中心岗位
      const isCenterNode = (node.properties.title === job.value.title || node.properties.name === job.value.title);
      const config = NODE_CONFIG[label] || NODE_CONFIG.Default;

      // 💡 动态计算半径：保证球体能装下文字
      const charCount = labelText.length;
      const dynamicRadius = isCenterNode 
        ? Math.max(20, charCount * 5.5) 
        : Math.max(12, charCount * 4.5);

      // 💡 确定层级 (Level)
      let level = 3; 
      if (isCenterNode) {
        level = 1;
      } else if (node.labels.includes('Ability')) { 
        // 假设你的 Neo4j 中第二级节点带有 'Ability' 标签，如果没有，可以根据关系距离判断
        level = 2;
      }

      // 💡 分配颜色
      let finalColor;
      if (level === 1) {
        finalColor = LEVEL_COLORS[1];
      } else if (level === 2) {
        finalColor = LEVEL_COLORS[2];
      } else {
        // 第三层：根据 ID 取模随机分配彩色
        finalColor = THIRD_LEVEL_COLORS[parseInt(id) % THIRD_LEVEL_COLORS.length];
      }

      // ✅ 确保这里只有一个干净的 nodes.push，没有重复的 fx/fy
      nodes.push({
        id: id,
        name: labelText,
        color: finalColor,
        val: dynamicRadius, 
        level: level,
        fx: null,
        fy: null
          });
        }
      });

      // 解析关系连线（保持不变）
      const rel = record.get('r');
      if (rel) {
        if (Array.isArray(rel)) {
          rel.forEach(r => links.push({ source: r.start.toString(), target: r.end.toString() }));
        } else {
          links.push({ source: rel.start.toString(), target: rel.end.toString() });
        }
      }
    });

    if (nodes.length > 0) {
      graphInstance.graphData({ nodes, links });
      
      // 💡 视觉聚焦：在数据加载后强制相机对焦
      setTimeout(() => {
        graphInstance.centerAt(0, 0, 500); // 移动到原点
        graphInstance.zoom(0.5, 500);        // 放大到 3 倍，解决“太小”的问题
      }, 500);
    } else {
      console.warn("未查找到数据，查询词为:", job.value.title);
    }

    session.close();
  } catch (err) {
    console.error('Neo4j 连通或查询失败:', err);
  }
};

const loading = ref(true)
const job = ref(null)
const router = useRouter()
const route = useRoute()
const isFavorited = ref(false)
const jobId = computed(() => route.params.id)

// 在页面挂载后启动
onMounted(async () => {
  // Load job from API
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
      }
    }
  } catch {
    // Job not found — keep null
  }

  // Check favorite status
  try {
    const { data: favData } = await favoritesApi.list()
    const favIds = (favData.favorites || []).map((f) => f.job_id)
    isFavorited.value = favIds.includes(targetId)
  } catch {
    // ignore
  }

  loading.value = false

  await nextTick()
  initGraph()
})

// 返回上一页
const goBack = () => {
  router.back()
}

const formatDescription = (desc) => {
  if (!desc) return ''
  return desc.replace(/；/g, '\n').replace(/\\n/g, '\n')
}



// 2. 修改点击收藏的逻辑
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

// 1. 在脚本最顶部增加导入 (约第 34 行 import 区域)


// 2. 在 toggleFavorite 函数下方追加以下绘图逻辑
const graph = ref(null);
const currentJobTitle = ref('软件测试工程师（专项方向）'); // 这里可以根据 job.value.title 动态匹配



const promotionGraphInstance = ref(null);

const initPromotionGraph = () => {
  const container = document.getElementById('promotion-graph-container');
  if (!container || !job.value) return;

  // 1. 销毁旧实例，防止重复渲染
  if (promotionGraphInstance.value) {
    promotionGraphInstance.value.destroy();
    promotionGraphInstance.value = null;
  }

  // 2. 统一获取岗位名称
  const currentTitle = (job.value.job_title || job.value.title || "").trim();
  
  // 3. 过滤数据
  const filtered = promotionData.filter(item => 
    item.tech_type === currentTitle
  );

  // 调试：请在浏览器控制台查看这里是否有数据输出
  console.log('当前页面岗位:', currentTitle);
  console.log('匹配到的晋升路径数据:', filtered);

  if (filtered.length === 0) {
    console.warn(`未匹配到 "${currentTitle}" 的晋升数据，请检查 JSON 里的 tech_type`);
    return;
  }

  // 4. 处理节点坐标 (将 fx, fy 映射到 G6 的 x, y)
  const nodes = filtered.map(item => ({
    id: item.title,
    label: `${item.level}\n${item.title}`,
    // 使用相对坐标，配合下面的 fitView: true 自动居中
    x: item.fx, 
    y: item.fy, 
    type: 'modelRect',
    style: {
      fill: item.type === 'management' ? '#FDF6EC' : '#ffffff',
      stroke: item.type === 'management' ? '#E6A23C' : '#409EFF',
      lineWidth: 2,
      radius: 4,
    },
    labelCfg: {
      style: {
        fontSize: 10,
        fill: '#333'
      }
    }
  }));

  // 5. 生成连线 (根据 fy 排序连线)
  const edges = [];
  const sortedNodes = [...nodes].sort((a, b) => a.y - b.y);
  for (let i = 0; i < sortedNodes.length - 1; i++) {
    edges.push({
      source: sortedNodes[i].id,
      target: sortedNodes[i+1].id,
      style: { stroke: '#A2B1C3', endArrow: true }
    });
  }

  // 6. 初始化并渲染图谱
  promotionGraphInstance.value = new G6.Graph({
    container: 'promotion-graph-container',
    width: container.scrollWidth,
    height: 450,
    fitView: true, // 核心：自动缩放以适配 fy 很大的数值
    fitViewPadding: 30,
    modes: {
      default: ['drag-canvas', 'zoom-canvas', 'drag-node'],
    },
    defaultNode: {
      size: [120, 40],
    }
  });

  promotionGraphInstance.value.data({ nodes, edges });
  promotionGraphInstance.value.render();
};


onBeforeUnmount(() => {
  // 清理 Neo4j 实例
  if (graphInstance && typeof graphInstance._destructor === 'function') {
    graphInstance._destructor();
  }
  // 清理 G6 实例
  if (promotionGraphInstance.value) {
    promotionGraphInstance.value.destroy();
  }
});
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


.graph-wrapper {
  position: relative;
  width: 100%;
  height: 600px; /* 设定固定高度 */
  background: #fdfdfd;
  border-radius: 8px;
  border: 1px solid #f0f2f5;
  overflow: hidden;
}

.graph-canvas {
  width: 100%;
  height: 600px; /* 必须有明确高度，否则背景看不见 */
  /* 设置径向渐变，营造空间感 */
  background: radial-gradient(circle at center, #fefcce2d 0%, #e9f2fc99 100%) !important;
  position: relative;
  overflow: hidden;
}

/* 确保内部生成的 canvas 是透明的，否则会挡住上面的渐变 */
:deep(.graph-canvas canvas) {
  background-color: transparent !important;
}

.reset-btn {
  position: absolute;
  right: 15px;
  bottom: 15px;
  z-index: 10;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

/* 兼容 Element Plus 卡片内部间距 */
:deep(.el-card__body) {
  padding: 15px;
}
</style>