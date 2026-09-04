import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import KanbanBoard from '../views/KanbanBoard.vue'
import * as store from '../store/kanban.js'

function resetStore() {
  store.state.orders.splice(0)
}

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/kanban', component: KanbanBoard },
    ],
  })
}

describe('KanbanBoard.vue', () => {
  beforeEach(() => {
    resetStore()
  })

  it('renders page title', async () => {
    const router = createTestRouter()
    router.push('/kanban')
    await router.isReady()

    const wrapper = mount(KanbanBoard, {
      global: { plugins: [router] },
    })
    expect(wrapper.text()).toContain('采购订单看板')
  })

  it('renders all 5 columns', async () => {
    const router = createTestRouter()
    router.push('/kanban')
    await router.isReady()

    const wrapper = mount(KanbanBoard, {
      global: { plugins: [router] },
    })
    expect(wrapper.text()).toContain('待处理')
    expect(wrapper.text()).toContain('已确认')
    expect(wrapper.text()).toContain('已发货')
    expect(wrapper.text()).toContain('已收货')
    expect(wrapper.text()).toContain('已取消')
  })

  it('shows add order button', async () => {
    const router = createTestRouter()
    router.push('/kanban')
    await router.isReady()

    const wrapper = mount(KanbanBoard, {
      global: { plugins: [router] },
    })
    expect(wrapper.find('.add-btn').exists()).toBe(true)
    expect(wrapper.text()).toContain('新建订单')
  })

  it('opens dialog when add button clicked', async () => {
    const router = createTestRouter()
    router.push('/kanban')
    await router.isReady()

    const wrapper = mount(KanbanBoard, {
      global: { plugins: [router] },
    })
    await wrapper.find('.add-btn').trigger('click')
    expect(wrapper.find('[data-testid="add-order-dialog"]').exists()).toBe(true)
  })

  it('shows empty columns initially', async () => {
    const router = createTestRouter()
    router.push('/kanban')
    await router.isReady()

    const wrapper = mount(KanbanBoard, {
      global: { plugins: [router] },
    })
    const emptyHints = wrapper.findAll('.empty-hint')
    expect(emptyHints).toHaveLength(5)
  })

  it('adding order places it in correct column', async () => {
    const router = createTestRouter()
    router.push('/kanban')
    await router.isReady()

    const wrapper = mount(KanbanBoard, {
      global: { plugins: [router] },
    })

    // Open dialog and submit
    await wrapper.find('.add-btn').trigger('click')
    const dialog = wrapper.findComponent({ name: 'AddOrderDialog' })
    await dialog.find('[data-testid="input-supplier"]').setValue('供应商A')
    await dialog.find('[data-testid="input-item-name"]').setValue('螺丝')
    await dialog.find('[data-testid="input-quantity"]').setValue(10)
    await dialog.find('[data-testid="input-price"]').setValue(5)
    await dialog.find('form').trigger('submit')

    // Check pending column has 1 card
    const pendingColumn = wrapper.find('[data-testid="column-pending"]')
    const cards = pendingColumn.findAll('.kanban-card')
    expect(cards).toHaveLength(1)
  })

  it('renders column count badges', async () => {
    store.addOrder('A', [{ name: 'x', quantity: 1, unitPrice: 1 }], 'pending')

    const router = createTestRouter()
    router.push('/kanban')
    await router.isReady()

    const wrapper = mount(KanbanBoard, {
      global: { plugins: [router] },
    })
    const pendingCol = wrapper.find('[data-testid="column-pending"]')
    expect(pendingCol.text()).toContain('1')
  })
})
