<template>
  <div class="interactive-loading" ref="containerRef" @mousemove="handleMouseMove" @mouseleave="handleMouseLeave">
    <!-- Canvas 粒子背景 -->
    <canvas ref="canvasRef" class="particle-canvas"></canvas>

    <!-- 极光背景 -->
    <div class="aurora-bg"></div>

    <!-- 浮动岗位球 - 带鼠标躲避 -->
    <div class="floating-orbs">
      <div
        v-for="(orb, idx) in orbs"
        :key="idx"
        class="orb-item"
        :style="{
          transform: `translate(${orb.x}px, ${orb.y}px) scale(${orb.scale}) rotate(${orb.rotation}deg)`,
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
        <div class="orbit-ring ring-1"><span class="satellite-dot sat-1"></span></div>
        <div class="orbit-ring ring-2"><span class="satellite-dot sat-2"></span></div>
        <div class="orbit-ring ring-3"><span class="satellite-dot sat-3"></span></div>
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
  { size: 70, baseX: 0.1, baseY: 0.15, speed: 0.8, gradient: 'linear-gradient(135deg, rgba(249,209,192,0.4) 0%, rgba(252,251,227,0.4) 100%)' },
  { size: 55, baseX: 0.85, baseY: 0.2, speed: 1.0, gradient: 'linear-gradient(135deg, rgba(171,207,246,0.4) 0%, rgba(196,239,235,0.4) 100%)' },
  { size: 80, baseX: 0.08, baseY: 0.65, speed: 0.6, gradient: 'linear-gradient(135deg, rgba(161,196,253,0.4) 0%, rgba(194,233,251,0.4) 100%)' },
  { size: 45, baseX: 0.88, baseY: 0.7, speed: 1.2, gradient: 'linear-gradient(135deg, rgba(240,147,251,0.3) 0%, rgba(245,87,108,0.3) 100%)' },
  { size: 60, baseX: 0.5, baseY: 0.08, speed: 0.9, gradient: 'linear-gradient(135deg, rgba(79,172,254,0.35) 0%, rgba(0,242,254,0.35) 100%)' },
  { size: 50, baseX: 0.35, baseY: 0.8, speed: 1.1, gradient: 'linear-gradient(135deg, rgba(67,233,123,0.3) 0%, rgba(56,249,215,0.3) 100%)' },
  { size: 65, baseX: 0.92, baseY: 0.45, speed: 0.7, gradient: 'linear-gradient(135deg, rgba(250,112,154,0.3) 0%, rgba(254,225,64,0.3) 100%)' },
  { size: 58, baseX: 0.15, baseY: 0.4, speed: 0.95, gradient: 'linear-gradient(135deg, rgba(161,140,209,0.35) 0%, rgba(251,194,235,0.35) 100%)' },
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
    opacity: 0.35 + Math.random() * 0.2,
    isDodging: false,
    floatPhase: Math.random() * Math.PI * 2,
    rotation: Math.random() * 360,
  }))
)

// Canvas 粒子初始化（自适应容器尺寸 + 设备像素比）
let containerW = 0
let containerH = 0

const initCanvas = () => {
  if (!canvasRef.value || !containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  containerW = rect.width
  containerH = rect.height
  canvasRef.value.width = containerW * dpr
  canvasRef.value.height = containerH * dpr
  canvasRef.value.style.width = containerW + 'px'
  canvasRef.value.style.height = containerH + 'px'
  canvasCtx = canvasRef.value.getContext('2d')
  canvasCtx.setTransform(dpr, 0, 0, dpr, 0, 0)

  // 重新分配粒子位置（保留已有粒子则只调整越界的）
  if (particles.length === 0) {
    for (let i = 0; i < 80; i++) {
      particles.push({
        x: Math.random() * containerW,
        y: Math.random() * containerH,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: Math.random() * 2 + 1,
        color: Math.random() > 0.5 ? 'rgba(80, 152, 249, 0.3)' : 'rgba(118, 75, 162, 0.3)',
      })
    }
  } else {
    particles.forEach(p => {
      if (p.x > containerW) p.x = Math.random() * containerW
      if (p.y > containerH) p.y = Math.random() * containerH
    })
  }
}

// 主渲染循环
const renderLoop = () => {
  if (!canvasCtx || !canvasRef.value || !containerRef.value) return
  const w = containerW
  const h = containerH
  if (w === 0 || h === 0) {
    animationFrameId = requestAnimationFrame(renderLoop)
    return
  }

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

  // 粒子星座连线
  const CONNECTION_DIST = 150
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x
      const dy = particles[i].y - particles[j].y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < CONNECTION_DIST) {
        const opacity = (1 - dist / CONNECTION_DIST) * 0.25
        canvasCtx.strokeStyle = `rgba(80, 152, 249, ${opacity})`
        canvasCtx.lineWidth = 0.6
        canvasCtx.beginPath()
        canvasCtx.moveTo(particles[i].x, particles[i].y)
        canvasCtx.lineTo(particles[j].x, particles[j].y)
        canvasCtx.stroke()
      }
    }
  }

  // 更新浮动球位置
  const time = Date.now() * 0.001
  orbs.forEach((orb, idx) => {
    // 缓慢旋转
    orb.rotation = (time * orb.speed * 20) % 360

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

// 容器尺寸变化（ResizeObserver 比 window.resize 更准确）
let resizeObserver = null

onMounted(() => {
  initCanvas()
  renderLoop()
  if (containerRef.value && window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      initCanvas()
    })
    resizeObserver.observe(containerRef.value)
  } else {
    window.addEventListener('resize', initCanvas)
  }
})

