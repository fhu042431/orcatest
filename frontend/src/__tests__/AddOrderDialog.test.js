import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AddOrderDialog from '../components/AddOrderDialog.vue'

describe('AddOrderDialog.vue', () => {
  it('renders dialog with form fields', () => {
    const wrapper = mount(AddOrderDialog)
    expect(wrapper.find('[data-testid="add-order-dialog"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="input-supplier"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="input-item-name"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="input-quantity"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="input-price"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="select-status"]').exists()).toBe(true)
  })

  it('shows validation error for empty supplier', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('请输入供应商名称')
  })

  it('shows validation error for empty item name', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('[data-testid="input-supplier"]').setValue('供应商A')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('请输入商品名称')
  })

  it('shows validation error for quantity < 1', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('[data-testid="input-supplier"]').setValue('供应商A')
    await wrapper.find('[data-testid="input-item-name"]').setValue('螺丝')
    await wrapper.find('[data-testid="input-quantity"]').setValue(0)
    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('数量至少为1')
  })

  it('shows validation error for negative price', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('[data-testid="input-supplier"]').setValue('供应商A')
    await wrapper.find('[data-testid="input-item-name"]').setValue('螺丝')
    await wrapper.find('[data-testid="input-quantity"]').setValue(1)
    await wrapper.find('[data-testid="input-price"]').setValue(-5)
    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('单价不能为负数')
  })

  it('emits submit with correct data on valid form', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('[data-testid="input-supplier"]').setValue('供应商A')
    await wrapper.find('[data-testid="input-item-name"]').setValue('螺丝')
    await wrapper.find('[data-testid="input-quantity"]').setValue(10)
    await wrapper.find('[data-testid="input-price"]').setValue(5)
    await wrapper.find('[data-testid="select-status"]').setValue('confirmed')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('submit')).toBeTruthy()
    const payload = wrapper.emitted('submit')[0][0]
    expect(payload.supplierName).toBe('供应商A')
    expect(payload.items[0]).toEqual({ name: '螺丝', quantity: 10, unitPrice: 5 })
    expect(payload.status).toBe('confirmed')
  })

  it('emits close when cancel clicked', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('.btn-cancel').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('emits close when overlay clicked', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('.dialog-overlay').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('does not close when dialog content clicked', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('.dialog').trigger('click')
    expect(wrapper.emitted('close')).toBeFalsy()
  })

  it('trims whitespace from supplier name', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('[data-testid="input-supplier"]').setValue('  供应商A  ')
    await wrapper.find('[data-testid="input-item-name"]').setValue('螺丝')
    await wrapper.find('[data-testid="input-quantity"]').setValue(1)
    await wrapper.find('[data-testid="input-price"]').setValue(0)
    await wrapper.find('form').trigger('submit')

    const payload = wrapper.emitted('submit')[0][0]
    expect(payload.supplierName).toBe('供应商A')
  })

  it('trims whitespace from item name', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('[data-testid="input-supplier"]').setValue('供应商A')
    await wrapper.find('[data-testid="input-item-name"]').setValue('  螺丝  ')
    await wrapper.find('[data-testid="input-quantity"]').setValue(1)
    await wrapper.find('[data-testid="input-price"]').setValue(0)
    await wrapper.find('form').trigger('submit')

    const payload = wrapper.emitted('submit')[0][0]
    expect(payload.items[0].name).toBe('螺丝')
  })

  it('has default status pending', () => {
    const wrapper = mount(AddOrderDialog)
    const select = wrapper.find('[data-testid="select-status"]')
    expect(select.element.value).toBe('pending')
  })

  it('renders all status options', () => {
    const wrapper = mount(AddOrderDialog)
    const options = wrapper.findAll('option')
    expect(options).toHaveLength(5)
    const texts = options.map((o) => o.text())
    expect(texts).toContain('待处理')
    expect(texts).toContain('已确认')
    expect(texts).toContain('已发货')
    expect(texts).toContain('已收货')
    expect(texts).toContain('已取消')
  })

  it('converts quantity and price to numbers', async () => {
    const wrapper = mount(AddOrderDialog)
    await wrapper.find('[data-testid="input-supplier"]').setValue('供应商A')
    await wrapper.find('[data-testid="input-item-name"]').setValue('螺丝')
    await wrapper.find('[data-testid="input-quantity"]').setValue('10')
    await wrapper.find('[data-testid="input-price"]').setValue('5.5')
    await wrapper.find('form').trigger('submit')

    const payload = wrapper.emitted('submit')[0][0]
    expect(typeof payload.items[0].quantity).toBe('number')
    expect(typeof payload.items[0].unitPrice).toBe('number')
    expect(payload.items[0].unitPrice).toBe(5.5)
  })
})
