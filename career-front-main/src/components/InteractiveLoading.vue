<template>
  <div class="interactive-loading" ref="containerRef" @mousemove="handleMouseMove" @mouseleave="handleMouseLeave">
    <!-- Canvas 粒子背景 -->
    <canvas ref="canvasRef" class="particle-canvas"></canvas>

    <!-- 浮动岗位球 - 带鼠标躲避 -->
    <div class="floating-orbs">
      <div
        v-for="(orb, idx) in orbs"
        :key="idx"
        class="orb-item"
        :style="{
          transform: `translate(${orb.x}px, ${orb.y}px) scale(${orb.scale})`,
          width: orb.size + 'px',
          height: orb.size + 'px',
          opacity: orb.opacity,
          background: orb.gradient,
          transition: orb.isDodging ? 'none' : 'transform 0.3s ease-out'
        }"
      >
        <span class="orb-label">{{ orb.label }}</span>
      </div>
    </div>

    <!-- 中心内容卡片 -->
    <div class="center-card">
      <div class="ai-status-bar">
        <div class="pulse-dot"></div>
        <span>{{ statusText }}</span>
      </div>

      <div class="loading-animation">
        <div class="orbit-ring ring-1"></div>
        <div class="orbit-ring ring-2"></div>
        <div class="core-icon">
          <el-icon><MagicStick /></el-icon>
        </div>
      </div>

      <h3 class="loading-title">{{ title }}</h3>
      <p class="loading-desc">{{ description }}</p>

      <div class="loading-steps" v-if="steps.length > 0">
        <div
          v-for="(step, i) in steps"
          :key="i"
          :class="['step-item', { active: currentStep >= i, done: currentStep > i }]"
        >
          <div class="step-indicator">
            <el-icon v-if="currentStep > i"><CircleCheck /></el-icon>
            <div v-else-if="currentStep === i" class="step-spinner"></div>
            <span v-else class="step-dot"></span>
          </div>
          <span class="step-text">{{ step }}</span>
        </div>
      </div>

      <div class="loading-progress" v-if="showProgress">
        <div class="progress-bar" :style="{ width: progress + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { MagicStick, CircleCheck } from '@element-plus/icons-vue'

const props = defineProps({
  title: { type: String, default: '加载中...' },
  description: { type: String, default: '' },
  statusText: { type: String, default: 'AI 引擎运行中' },
  steps: { type: Array, default: () => [] },
  currentStep: { type: Number, default: 0 },
  progress: { type: Number, default: 0 },
  showProgress: { type: Boolean, default: true },
  orbLabels: {
    type: Array,
    default: () => ['前端', '后端', 'AI', '数据', '产品', '安全', '运维', '设计']
  }
})

const containerRef = ref(null)
const canvasRef = ref(null)
const mouse = reactive({ x: -1000, y: -1000 })
let animationFrameId = null
let canvasCtx = null
let particles = []