onUnmounted(() => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  if (resizeObserver) {
    resizeObserver.disconnect()
  } else {
    window.removeEventListener('resize', initCanvas)
  }
})
</script>

<style scoped>
.interactive-loading {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 20px;
  background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 50%, #f5f0ff 100%);
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

.aurora-bg {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(80, 152, 249, 0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(118, 75, 162, 0.10) 0%, transparent 50%),
    radial-gradient(ellipse at 40% 80%, rgba(67, 233, 123, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 60%, rgba(250, 112, 154, 0.08) 0%, transparent 50%);
  animation: auroraMove 12s ease-in-out infinite alternate;
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
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow:
    inset 0 1px 2px rgba(255, 255, 255, 0.6),
    0 8px 40px rgba(31, 38, 135, 0.05);
  cursor: default;
  will-change: transform;

  &::before {
    content: '';
    position: absolute;
    inset: -25%;
    border-radius: 50%;
    background: inherit;
    filter: blur(20px);
    opacity: 0.6;
    z-index: -1;
  }
}

.orb-label {
  font-size: 11px;
  font-weight: 600;
  color: rgba(80, 152, 249, 0.6);
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
  padding: clamp(20px, 5%, 40px) clamp(24px, 6%, 50px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 20px 60px rgba(31, 38, 135, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.6);
  text-align: center;
  max-width: 480px;
  width: 100%;
  margin: clamp(8px, 2%, 20px);
}

.loading-animation {
  position: relative;
  width: clamp(80px, 15vw, 120px);
  height: clamp(80px, 15vw, 120px);
  margin: 0 auto clamp(16px, 3vw, 28px);
}

.loading-title {
  margin: 0 0 clamp(4px, 1vw, 8px);
  font-size: clamp(16px, 2.5vw, 20px);
  font-weight: 700;
  color: #1e293b;
}

.loading-desc {
  margin: 0 0 clamp(16px, 3vw, 32px);
  font-size: clamp(11px, 1.5vw, 13px);
  color: #94a3b8;
}

.loading-steps {
  display: flex;
  flex-direction: column;
  gap: clamp(6px, 1vw, 12px);
  text-align: left;
  margin-bottom: clamp(14px, 3vw, 28px);
}

.step-item {
  display: flex;
  align-items: center;
  gap: clamp(8px, 1.5vw, 12px);
  font-size: clamp(11px, 1.5vw, 13px);
  color: #94a3b8;
  opacity: 0.4;
  transform: translateX(-8px);
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
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

.orbit-ring {
  position: absolute;
  border-radius: 50%;
}

.ring-1 {
  inset: 0;
  background: conic-gradient(from 0deg, #5098f9, rgba(80, 152, 249, 0.15), #5098f9);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 2px), #fff calc(100% - 2px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 2px), #fff calc(100% - 2px));
  animation: spinRing 2s linear infinite;
}

.ring-2 {
  inset: 12px;
  background: conic-gradient(from 120deg, #764ba2, rgba(118, 75, 162, 0.15), #764ba2);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 2px), #fff calc(100% - 2px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 2px), #fff calc(100% - 2px));
  animation: spinRing 3s linear infinite reverse;
}

.ring-3 {
  inset: -10px;
  background: conic-gradient(from 240deg, #4facfe, rgba(79, 172, 254, 0.1), #43e97b, rgba(67, 233, 123, 0.1), #4facfe);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 1.5px), #fff calc(100% - 1.5px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 1.5px), #fff calc(100% - 1.5px));
  animation: spinRing 5s linear infinite;
  opacity: 0.6;
}

.satellite-dot {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #5098f9;
  box-shadow: 0 0 8px rgba(80, 152, 249, 0.6);
  top: -3px;
  left: 50%;
  margin-left: -3px;
}

.sat-2 {
  background: #764ba2;
  box-shadow: 0 0 8px rgba(118, 75, 162, 0.6);
  top: auto;
  bottom: -3px;
  left: 50%;
}

.sat-3 {
  background: #4facfe;
  box-shadow: 0 0 8px rgba(79, 172, 254, 0.6);
  top: 50%;
  left: -3px;
  margin-left: 0;
  margin-top: -3px;
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

.step-item.active {
  color: #5098f9;
  font-weight: 600;
  opacity: 1;
  transform: translateX(0);
}

.step-item.done {
  color: #6bd089;
  opacity: 0.85;
  transform: translateX(0);
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
  position: relative;
  overflow: hidden;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.4) 50%,
      transparent 100%
    );
    background-size: 50% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
  }
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}

@keyframes auroraMove {
  0% { transform: translate(0%, 0%) rotate(0deg) scale(1); }
  33% { transform: translate(5%, -3%) rotate(2deg) scale(1.05); }
  66% { transform: translate(-3%, 5%) rotate(-1deg) scale(0.98); }
  100% { transform: translate(2%, -2%) rotate(1deg) scale(1.02); }
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
