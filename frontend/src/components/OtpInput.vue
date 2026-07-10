<template>
  <div class="otp-row">
    <input
      v-for="(digit, index) in digits"
      :key="index"
      :ref="(el) => { if (el) inputs[index] = el }"
      v-model="digits[index]"
      type="text"
      inputmode="numeric"
      maxlength="1"
      class="otp-cell"
      :class="{ error: error }"
      @input="onInput(index, $event)"
      @keydown="onKeydown(index, $event)"
      @paste="onPaste"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  error: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const digits = ref(Array(6).fill(''))
const inputs = ref([])

const syncFromProp = () => {
  const chars = (props.modelValue || '').split('').slice(0, 6)
  digits.value = Array(6)
    .fill('')
    .map((_, i) => chars[i] || '')
}

const updateModel = () => {
  emit('update:modelValue', digits.value.join(''))
}

const focusInput = (index) => {
  const el = inputs.value[index]
  if (el) el.focus()
}

const onInput = (index, event) => {
  const val = event.target.value.replace(/\D/g, '')
  const char = val.slice(-1)
  digits.value[index] = char
  updateModel()
  if (char && index < 5) {
    focusInput(index + 1)
  }
}

const onKeydown = (index, event) => {
  if (event.key === 'Backspace') {
    if (!digits.value[index] && index > 0) {
      digits.value[index - 1] = ''
      updateModel()
      focusInput(index - 1)
    }
  } else if (event.key === 'ArrowLeft' && index > 0) {
    focusInput(index - 1)
  } else if (event.key === 'ArrowRight' && index < 5) {
    focusInput(index + 1)
  }
}

const onPaste = (event) => {
  event.preventDefault()
  const text = (event.clipboardData || window.clipboardData).getData('text')
  const cleaned = text.replace(/\D/g, '').slice(0, 6)
  cleaned.split('').forEach((char, i) => {
    digits.value[i] = char
  })
  updateModel()
  focusInput(Math.min(cleaned.length, 5))
}

watch(() => props.modelValue, syncFromProp, { immediate: true })
</script>

<style scoped>
.otp-row {
  display: flex;
  gap: 10px;
  justify-content: space-between;
}

.otp-cell {
  width: 100%;
  aspect-ratio: 1;
  min-width: 0;
  text-align: center;
  padding: 0;
  border-radius: var(--radius-sm, 10px);
  background: rgba(2, 6, 23, 0.45);
  border: 1px solid var(--border-subtle, rgba(148, 163, 184, 0.12));
  color: var(--text-primary, #f8fafc);
  font-size: 20px;
  font-weight: 600;
  font-family: var(--font-display, 'Sora', sans-serif);
  outline: none;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
}

.otp-cell:focus {
  border-color: var(--border-active, rgba(16, 185, 129, 0.45));
  box-shadow: 0 0 18px var(--accent-glow, rgba(16, 185, 129, 0.35));
  transform: translateY(-2px);
}

.otp-cell.error {
  border-color: rgba(239, 68, 68, 0.55);
}

@media (max-width: 480px) {
  .otp-row {
    gap: 8px;
  }

  .otp-cell {
    font-size: 18px;
  }
}
</style>
