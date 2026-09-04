<script setup>
import { removeOrder } from '../store/kanban.js'

const props = defineProps({
  order: { type: Object, required: true },
  columnColor: { type: String, default: '#6b7280' },
})

function onDragStart(e) {
  e.dataTransfer.setData('text/plain', String(props.order.id))
  e.dataTransfer.effectAllowed = 'move'
}

function handleDelete() {
  removeOrder(props.order.id)
}

function formatAmount(amount) {
  return `¥${amount.toFixed(2)}`
}
</script>

<template>
  <div
    class="kanban-card"
    draggable="true"
    @dragstart="onDragStart"
    :data-testid="`card-${order.id}`"
  >
    <div class="card-header">
      <span class="card-id">#{{ order.id }}</span>
      <button class="delete-btn" @click.stop="handleDelete" title="删除订单">&times;</button>
    </div>
    <div class="card-supplier">{{ order.supplierName }}</div>
    <div class="card-items">
      <div v-for="(item, idx) in order.items" :key="idx" class="card-item">
        {{ item.name }} × {{ item.quantity }}
      </div>
    </div>
    <div class="card-footer">
      <span class="card-amount">{{ formatAmount(order.totalAmount) }}</span>
      <span class="card-time">{{ new Date(order.createdAt).toLocaleDateString() }}</span>
    </div>
  </div>
</template>

<style scoped>
.kanban-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-left: 3px solid;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 8px;
  cursor: grab;
  transition: box-shadow 0.15s, transform 0.15s;
}

.kanban-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.kanban-card:active {
  cursor: grabbing;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.card-id {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
}

.delete-btn {
  background: none;
  border: none;
  color: #d1d5db;
  font-size: 16px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  transition: color 0.15s;
}

.delete-btn:hover {
  color: #ef4444;
}

.card-supplier {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 6px;
}

.card-items {
  margin-bottom: 8px;
}

.card-item {
  font-size: 12px;
  color: #6b7280;
  padding: 1px 0;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.card-amount {
  font-weight: 600;
  color: #059669;
}

.card-time {
  color: #9ca3af;
}
</style>
