import { describe, it, expect, beforeEach } from 'vitest'
import {
  state,
  addOrder,
  removeOrder,
  updateOrderStatus,
  getColumnOrders,
  moveOrder,
  createOrder,
  COLUMNS,
} from '../../src/store/kanban.js'

// Reset store state between tests
function resetStore() {
  state.orders.splice(0)
}

describe('kanban store', () => {
  beforeEach(() => {
    resetStore()
  })

  describe('createOrder', () => {
    it('creates order with correct fields', () => {
      const order = createOrder('供应商A', [{ name: '螺丝', quantity: 10, unitPrice: 5 }])
      expect(order.id).toBeDefined()
      expect(order.supplierName).toBe('供应商A')
      expect(order.items).toHaveLength(1)
      expect(order.totalAmount).toBe(50)
      expect(order.status).toBe('pending')
      expect(order.createdAt).toBeDefined()
    })

    it('calculates totalAmount from multiple items', () => {
      const order = createOrder('供应商B', [
        { name: '螺丝', quantity: 10, unitPrice: 5 },
        { name: '螺母', quantity: 20, unitPrice: 2 },
      ])
      expect(order.totalAmount).toBe(90)
    })

    it('uses provided status', () => {
      const order = createOrder('供应商A', [], 'confirmed')
      expect(order.status).toBe('confirmed')
    })

    it('defaults status to pending', () => {
      const order = createOrder('供应商A', [])
      expect(order.status).toBe('pending')
    })

    it('generates unique ids', () => {
      const o1 = createOrder('A', [])
      const o2 = createOrder('B', [])
      expect(o1.id).not.toBe(o2.id)
    })
  })

  describe('addOrder', () => {
    it('adds order to state', () => {
      const order = addOrder('供应商A', [{ name: '螺丝', quantity: 5, unitPrice: 10 }])
      expect(order).toBeDefined()
      const orders = getColumnOrders('pending')
      expect(orders).toHaveLength(1)
      expect(orders[0].supplierName).toBe('供应商A')
    })

    it('adds order with specific status', () => {
      addOrder('供应商A', [{ name: '螺丝', quantity: 5, unitPrice: 10 }], 'confirmed')
      expect(getColumnOrders('pending')).toHaveLength(0)
      expect(getColumnOrders('confirmed')).toHaveLength(1)
    })
  })

  describe('removeOrder', () => {
    it('removes order by id', () => {
      const order = addOrder('供应商A', [{ name: '螺丝', quantity: 5, unitPrice: 10 }])
      removeOrder(order.id)
      expect(getColumnOrders('pending')).toHaveLength(0)
    })

    it('does nothing for non-existent id', () => {
      addOrder('供应商A', [{ name: '螺丝', quantity: 5, unitPrice: 10 }])
      removeOrder(9999)
      expect(getColumnOrders('pending')).toHaveLength(1)
    })
  })

  describe('updateOrderStatus', () => {
    it('updates order status', () => {
      const order = addOrder('供应商A', [{ name: '螺丝', quantity: 5, unitPrice: 10 }])
      updateOrderStatus(order.id, 'shipped')
      expect(getColumnOrders('shipped')).toHaveLength(1)
      expect(getColumnOrders('pending')).toHaveLength(0)
    })

    it('does nothing for non-existent order', () => {
      addOrder('供应商A', [{ name: '螺丝', quantity: 5, unitPrice: 10 }])
      updateOrderStatus(9999, 'shipped')
      expect(getColumnOrders('pending')).toHaveLength(1)
      expect(getColumnOrders('shipped')).toHaveLength(0)
    })
  })

  describe('moveOrder', () => {
    it('moves order to new column', () => {
      const order = addOrder('供应商A', [{ name: '螺丝', quantity: 5, unitPrice: 10 }])
      moveOrder(order.id, 'confirmed')
      expect(getColumnOrders('confirmed')).toHaveLength(1)
      expect(getColumnOrders('pending')).toHaveLength(0)
    })

    it('does nothing if status is same', () => {
      const order = addOrder('供应商A', [{ name: '螺丝', quantity: 5, unitPrice: 10 }])
      moveOrder(order.id, 'pending')
      expect(getColumnOrders('pending')).toHaveLength(1)
    })
  })

  describe('getColumnOrders', () => {
    it('returns empty array for column with no orders', () => {
      expect(getColumnOrders('pending')).toEqual([])
    })

    it('returns only orders matching status', () => {
      addOrder('A', [{ name: 'x', quantity: 1, unitPrice: 1 }], 'pending')
      addOrder('B', [{ name: 'y', quantity: 1, unitPrice: 1 }], 'confirmed')
      addOrder('C', [{ name: 'z', quantity: 1, unitPrice: 1 }], 'pending')
      expect(getColumnOrders('pending')).toHaveLength(2)
      expect(getColumnOrders('confirmed')).toHaveLength(1)
      expect(getColumnOrders('shipped')).toHaveLength(0)
    })
  })

  describe('COLUMNS', () => {
    it('defines all 5 status columns', () => {
      expect(COLUMNS).toHaveLength(5)
      const ids = COLUMNS.map((c) => c.id)
      expect(ids).toContain('pending')
      expect(ids).toContain('confirmed')
      expect(ids).toContain('shipped')
      expect(ids).toContain('received')
      expect(ids).toContain('cancelled')
    })

    it('each column has id, title, and color', () => {
      COLUMNS.forEach((col) => {
        expect(col.id).toBeDefined()
        expect(col.title).toBeDefined()
        expect(col.color).toBeDefined()
      })
    })
  })
})
