<template>
  <div class="app-container">
    <!-- 全局导航栏 -->
    <nav class="navbar">
      <div class="navbar-left">
        <div class="logo-wrapper" @click="router.push('/')">
          <img src="@/assets/logo.png" alt="Logo" class="nav-logo-img" />
          <div class="brand-text">
            <span class="brand-ch">职途无限</span>
            <span class="brand-en">INFINITE PATH</span>
          </div>
        </div>
</div>
      
      <div class="navbar-center">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/jobs" class="nav-link">岗位探索</router-link>
        <router-link to="/profile" class="nav-link">个人中心</router-link>
      </div>
      
      <div class="navbar-right">
        <template v-if="isLoggedIn">
          <el-dropdown trigger="click" placement="bottom-end">
            <div class="user-pill">
              <div class="avatar-wrapper">
                {{ userData.name?.charAt(0) }}
              </div>
              <span class="username">{{ userData.name }}</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </div>

            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/profile')">个人中心</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout" class="logout-item">
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        
        <template v-else>
          <el-button type="primary" round @click="handleLogin">登录/注册</el-button>
        </template>
      </div>
    </nav>

    <!-- 路由视图 -->
    <router-view />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const isLoggedIn = computed(() => auth.isLoggedIn)
const userData = computed(() => auth.user || { name: '用户' })

const handleLogin = () => {
  router.push('/profile/info')
}

const handleLogout = async () => {
  await auth.logout()
  router.push('/')
}
</script>

<style scoped lang="scss">
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #eff5f8;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  height: 64px; /* 稍微加高一点，比例更协调 */
  
background: linear-gradient(
    to bottom, 
    rgba(200, 226, 245, 0.634) 0%, 
    rgba(253, 252, 224, 0.318) 100%
  );

  /* 🌟 核心：毛玻璃效果 */
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);

  /* 🌟 消除生硬感的关键：去掉阴影，使用极细的浅色描边 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  
  /* 如果一定要有阴影，使用非常淡的扩散投影 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 1000;

  .navbar-left {
    display: flex;
    align-items: center;

    .logo-wrapper {
      display: flex;      /* 关键：让图片和文字横向排列 */
      align-items: center; /* 关键：让图片和文字垂直居中 */
      gap: 15px;          /* 图片和文字的间距 */

      .nav-logo-img {
        height: 40px;
        width: auto;
        object-fit: contain;
      }

      .brand-text {
        display: flex;
        flex-direction: column; /* 文字保持上下排列 */
        line-height: 1.1;

        .brand-ch {
          font-family: "Inter", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
          font-size: 18px;
          font-weight: 600;
          color: #082645;
          letter-spacing: 1px;
        }

        .brand-en {
          
          font-size: 10px;
          color: #909399;
          letter-spacing: 1.5px;
          transform: scale(0.85);
          transform-origin: left;
      }
    }
  }
}

.nav-logo-img {
  height: 40px;
  width: auto;
  object-fit: contain;
  
  /* 1. 核心修补：使用 drop-shadow 而不是 box-shadow */
  /* 颜色建议：使用比背景色稍微深一点或浅一点的颜色，这里用半透明色 */
  filter: drop-shadow(0 0 1px rgba(255, 255, 255, 0.5)) 
          blur(0.2px); /* 极微小的模糊可以软化锯齿 */

  /* 2. 混合模式（魔法步骤）：
     如果你的导航栏是白色的，用 multiply；
     如果你的导航栏是深色的，用 screen；
     这会自动过滤掉边缘残留的杂色 */
  mix-blend-mode: multiply; 

  /* 3. 稍微调低一点点对比度，减少硬边缘的视觉冲击 */
  opacity: 0.95; 
  
  transition: all 0.3s ease;
}

.nav-logo-img:hover {
  opacity: 1;
  filter: drop-shadow(0 0 5px rgba(64, 158, 255, 0.3)); /* 悬停时用发光掩盖边缘 */
  transform: scale(1.02);
}

  .navbar-center {
    display: flex;
    gap: 80px;

    .nav-link {
      text-decoration: none;
      color: #606266;
      font-size: 16px;
      transition: color 0.3s;
      position: relative;

      &:hover {
        color: #2e497b;
      }

      &.router-link-active {
        color: #082645;
        font-weight: bold;
      }

      &::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 50%;
    width: 0;
    height: 2px;
    background: #072645;
    transition: all 0.3s ease;
    transform: translateX(-50%);
  }

  &:hover::after,
  &.router-link-active::after {
    width: 25px; /* 划线展开 */
  }
    }
  }

.navbar-right {
  display: flex;
  align-items: center;

  .user-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px 4px 4px; /* 左侧留窄给头像，右侧留宽给文字 */
    background: rgba(255, 255, 255, 0.6); /* 配合毛玻璃导航栏 */
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 20px; /* 胶囊形状 */
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      background: #fff;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
      border-color: #409EFF;
    }

    .avatar-wrapper {
      width: 28px;
      height: 28px;
      background: linear-gradient(135deg, #409EFF, #67C23A); /* 渐变色头像背景 */
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: bold;
      box-shadow: 0 2px 4px rgba(64, 158, 255, 0.2);
    }

    .username {
      font-size: 14px;
      color: #303133;
      font-weight: 500;
    }

    .el-icon--right {
      font-size: 12px;
      color: #909399;
    }
  }
}

// 退出登录按钮标红
.logout-item {
  color: #f56c6c !important;
}
}
</style>