<script setup>
import { computed } from 'vue'
import { getColumnOrders, state, setDragOverColumn } from '../store/kanban.js'
import KanbanCard from './KanbanCard.vue'

const props = defineProps({
  columnId: { type: String, required: true },
  title: { type: String, required: true },
  color: { type: String, default: '#6b7280' },
})

const emit = defineEmits(['card-drop'])

const orders = computed(() => getColumnOrders(props.columnId))
const isDragOver = computed(() => state.dragOverColumn === props.columnId)

function onDragOver(e) {
  e.preventDefault()
  setDragOverColumn(props.columnId)
}

function onDragLeave() {
  if (state.dragOverColumn === props.columnId) {
    setDragOverColumn(null)
  }
}

function onDrop(e) {
  e.preventDefault()
  const orderId = Number(e.dataTransfer.getData('text/plain'))
  if (orderId) {
    emit('card-drop', { orderId, toColumn: props.columnId })
  }
  setDragOverColumn(null)
}
</script>

<template>
  <div
    class="kanban-column"
    :class="{ 'drag-over': isDragOver }"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
    :data-testid="`column-${columnId}`"
  >
    <div class="column-header" :style="{ borderTopColor: color }">
      <span class="column-title">{{ title }}</span>
      <span class="column-count">{{ orders.length }}</span>
    </div>
    <div class="column-body">
      <KanbanCard
        v-for="order in orders"
        :key="order.id"
        :order="order"
        :column-color="color"
      />
      <div v-if="orders.length === 0" class="empty-hint">暂无订单</div>
    </div>
  </div>
</template>

<style scoped>
.kanban-column {
  flex: 0 0 260px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 140px);
  transition: box-shadow 0.2s;
}

.kanban-column.drag-over {
  box-shadow: 0 0 0 2px #3b82f6, 0 4px 12px rgba(59, 130, 246, 0.25);
}

.column-header {
  padding: 12px 16px;
  border-top: 3px solid;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.column-title {
  font-size: 14px;
  color: #374151;
}

.column-count {
  background: #f3f4f6;
  color: #6b7280;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

.column-body {
  padding: 8px 12px;
  flex: 1;
  overflow-y: auto;
  min-height: 60px;
}

.empty-hint {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  padding: 20px 0;
}
</style>
