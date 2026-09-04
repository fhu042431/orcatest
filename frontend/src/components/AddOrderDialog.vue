<script setup>
import { ref } from 'vue'

const emit = defineEmits(['close', 'submit'])

const supplierName = ref('')
const itemName = ref('')
const itemQuantity = ref(1)
const itemPrice = ref(0)
const status = ref('pending')
const errors = ref({})

const statusOptions = [
  { value: 'pending', label: '待处理' },
  { value: 'confirmed', label: '已确认' },
  { value: 'shipped', label: '已发货' },
  { value: 'received', label: '已收货' },
  { value: 'cancelled', label: '已取消' },
]

function validate() {
  errors.value = {}
  if (!supplierName.value.trim()) {
    errors.value.supplierName = '请输入供应商名称'
  }
  if (!itemName.value.trim()) {
    errors.value.itemName = '请输入商品名称'
  }
  if (itemQuantity.value < 1) {
    errors.value.itemQuantity = '数量至少为1'
  }
  if (itemPrice.value < 0) {
    errors.value.itemPrice = '单价不能为负数'
  }
  return Object.keys(errors.value).length === 0
}

function handleSubmit() {
  if (!validate()) return
  emit('submit', {
    supplierName: supplierName.value.trim(),
    items: [
      {
        name: itemName.value.trim(),
        quantity: Number(itemQuantity.value),
        unitPrice: Number(itemPrice.value),
      },
    ],
    status: status.value,
  })
}

function handleOverlayClick(e) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}
</script>

<template>
  <div class="dialog-overlay" @click="handleOverlayClick" data-testid="add-order-dialog">
    <div class="dialog">
      <h2>新建采购订单</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>供应商名称</label>
          <input v-model="supplierName" placeholder="请输入供应商名称" data-testid="input-supplier" />
          <span v-if="errors.supplierName" class="error">{{ errors.supplierName }}</span>
        </div>
        <div class="form-group">
          <label>商品名称</label>
          <input v-model="itemName" placeholder="请输入商品名称" data-testid="input-item-name" />
          <span v-if="errors.itemName" class="error">{{ errors.itemName }}</span>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>数量</label>
            <input v-model.number="itemQuantity" type="number" min="1" data-testid="input-quantity" />
            <span v-if="errors.itemQuantity" class="error">{{ errors.itemQuantity }}</span>
          </div>
          <div class="form-group">
            <label>单价</label>
            <input v-model.number="itemPrice" type="number" min="0" step="0.01" data-testid="input-price" />
            <span v-if="errors.itemPrice" class="error">{{ errors.itemPrice }}</span>
          </div>
        </div>
        <div class="form-group">
          <label>状态</label>
          <select v-model="status" data-testid="select-status">
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
        <div class="dialog-actions">
          <button type="button" class="btn-cancel" @click="emit('close')">取消</button>
          <button type="submit" class="btn-submit">确认</button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.dialog {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  width: 420px;
  max-width: 90vw;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.dialog h2 {
  margin: 0 0 20px;
  font-size: 18px;
  color: #1f2937;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 4px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-row .form-group {
  flex: 1;
}

.error {
  color: #ef4444;
  font-size: 12px;
  margin-top: 2px;
  display: block;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn-cancel {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-submit {
  background: #3b82f6;
  color: #fff;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.btn-submit:hover {
  background: #2563eb;
}
</style>
