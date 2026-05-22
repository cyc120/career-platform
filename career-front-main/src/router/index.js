// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue') // ✅ 指向 Home.vue
  },
  {
    path: '/jobs',
    name: 'JobExplorer',
    component: () => import('@/views/Jobs/JobExplorer.vue')
  },
  {
    path: '/job/:id',
    name: 'JobDetail',
    component: () => import('@/views/Jobs/JobDetail.vue')
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile/Index.vue'),
    children: [
      {
        path: 'info',
        name: 'PersonalInfo',
        component: () => import('@/views/Profile/PersonalInfo.vue')
      },
      {
        path: 'match',
        name: 'JobMatch',
        component: () => import('@/views/Profile/JobMatch.vue')
      },
      {
        path: 'growth',
        name: 'GrowthTracker',
        component: () => import('@/views/Profile/GrowthTracker.vue')
      },
      {
        path: 'favorites',
        name: 'FavoriteJobs',
        component: () => import('@/views/Profile/FavoriteJobs.vue')
      },
     {
        path: 'report-export',
        name: 'PolishAndExport',
        component: () => import('@/views/Profile/PolishAndExport.vue')
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;