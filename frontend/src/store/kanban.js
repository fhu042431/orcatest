import { reactive, computed } from 'vue'

/**
 * Kanban store: manages board state for purchase-order kanban.
 * Columns represent order statuses; cards represent individual orders.
 */

const COLUMNS = [
  { id: 'pending', title: '待处理', color: '#f59e0b' },
  { id: 'confirmed', title: '已确认', color: '#3b82f6' },
  { id: 'shipped', title: '已发货', color: '#8b5cf6' },
  { id: 'received', title: '已收货', color: '#10b981' },
  { id: 'cancelled', title: '已取消', color: '#ef4444' },
]

let nextId = 1

function createOrder(supplierName, items, status = 'pending') {
  return {
    id: nextId++,
    supplierName,
    items,
    totalAmount: items.reduce((sum, it) => sum + it.quantity * it.unitPrice, 0),
    status,
    createdAt: new Date().toISOString(),
  }
}

const state = reactive({
  orders: [],
  dragOverColumn: null,
})

function addOrder(supplierName, items, status) {
  const order = createOrder(supplierName, items, status)
  state.orders.push(order)
  return order
}

function removeOrder(orderId) {
  const idx = state.orders.findIndex((o) => o.id === orderId)
  if (idx !== -1) state.orders.splice(idx, 1)
}

function updateOrderStatus(orderId, newStatus) {
  const order = state.orders.find((o) => o.id === orderId)
  if (order) {
    order.status = newStatus
  }
}

function getColumnOrders(status) {
  return state.orders.filter((o) => o.status === status)
}

function setDragOverColumn(colId) {
  state.dragOverColumn = colId
}

function moveOrder(orderId, toStatus) {
  const order = state.orders.find((o) => o.id === orderId)
  if (order && order.status !== toStatus) {
    order.status = toStatus
  }
}

const columns = computed(() =>
  COLUMNS.map((col) => ({
    ...col,
    orders: getColumnOrders(col.id),
  }))
)

const totalOrders = computed(() => state.orders.length)

export {
  state,
  COLUMNS,
  columns,
  totalOrders,
  addOrder,
  removeOrder,
  updateOrderStatus,
  getColumnOrders,
  moveOrder,
  setDragOverColumn,
  createOrder,
}
