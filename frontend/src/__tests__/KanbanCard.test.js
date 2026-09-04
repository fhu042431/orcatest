import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import KanbanCard from '../components/KanbanCard.vue'

describe('KanbanCard.vue', () => {
  const defaultOrder = {
    id: 1,
    supplierName: '供应商A',
    items: [
      { name: '螺丝', quantity: 10, unitPrice: 5 },
      { name: '螺母', quantity: 20, unitPrice: 2 },
    ],
    totalAmount: 90,
    status: 'pending',
    createdAt: '2026-09-04T10:00:00.000Z',
  }

  it('renders order id', () => {
    const wrapper = mount(KanbanCard, { props: { order: defaultOrder } })
    expect(wrapper.text()).toContain('#1')
  })

  it('renders supplier name', () => {
    const wrapper = mount(KanbanCard, { props: { order: defaultOrder } })
    expect(wrapper.text()).toContain('供应商A')
  })

  it('renders all items', () => {
    const wrapper = mount(KanbanCard, { props: { order: defaultOrder } })
    expect(wrapper.text()).toContain('螺丝 × 10')
    expect(wrapper.text()).toContain('螺母 × 20')
  })

  it('renders formatted total amount', () => {
    const wrapper = mount(KanbanCard, { props: { order: defaultOrder } })
    expect(wrapper.text()).toContain('¥90.00')
  })

  it('renders date', () => {
    const wrapper = mount(KanbanCard, { props: { order: defaultOrder } })
    expect(wrapper.text()).toContain('2026')
  })

  it('has draggable attribute', () => {
    const wrapper = mount(KanbanCard, { props: { order: defaultOrder } })
    expect(wrapper.attributes('draggable')).toBe('true')
  })

  it('sets dataTransfer on dragstart', async () => {
    const wrapper = mount(KanbanCard, { props: { order: defaultOrder } })
    const dt = { setData: vi.fn(), effectAllowed: '' }
    await wrapper.find('[draggable]').trigger('dragstart', { dataTransfer: dt })
    expect(dt.setData).toHaveBeenCalledWith('text/plain', '1')
    expect(dt.effectAllowed).toBe('move')
  })

  it('receives columnColor prop', () => {
    const wrapper = mount(KanbanCard, {
      props: { order: defaultOrder, columnColor: '#ff0000' },
    })
    expect(wrapper.props('columnColor')).toBe('#ff0000')
  })

  it('renders with empty items', () => {
    const order = { ...defaultOrder, items: [], totalAmount: 0 }
    const wrapper = mount(KanbanCard, { props: { order } })
    expect(wrapper.text()).toContain('#1')
    expect(wrapper.text()).toContain('¥0.00')
  })

  it('has delete button', () => {
    const wrapper = mount(KanbanCard, { props: { order: defaultOrder } })
    const btn = wrapper.find('.delete-btn')
    expect(btn.exists()).toBe(true)
  })

  it('renders zero-quantity items', () => {
    const order = {
      ...defaultOrder,
      items: [{ name: '测试', quantity: 0, unitPrice: 10 }],
      totalAmount: 0,
    }
    const wrapper = mount(KanbanCard, { props: { order } })
    expect(wrapper.text()).toContain('测试 × 0')
  })

  it('renders order with high id', () => {
    const order = { ...defaultOrder, id: 9999 }
    const wrapper = mount(KanbanCard, { props: { order } })
    expect(wrapper.text()).toContain('#9999')
  })

  it('formats large amounts correctly', () => {
    const order = { ...defaultOrder, totalAmount: 12345.67 }
    const wrapper = mount(KanbanCard, { props: { order } })
    expect(wrapper.text()).toContain('¥12345.67')
  })

  it('formats zero amount correctly', () => {
    const order = { ...defaultOrder, totalAmount: 0 }
    const wrapper = mount(KanbanCard, { props: { order } })
    expect(wrapper.text()).toContain('¥0.00')
  })
})
