<template>
  <el-container class="layout-container">
    <!-- 移动端遮罩层 -->
    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="closeMobileMenu"></div>

    <!-- PC端侧边栏 / 移动端浮动侧边栏 -->
    <el-aside
      :width="isCollapse && !isMobile ? '64px' : '220px'"
      :class="['layout-aside', { 'mobile-open': mobileMenuOpen, 'mobile-aside': isMobile }]"
    >
      <div class="logo">
        <el-icon size="22"><DataBoard /></el-icon>
        <span v-show="!isCollapse || isMobile">{{ siteTitle }}</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse && !isMobile"
        router
        class="side-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        @select="closeMobileMenu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item v-for="cat in categories" :key="cat.id" :index="`/category/${cat.id}`">
          <el-icon><component :is="cat.icon || 'Folder'" /></el-icon>
          <span>{{ cat.name }}</span>
        </el-menu-item>
        <el-sub-menu index="/settings">
          <template #title>
            <el-icon><Tools /></el-icon>
            <span>系统设置</span>
          </template>
          <el-sub-menu index="/settings/general">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>常用设置</span>
            </template>
            <el-menu-item index="/settings/general/title"><el-icon><EditPen /></el-icon><span>站点标题</span></el-menu-item>
            <el-menu-item index="/settings/general/password"><el-icon><Key /></el-icon><span>修改账密</span></el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/settings/smtp"><el-icon><Message /></el-icon><span>邮件设置</span></el-menu-item>
          <el-menu-item index="/settings/reminders"><el-icon><Bell /></el-icon><span>提醒日志</span></el-menu-item>
          <el-menu-item index="/settings/database"><el-icon><Coin /></el-icon><span>数据库管理</span></el-menu-item>
          <el-menu-item index="/settings/import"><el-icon><Upload /></el-icon><span>数据导入导出</span></el-menu-item>
        </el-sub-menu>
      </el-menu>

      <div class="collapse-btn" @click="toggleCollapse" v-if="!isMobile">
        <el-icon :size="16"><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
        <span v-show="!isCollapse">收起</span>
      </div>
    </el-aside>

    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon v-if="isMobile" size="20" @click="toggleMobileMenu" style="cursor:pointer">
            <Operation />
          </el-icon>
          <el-icon v-else size="18" @click="toggleCollapse" style="cursor:pointer">
            <Fold v-if="!isCollapse" /><Expand v-else />
          </el-icon>
          <span class="header-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-badge :value="dueCount" :hidden="dueCount === 0">
            <el-icon size="18" @click="$router.push('/settings/reminders')" style="cursor:pointer">
              <Bell />
            </el-icon>
          </el-badge>
          <span class="username" v-if="!isMobile">{{ authStore.username }}</span>
          <el-button type="danger" size="small" @click="authStore.logout" text>退出</el-button>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSiteStore } from '../stores/site'
import { categoryApi, dashboardApi } from '../api'

const route = useRoute()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const isCollapse = ref(false)
const mobileMenuOpen = ref(false)
const windowWidth = ref(window.innerWidth)
const categories = ref<any[]>([])
const dueCount = ref(0)

const isMobile = computed(() => windowWidth.value < 768)

const activeMenu = computed(() => {
  if (route.path.startsWith('/category/')) return route.path
  if (route.path.startsWith('/settings')) return route.path
  return route.path
})

const pageTitle = computed(() => route.meta.title as string || '')
const siteTitle = computed(() => siteStore.title)

function onResize() { windowWidth.value = window.innerWidth }

function toggleCollapse() { isCollapse.value = !isCollapse.value }

function toggleMobileMenu() { mobileMenuOpen.value = !mobileMenuOpen.value }

function closeMobileMenu() { mobileMenuOpen.value = false }

onMounted(async () => {
  window.addEventListener('resize', onResize)
  siteStore.fetchTitle()
  try {
    const [catRes, statsRes] = await Promise.all([categoryApi.list(), dashboardApi.stats()])
    categories.value = catRes.data || []
    dueCount.value = statsRes.data.pendingCount || 0
  } catch {}
})

onUnmounted(() => { window.removeEventListener('resize', onResize) })

watch(() => route.path, async () => {
  if (route.path === '/dashboard') {
    try { const s = await dashboardApi.stats(); dueCount.value = s.data.pendingCount || 0 } catch {}
  }
})
</script>

<style scoped>
.layout-container { height: 100vh; }
.layout-aside {
  background-color: #304156;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.3s;
  position: relative;
  flex-shrink: 0;
}
.layout-aside :deep(.el-menu) { border-right: none; }
.layout-aside :deep(.el-menu--collapse) { width: 64px; }
.layout-aside :deep(.el-menu-vertical:not(.el-menu--collapse)) { width: 220px; }
.logo {
  height: 56px; display: flex; align-items: center; justify-content: center;
  gap: 8px; color: #fff; font-size: 16px; font-weight: 600;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  white-space: nowrap; overflow: hidden;
}
.side-menu { border-right: none; }
.collapse-btn {
  position: absolute; bottom: 0; width: 100%; height: 40px;
  display: flex; align-items: center; justify-content: center;
  gap: 6px; font-size: 13px; color: #bfcbd9; cursor: pointer;
  border-top: 1px solid rgba(255,255,255,0.1);
  transition: background 0.2s; user-select: none;
}
.collapse-btn:hover { background: rgba(255,255,255,0.05); color: #409EFF; }
.layout-header {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-bottom: 1px solid #e6e6e6;
  padding: 0 16px; height: 52px;
}
.header-left { display: flex; align-items: center; gap: 10px; }
.header-title { font-size: 16px; font-weight: 500; }
.header-right { display: flex; align-items: center; gap: 12px; }
.username { color: #606266; font-size: 14px; }
.layout-main {
  background: #f5f7fa;
  min-height: calc(100vh - 52px);
  padding: 12px;
}

/* 移动端侧边栏：默认隐藏，浮动覆盖 */
.mobile-aside {
  position: fixed !important;
  left: -220px;
  top: 0;
  bottom: 0;
  z-index: 1000;
  width: 220px !important;
  transition: left 0.3s;
}
.mobile-aside.mobile-open { left: 0; }
.mobile-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  z-index: 999;
}

/* 移动端响应式调整 */
@media (max-width: 767px) {
  .layout-header { padding: 0 12px; }
  .header-title { font-size: 15px; }
}
</style>
