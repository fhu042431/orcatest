import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import KanbanColumn from '../components/KanbanColumn.vue'
import * as store from '../store/kanban.js'

// Reset store state
function resetStore() {
  store.state.orders.splice(0)
}

describe('KanbanColumn.vue', () => {
  beforeEach(() => {
    resetStore()
  })

  it('renders column title', () => {
    const wrapper = mount(KanbanColumn, {
      props: { columnId: 'pending', title: '待处理', color: '#f59e0b' },
    })
    expect(wrapper.text()).toContain('待处理')
  })

  it('shows order count', () => {
    store.addOrder('A', [{ name: 'x', quantity: 1, unitPrice: 1 }], 'pending')
    store.addOrder('B', [{ name: 'y', quantity: 1, unitPrice: 1 }], 'pending')
    const wrapper = mount(KanbanColumn, {
      props: { columnId: 'pending', title: '待处理', color: '#f59e0b' },
    })
    expect(wrapper.text()).toContain('2')
  })

  it('shows empty hint when no orders', () => {
    const wrapper = mount(KanbanColumn, {
      props: { columnId: 'pending', title: '待处理', color: '#f59e0b' },
    })
    expect(wrapper.text()).toContain('暂无订单')
  })

  it('renders KanbanCard for each order', () => {
    store.addOrder('A', [{ name: 'x', quantity: 1, unitPrice: 1 }], 'pending')
    store.addOrder('B', [{ name: 'y', quantity: 1, unitPrice: 1 }], 'pending')
    const wrapper = mount(KanbanColumn, {
      props: { columnId: 'pending', title: '待处理', color: '#f59e0b' },
    })
    const cards = wrapper.findAll('.kanban-card')
    expect(cards).toHaveLength(2)
  })

  it('has data-testid matching column id', () => {
    const wrapper = mount(KanbanColumn, {
      props: { columnId: 'shipped', title: '已发货', color: '#8b5cf6' },
    })
    expect(wrapper.attributes('data-testid')).toBe('column-shipped')
  })

  it('applies drag-over class when dragged over', async () => {
    const wrapper = mount(KanbanColumn, {
      props: { columnId: 'pending', title: '待处理', color: '#f59e0b' },
    })
    await wrapper.find('.kanban-column').trigger('dragover', { preventDefault: vi.fn() })
    expect(wrapper.find('.kanban-column').classes()).toContain('drag-over')
  })

  it('emits card-drop on drop with order id', async () => {
    store.addOrder('A', [{ name: 'x', quantity: 1, unitPrice: 1 }], 'pending')
    const order = store.getColumnOrders('pending')[0]

    const wrapper = mount(KanbanColumn, {
      props: { columnId: 'confirmed', title: '已确认', color: '#3b82f6' },
    })

    const dt = { getData: vi.fn().mockReturnValue(String(order.id)), preventDefault: vi.fn() }
    await wrapper.find('.kanban-column').trigger('drop', { dataTransfer: dt })

    expect(wrapper.emitted('card-drop')).toBeTruthy()
    expect(wrapper.emitted('card-drop')[0][0]).toEqual({
      orderId: order.id,
      toColumn: 'confirmed',
    })
  })

  it('does not emit card-drop when drag data is empty', async () => {
    const wrapper = mount(KanbanColumn, {
      props: { columnId: 'confirmed', title: '已确认', color: '#3b82f6' },
    })

    const dt = { getData: vi.fn().mockReturnValue(''), preventDefault: vi.fn() }
    await wrapper.find('.kanban-column').trigger('drop', { dataTransfer: dt })

    expect(wrapper.emitted('card-drop')).toBeFalsy()
  })

  it('only shows orders for its column', () => {
    store.addOrder('A', [{ name: 'x', quantity: 1, unitPrice: 1 }], 'pending')
    store.addOrder('B', [{ name: 'y', quantity: 1, unitPrice: 1 }], 'confirmed')

    const wrapper = mount(KanbanColumn, {
      props: { columnId: 'pending', title: '待处理', color: '#f59e0b' },
    })
    const cards = wrapper.findAll('.kanban-card')
    expect(cards).toHaveLength(1)
  })

  it('renders border-top color from prop', () => {
    const wrapper = mount(KanbanColumn, {
      props: { columnId: 'pending', title: '待处理', color: '#ff0000' },
    })
    const header = wrapper.find('.column-header')
    expect(header.attributes('style')).toContain('#ff0000')
  })
})
