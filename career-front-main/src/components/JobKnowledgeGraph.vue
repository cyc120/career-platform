<template>
  <div class="job-knowledge-graph">
    <div v-if="error" class="graph-error">
      <el-icon :size="32"><WarningFilled /></el-icon>
      <span>{{ error }}</span>
    </div>
    <div v-show="!error" class="graph-wrapper">
      <div ref="graphContainer" class="graph-canvas"></div>
      <div v-if="loading" class="graph-loading-overlay">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <span>正在加载知识图谱...</span>
      </div>
      <el-button v-if="!loading" class="reset-btn" @click="resetView" circle>
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import ForceGraph from 'force-graph'
import * as d3 from 'd3'
import { Loading, WarningFilled, Refresh } from '@element-plus/icons-vue'
import { matchingApi } from '@/api/matching'

const props = defineProps({
  jobTitle: { type: String, default: '' },
})

const graphContainer = ref(null)
const loading = ref(false)
const error = ref('')
let graphInstance = null

const LEVEL_COLORS = {
  1: '#FF8C00',
  2: '#E6E6FA',
}
const THIRD_LEVEL_COLORS = ['#7fb8ee', '#76d7ea', '#8de3c0', '#b6e39a', '#f3d999', '#f7a8a8']

const initGraph = async () => {
  if (!graphContainer.value || !props.jobTitle) return

  loading.value = true
  error.value = ''

  try {
    const { data } = await matchingApi.getJobGraph(props.jobTitle)
    if (!data.success) {
      error.value = data.error || '未找到图谱数据'
      return
    }

    const graphData = data.data
    const centerTitle = graphData.center || props.jobTitle

    // 构建 force-graph 需要的数据格式
    // Neo4j 标签：岗位(中心)、能力维度(二级)、核心要求(三级)
    const nodeMap = {}
    const nodes = graphData.nodes.map((n) => {
      const isCenter = n.name === centerTitle || n.label === '岗位'
      const displayName = n.name.length > 20 ? n.name.substring(0, 18) + '...' : n.name
      const charCount = displayName.length
      const dynamicRadius = isCenter ? Math.max(20, charCount * 5.5) : Math.max(12, charCount * 4.5)

      let level = 3
      if (isCenter) level = 1
      else if (n.label === '能力维度') level = 2

      let color
      if (level === 1) color = LEVEL_COLORS[1]
      else if (level === 2) color = LEVEL_COLORS[2]
      else {
        // 用 id 的数字部分取模
        const numPart = n.id.replace(/\D/g, '') || '0'
        color = THIRD_LEVEL_COLORS[parseInt(numPart.slice(-4) || '0') % THIRD_LEVEL_COLORS.length]
      }

      const node = { id: n.id, name: displayName, fullName: n.name, color, val: dynamicRadius, level }
      nodeMap[n.id] = node
      return node
    })

    const links = graphData.links
      .filter((l) => nodeMap[l.source] && nodeMap[l.target])
      .map((l) => ({ source: l.source, target: l.target }))

    // 初始化 force-graph
    if (graphInstance) {
      graphInstance._destructor()
      graphInstance = null
    }

    graphInstance = ForceGraph()(graphContainer.value)
      .backgroundColor('rgba(0,0,0,0)')
      .nodeCanvasObject((node, ctx, globalScale) => {
        const label = node.name
        let currentRadius
        if (node.level === 1) currentRadius = 70
        else if (node.level === 2) currentRadius = 45
        else currentRadius = node.val || 10

        ctx.beginPath()
        ctx.arc(node.x, node.y, currentRadius, 0, 2 * Math.PI, false)
        if (node.level <= 2) {
          ctx.shadowColor = node.color
          ctx.shadowBlur = 10 / globalScale
        }
        ctx.fillStyle = node.color
        ctx.fill()
        ctx.shadowBlur = 0
        ctx.strokeStyle = '#ffffff'
        ctx.lineWidth = 1.5 / globalScale
        ctx.stroke()

        const fontSize = node.level === 1 ? 18 : node.level === 2 ? 14 : 11
        ctx.font = `${node.level <= 2 ? '600' : '500'} ${fontSize}px Sans-Serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = node.level === 1 ? '#ffffff' : '#001f3f'

        if (label.length > 6) {
          const mid = Math.ceil(label.length / 2)
          ctx.fillText(label.substring(0, mid), node.x, node.y - fontSize * 0.6)
          ctx.fillText(label.substring(mid), node.x, node.y + fontSize * 0.6)
        } else {
          ctx.fillText(label, node.x, node.y)
        }
      })
      .nodeLabel((node) => `<div style="background:rgba(0,0,0,0.75);color:#fff;padding:6px 12px;border-radius:6px;font-size:13px;max-width:320px;white-space:pre-wrap;word-break:break-all;">${node.fullName || node.name}</div>`)
      .linkDirectionalArrowLength(3)
      .linkDirectionalArrowRelPos(1)
      .d3Force('charge', d3.forceManyBody().strength(-2500))
      .d3Force('link', d3.forceLink().distance((d) => 120 + (d.source.val || 0) + (d.target.val || 0)))
      .d3Force('collide', d3.forceCollide((node) => (node.val || 10) + 15))
      .d3Force('center', d3.forceCenter(0, 0))
      .d3VelocityDecay(0.2)

    graphInstance.graphData({ nodes, links })

    setTimeout(() => {
      graphInstance.centerAt(0, 0, 500)
      graphInstance.zoom(0.5, 500)
    }, 500)
  } catch (e) {
    console.error('[JobKnowledgeGraph] load failed:', e)
    error.value = '图谱加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const resetView = () => {
  if (graphInstance) {
    graphInstance.centerAt(0, 0, 500)
    graphInstance.zoom(0.5, 500)
  }
}

watch(() => props.jobTitle, () => {
  nextTick(() => initGraph())
})

onMounted(() => {
  initGraph()
})

onBeforeUnmount(() => {
  if (graphInstance && typeof graphInstance._destructor === 'function') {
    graphInstance._destructor()
    graphInstance = null
  }
})
</script>

<style scoped>
.job-knowledge-graph {
  width: 100%;
  min-height: 200px;
}

.graph-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 300px;
  color: #e6a23c;
  font-size: 14px;
}

.graph-wrapper {
  position: relative;
  width: 100%;
  height: 600px;
  background: #fdfdfd;
  border-radius: 8px;
  border: 1px solid #f0f2f5;
  overflow: hidden;
}

.graph-canvas {
  width: 100%;
  height: 600px;
  background: radial-gradient(circle at center, #fefcce2d 0%, #e9f2fc99 100%);
  position: relative;
  overflow: hidden;
}

:deep(.graph-canvas canvas) {
  background-color: transparent !important;
}

.graph-loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(253, 253, 253, 0.85);
  color: #909399;
  font-size: 14px;
  z-index: 5;
}

.reset-btn {
  position: absolute;
  right: 15px;
  bottom: 15px;
  z-index: 10;
  box-shadow: 0 2px 12px rgba(89, 89, 89, 0.1);
}
</style>