// 浮动球数据
const orbConfigs = [
  { size: 70, baseX: 0.1, baseY: 0.15, speed: 0.8, gradient: 'linear-gradient(135deg, #f9d1c0 0%, #fcfbe3 100%)' },
  { size: 55, baseX: 0.85, baseY: 0.2, speed: 1.0, gradient: 'linear-gradient(135deg, #abcff6 0%, #c4efeb 100%)' },
  { size: 80, baseX: 0.08, baseY: 0.65, speed: 0.6, gradient: 'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)' },
  { size: 45, baseX: 0.88, baseY: 0.7, speed: 1.2, gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { size: 60, baseX: 0.5, baseY: 0.08, speed: 0.9, gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { size: 50, baseX: 0.35, baseY: 0.8, speed: 1.1, gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
  { size: 65, baseX: 0.92, baseY: 0.45, speed: 0.7, gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' },
  { size: 58, baseX: 0.15, baseY: 0.4, speed: 0.95, gradient: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)' },
]

const orbs = reactive(
  orbConfigs.map((config, idx) => ({
    ...config,
    label: props.orbLabels[idx] || '',
    x: 0,
    y: 0,
    vx: (Math.random() - 0.5) * 2,
    vy: (Math.random() - 0.5) * 2,
    scale: 1,
    opacity: 0.7 + Math.random() * 0.3,
    isDodging: false,
    floatPhase: Math.random() * Math.PI * 2,
  }))
)

// Canvas 粒子初始化
const initCanvas = () => {
  if (!canvasRef.value || !containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  canvasRef.value.width = rect.width
  canvasRef.value.height = rect.height
  canvasCtx = canvasRef.value.getContext('2d')

  particles = []
  for (let i = 0; i < 80; i++) {
    particles.push({
      x: Math.random() * rect.width,
      y: Math.random() * rect.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 2 + 1,
      color: Math.random() > 0.5 ? 'rgba(80, 152, 249, 0.3)' : 'rgba(118, 75, 162, 0.3)',
    })
  }
}

// 主渲染循环
const renderLoop = () => {
  if (!canvasCtx || !canvasRef.value || !containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const w = rect.width
  const h = rect.height

  canvasCtx.clearRect(0, 0, w, h)

  // 渲染粒子
  particles.forEach(p => {
    p.x += p.vx
    p.y += p.vy
    if (p.x < 0 || p.x > w) p.vx *= -1
    if (p.y < 0 || p.y > h) p.vy *= -1

    // 鼠标排斥效果
    const dx = mouse.x - p.x
    const dy = mouse.y - p.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist < 120) {
      p.x -= dx * 0.02
      p.y -= dy * 0.02
    }

    canvasCtx.fillStyle = p.color
    canvasCtx.beginPath()
    canvasCtx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
    canvasCtx.fill()
  })

  // 更新浮动球位置
  const time = Date.now() * 0.001
  orbs.forEach((orb, idx) => {
    // 基础浮动动画
    const floatX = Math.sin(time * orb.speed + orb.floatPhase) * 15
    const floatY = Math.cos(time * orb.speed * 0.8 + orb.floatPhase) * 12

    // 目标位置
    const targetX = orb.baseX * w + floatX - orb.size / 2
    const targetY = orb.baseY * h + floatY - orb.size / 2

    // 鼠标躲避
    const orbCenterX = targetX + orb.size / 2
    const orbCenterY = targetY + orb.size / 2
    const dx = mouse.x - orbCenterX
    const dy = mouse.y - orbCenterY
    const dist = Math.sqrt(dx * dx + dy * dy)
    const dodgeRadius = 120

    if (dist < dodgeRadius && dist > 0) {
      const force = (dodgeRadius - dist) / dodgeRadius * 60
      orb.x = targetX - (dx / dist) * force
      orb.y = targetY - (dy / dist) * force
      orb.isDodging = true
      orb.scale = 0.9
    } else {
      orb.x += (targetX - orb.x) * 0.08
      orb.y += (targetY - orb.y) * 0.08
      orb.isDodging = false
      orb.scale = 1
    }
  })

  animationFrameId = requestAnimationFrame(renderLoop)
}

// 鼠标交互
const handleMouseMove = (e) => {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  mouse.x = e.clientX - rect.left
  mouse.y = e.clientY - rect.top
}

const handleMouseLeave = () => {
  mouse.x = -1000
  mouse.y = -1000
}

// 窗口大小变化
const handleResize = () => {
  initCanvas()
}

onMounted(() => {
  initCanvas()
  renderLoop()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.interactive-loading {
  position: relative;
  width: 100%;
  min-height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 20px;
  background: linear-gradient(-45deg, #ff9a9e22, #fad0c422, #afcaf422, #b1efbf22);
  background-size: 400% 400%;
  animation: gradientBG 8s ease infinite;
}

.particle-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
}

.floating-orbs {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
  pointer-events: none;
}

.orb-item {
  position: absolute;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow:
    inset 0 1px 1px rgba(255, 255, 255, 0.8),
    0 8px 32px rgba(31, 38, 135, 0.08);
  cursor: default;
  will-change: transform;
}

.orb-label {
  font-size: 11px;
  font-weight: 600;
  color: #5098f9;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
  user-select: none;
}

.center-card {
  position: relative;
  z-index: 10;
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(24px) saturate(1.2);
  -webkit-backdrop-filter: blur(24px) saturate(1.2);
  border-radius: 24px;
  padding: 40px 50px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 20px 60px rgba(31, 38, 135, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.6);
  text-align: center;
  max-width: 480px;
  width: 100%;
}

.ai-status-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 12px;
  color: #5098f9;
  margin-bottom: 28px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  background: #5098f9;
  border-radius: 50%;
  box-shadow: 0 0 8px #5098f9;
  animation: blink 1.5s infinite;
}

.loading-animation {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 28px;
}

.orbit-ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid transparent;
}

.ring-1 {
  inset: 0;
  border-top-color: #5098f9;
  border-right-color: rgba(80, 152, 249, 0.3);
  animation: spinRing 2s linear infinite;
}

.ring-2 {
  inset: 12px;
  border-bottom-color: #764ba2;
  border-left-color: rgba(118, 75, 162, 0.3);
  animation: spinRing 3s linear infinite reverse;
}

.core-icon {
  position: absolute;
  inset: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #5098f9 0%, #764ba2 100%);
  border-radius: 50%;
  box-shadow: 0 8px 30px rgba(80, 152, 249, 0.35);
  animation: pulseGlow 2s ease-in-out infinite;
}

.core-icon .el-icon {
  font-size: 36px;
  color: white;
}

.loading-title {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.loading-desc {
  margin: 0 0 32px;
  font-size: 13px;
  color: #94a3b8;
}

.loading-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
  text-align: left;
  margin-bottom: 28px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #94a3b8;
  transition: all 0.3s;
}

.step-item.active {
  color: #5098f9;
  font-weight: 600;
}

.step-item.done {
  color: #6bd089;
}

.step-indicator {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-indicator .el-icon {
  color: #6bd089;
  font-size: 18px;
}

.step-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(80, 152, 249, 0.2);
  border-top-color: #5098f9;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #e2e8f0;
}

.loading-progress {
  height: 4px;
  background: rgba(80, 152, 249, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #5098f9, #764ba2);
  border-radius: 2px;
  transition: width 0.4s ease;
}

@keyframes gradientBG {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes spinRing {
  to { transform: rotate(360deg); }
}

@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 8px 30px rgba(80, 152, 249, 0.35); }
  50% { box-shadow: 0 8px 40px rgba(80, 152, 249, 0.55); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
