<script setup>
import { ref } from 'vue'
import { moveOrder, addOrder } from '../store/kanban.js'
import KanbanColumn from '../components/KanbanColumn.vue'
import AddOrderDialog from '../components/AddOrderDialog.vue'

const showDialog = ref(false)

const columns = [
  { id: 'pending', title: '待处理', color: '#f59e0b' },
  { id: 'confirmed', title: '已确认', color: '#3b82f6' },
  { id: 'shipped', title: '已发货', color: '#8b5cf6' },
  { id: 'received', title: '已收货', color: '#10b981' },
  { id: 'cancelled', title: '已取消', color: '#ef4444' },
]

function onCardDrop({ orderId, toColumn }) {
  moveOrder(orderId, toColumn)
}

function onAddOrder(order) {
  addOrder(order.supplierName, order.items, order.status)
  showDialog.value = false
}
</script>

<template>
  <div class="kanban-board">
    <div class="kanban-header">
      <h1>采购订单看板</h1>
      <button class="add-btn" @click="showDialog = true">+ 新建订单</button>
    </div>
    <div class="kanban-columns">
      <KanbanColumn
        v-for="col in columns"
        :key="col.id"
        :column-id="col.id"
        :title="col.title"
        :color="col.color"
        @card-drop="onCardDrop"
      />
    </div>
    <AddOrderDialog
      v-if="showDialog"
      @close="showDialog = false"
      @submit="onAddOrder"
    />
  </div>
</template>

<style scoped>
.kanban-board {
  padding: 20px;
  min-height: calc(100vh - 52px);
  background: #f0f2f5;
}

.kanban-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.kanban-header h1 {
  margin: 0;
  font-size: 24px;
  color: #1a1a2e;
}

.add-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.add-btn:hover {
  background: #2563eb;
}

.kanban-columns {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 16px;
}
</style>
