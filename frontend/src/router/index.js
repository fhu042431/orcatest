import { createRouter, createWebHistory } from 'vue-router'
import KanbanBoard from '../views/KanbanBoard.vue'

const routes = [
  {
    path: '/',
    redirect: '/kanban',
  },
  {
    path: '/kanban',
    name: 'KanbanBoard',
    component: KanbanBoard,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
