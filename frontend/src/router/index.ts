import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/login/LoginView.vue'),
      meta: { title: '登录' }
    },
    {
      path: '/',
      component: () => import('../layouts/DefaultLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('../views/dashboard/DashboardView.vue'),
          meta: { title: '仪表盘' }
        },
        {
          path: 'category/:id',
          name: 'records',
          component: () => import('../views/records/RecordListView.vue'),
          meta: { title: '数据列表' }
        },
        {
          path: 'settings',
          name: 'settings',
          redirect: '/settings/general',
          children: [
            {
              path: 'general',
              redirect: '/settings/general/title',
              children: [
                { path: 'title', name: 'title', component: () => import('../views/settings/TitleView.vue'), meta: { title: '站点标题' } },
                { path: 'password', name: 'password', component: () => import('../views/settings/PasswordView.vue'), meta: { title: '修改账密' } }
              ]
            },
            {
              path: 'smtp',
              name: 'smtp',
              component: () => import('../views/settings/SmtpView.vue'),
              meta: { title: '邮件设置' }
            },
            {
              path: 'reminders',
              name: 'reminders',
              component: () => import('../views/reminders/ReminderLogView.vue'),
              meta: { title: '提醒日志' }
            },
            {
              path: 'database',
              name: 'database',
              component: () => import('../views/categories/CategoryManageView.vue'),
              meta: { title: '数据库管理' }
            },
            {
              path: 'import',
              name: 'import',
              component: () => import('../views/import_data/ImportExportView.vue'),
              meta: { title: '数据导入导出' }
            }
          ]
        }
      ]
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
