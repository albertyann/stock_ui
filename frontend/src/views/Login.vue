<template>
  <div class="login-page">
    <div class="brand-panel">
      <div class="mesh-gradient"></div>
      <div class="grid-overlay"></div>
      <div class="market-lines" aria-hidden="true">
        <svg viewBox="0 0 800 400" preserveAspectRatio="none">
          <path
            d="M0,320 C120,300 180,220 260,240 S400,160 520,200 S680,120 800,80"
            class="market-line line-1"
          />
          <path
            d="M0,360 C140,340 200,280 300,300 S440,200 580,240 S720,160 800,140"
            class="market-line line-2"
          />
          <path
            d="M0,280 C100,260 160,180 240,200 S380,100 500,140 S660,60 800,40"
            class="market-line line-3"
          />
        </svg>
      </div>
      <div class="particles" aria-hidden="true">
        <span v-for="n in 18" :key="n" class="particle" :style="particleStyle(n)"></span>
      </div>

      <div class="brand-content">
        <div class="brand-badge">
          <svg viewBox="0 0 48 48" class="brand-logo">
            <path
              d="M6 36 L18 24 L26 32 L42 12 L42 18 L26 38 L18 30 L10 38 Z"
              fill="currentColor"
            />
            <circle cx="38" cy="12" r="4" fill="currentColor" opacity="0.35" />
          </svg>
          <span class="brand-name">小麦国度</span>
        </div>
        <h1 class="brand-headline">
          洞察 A 股脉搏
          <br />
          <span class="accent-text">掌控每一次起落</span>
        </h1>
        <p class="brand-subtitle">
          为严肃投资者打造的市场观察工具。实时数据、多维信号、清晰决策。
        </p>
        <div class="brand-stats">
          <div class="stat-item">
            <span class="stat-value">A 股</span>
            <span class="stat-label">全市场覆盖</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">实时</span>
            <span class="stat-label">行情与信号</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">安全</span>
            <span class="stat-label">TOTP 验证</span>
          </div>
        </div>
      </div>
    </div>

    <div class="form-panel">
      <div class="form-card">
        <div class="form-header">
          <div class="tab-switcher">
            <button
              type="button"
              class="tab-button"
              :class="{ active: panel === 'login' }"
              @click="switchPanel('login')"
            >
              登录
            </button>
            <button
              type="button"
              class="tab-button"
              :class="{ active: panel === 'enroll' }"
              @click="switchPanel('enroll')"
            >
              首次绑定
            </button>
            <span class="tab-slider" :class="panel === 'enroll' ? 'right' : 'left'"></span>
          </div>
        </div>

        <div class="form-body">
          <div v-if="panel === 'login'" class="panel-section">
            <h2 class="form-title">欢迎回来</h2>
            <p class="form-hint">请输入手机号与 Authenticator 生成的 6 位动态码</p>

            <form class="form-stack" @submit.prevent="handleLogin">
              <div class="field-group">
                <label class="field-label" for="login-phone">手机号</label>
                <div class="input-wrap" :class="{ error: errors.phone }">
                  <input
                    id="login-phone"
                    v-model="loginForm.phone"
                    type="tel"
                    inputmode="tel"
                    autocomplete="tel"
                    placeholder="请输入手机号"
                    maxlength="11"
                    @input="clearError('phone')"
                  />
                </div>
                <p v-if="errors.phone" class="field-error">{{ errors.phone }}</p>
              </div>

              <div class="field-group">
                <label class="field-label">TOTP 动态码</label>
                <OtpInput v-model="loginForm.totp_code" :error="!!errors.totp_code" />
                <p v-if="errors.totp_code" class="field-error">{{ errors.totp_code }}</p>
              </div>

              <button
                type="submit"
                class="submit-button"
                :disabled="logining"
                :class="{ loading: logining }"
              >
                <span class="btn-text">{{ logining ? '登录中…' : '立即登录' }}</span>
                <span class="btn-glow"></span>
              </button>
            </form>

            <div class="divider"><span>或使用以下方式</span></div>

            <div class="social-login">
              <button
                type="button"
                class="social-button"
                aria-label="GitHub 登录"
                @click="handleSocialLogin"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                  />
                </svg>
              </button>
              <button
                type="button"
                class="social-button"
                aria-label="Google 登录"
                @click="handleSocialLogin"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
              </button>
              <button
                type="button"
                class="social-button"
                aria-label="微信登录"
                @click="handleSocialLogin"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 01-1.162 1.178A1.17 1.17 0 014.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 01-1.162 1.178 1.17 1.17 0 01-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 01.598.082l1.584.926a.272.272 0 00.14.045c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.49.49 0 01.177-.554C23.016 18.115 24 16.405 24 14.479c0-3.197-3.098-5.621-7.062-5.621zm-2.36 2.63c.535 0 .969.44.969.982a.976.976 0 01-.969.983.976.976 0 01-.969-.983c0-.542.434-.982.97-.982zm4.72 0c.535 0 .969.44.969.982a.976.976 0 01-.969.983.976.976 0 01-.969-.983c0-.542.434-.982.969-.982z"
                    fill="#07C160"
                  />
                </svg>
              </button>
            </div>
          </div>

          <div v-else class="panel-section">
            <template v-if="enrollStep === 1">
              <h2 class="form-title">首次绑定</h2>
              <p class="form-hint">输入手机号与邀请码，开启 TOTP 安全验证</p>

              <form class="form-stack" @submit.prevent="handleEnroll">
                <div class="field-group">
                  <label class="field-label" for="enroll-phone">手机号</label>
                  <div class="input-wrap" :class="{ error: errors.enrollPhone }">
                    <input
                      id="enroll-phone"
                      v-model="enrollForm.phone"
                      type="tel"
                      inputmode="tel"
                      autocomplete="tel"
                      placeholder="请输入手机号"
                      maxlength="11"
                      @input="clearError('enrollPhone')"
                    />
                  </div>
                  <p v-if="errors.enrollPhone" class="field-error">{{ errors.enrollPhone }}</p>
                </div>

                <div class="field-group">
                  <label class="field-label" for="enroll-invitation">邀请码</label>
                  <div class="input-wrap" :class="{ error: errors.invitation_code }">
                    <input
                      id="enroll-invitation"
                      v-model="enrollForm.invitation_code"
                      type="text"
                      autocomplete="off"
                      placeholder="请输入邀请码"
                      @input="clearError('invitation_code')"
                    />
                  </div>
                  <p v-if="errors.invitation_code" class="field-error">
                    {{ errors.invitation_code }}
                  </p>
                </div>

                <button
                  type="submit"
                  class="submit-button"
                  :disabled="enrolling"
                  :class="{ loading: enrolling }"
                >
                  <span class="btn-text">{{ enrolling ? '提交中…' : '提交绑定申请' }}</span>
                  <span class="btn-glow"></span>
                </button>
              </form>
            </template>

            <template v-else-if="enrollStep === 2">
              <h2 class="form-title">验证身份</h2>
              <p class="form-hint">使用 Authenticator 扫描二维码完成绑定</p>

              <div class="qr-wrapper">
                <img :src="qrCodeDataUri" alt="TOTP 二维码" class="qr-image" />
                <div class="qr-scan-line"></div>
              </div>

              <div class="secret-block">
                <span class="secret-label">无法扫码？手动输入密钥</span>
                <div class="secret-value" @click="copySecret">
                  <span>{{ enrollSecret }}</span>
                  <svg viewBox="0 0 24 24" class="copy-icon" aria-hidden="true">
                    <path
                      d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"
                    />
                  </svg>
                </div>
              </div>

              <form class="form-stack" @submit.prevent="handleEnrollConfirm">
                <div class="field-group">
                  <label class="field-label">输入 6 位动态码确认</label>
                  <OtpInput v-model="confirmForm.totp_code" :error="!!errors.confirmTotp" />
                  <p v-if="errors.confirmTotp" class="field-error">{{ errors.confirmTotp }}</p>
                </div>

                <button
                  type="submit"
                  class="submit-button"
                  :disabled="confirming"
                  :class="{ loading: confirming }"
                >
                  <span class="btn-text">{{ confirming ? '确认中…' : '完成绑定' }}</span>
                  <span class="btn-glow"></span>
                </button>
              </form>
            </template>
          </div>
        </div>
      </div>

      <p class="copyright">© 2025 小麦国度 · 专注 A 股市场观察</p>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import OtpInput from '@/components/OtpInput.vue'

export default {
  name: 'LoginView',
  components: { OtpInput },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const authStore = useAuthStore()

    const panel = ref('login')
    const logining = ref(false)
    const enrolling = ref(false)
    const confirming = ref(false)

    const loginForm = reactive({ phone: '', totp_code: '' })
    const enrollForm = reactive({ phone: '', invitation_code: '' })
    const confirmForm = reactive({ totp_code: '' })

    const errors = reactive({
      phone: '',
      totp_code: '',
      enrollPhone: '',
      invitation_code: '',
      confirmTotp: '',
    })

    const enrollStep = ref(1)
    const pendingToken = ref('')
    const qrCodeDataUri = ref('')
    const enrollSecret = ref('')

    const switchPanel = (target) => {
      panel.value = target
      clearAllErrors()
      if (target === 'enroll') {
        enrollStep.value = 1
        enrollForm.phone = ''
        enrollForm.invitation_code = ''
        confirmForm.totp_code = ''
        pendingToken.value = ''
        qrCodeDataUri.value = ''
        enrollSecret.value = ''
      } else {
        loginForm.phone = ''
        loginForm.totp_code = ''
      }
    }

    const clearError = (key) => {
      errors[key] = ''
    }

    const clearAllErrors = () => {
      errors.phone = ''
      errors.totp_code = ''
      errors.enrollPhone = ''
      errors.invitation_code = ''
      errors.confirmTotp = ''
    }

    const validatePhone = (phone) => {
      if (!phone) return '请输入手机号'
      if (!/^1\d{10}$/.test(phone)) return '请输入有效的 11 位手机号'
      return ''
    }

    const validateTotp = (code) => {
      if (!code) return '请输入 6 位动态码'
      if (!/^\d{6}$/.test(code)) return '动态码必须为 6 位数字'
      return ''
    }

    const handleLogin = async () => {
      clearAllErrors()
      errors.phone = validatePhone(loginForm.phone)
      errors.totp_code = validateTotp(loginForm.totp_code)
      if (errors.phone || errors.totp_code) return

      logining.value = true
      try {
        const res = await authApi.login(loginForm.phone, loginForm.totp_code)
        authStore.user = res.data
        ElMessage.success('登录成功')
        const redirect = route.query.redirect
        router.push(typeof redirect === 'string' ? redirect : '/')
      } catch (err) {
        ElMessage.error(err.response?.data?.detail || '登录失败')
      } finally {
        logining.value = false
      }
    }

    const handleEnroll = async () => {
      clearAllErrors()
      errors.enrollPhone = validatePhone(enrollForm.phone)
      if (!enrollForm.invitation_code) {
        errors.invitation_code = '请输入邀请码'
      }
      if (errors.enrollPhone || errors.invitation_code) return

      enrolling.value = true
      try {
        const res = await authApi.enroll(enrollForm.phone, enrollForm.invitation_code)
        pendingToken.value = res.data.pending_token
        qrCodeDataUri.value = res.data.qr_code_data_uri
        enrollSecret.value = res.data.secret
        enrollStep.value = 2
        ElMessage.success('请使用 Authenticator 扫描下方二维码')
      } catch (err) {
        ElMessage.error(err.response?.data?.detail || '绑定申请失败')
      } finally {
        enrolling.value = false
      }
    }

    const handleEnrollConfirm = async () => {
      clearAllErrors()
      errors.confirmTotp = validateTotp(confirmForm.totp_code)
      if (errors.confirmTotp) return

      confirming.value = true
      try {
        const res = await authApi.enrollConfirm(pendingToken.value, confirmForm.totp_code)
        authStore.user = res.data
        ElMessage.success('绑定成功')
        const redirect = route.query.redirect
        router.push(typeof redirect === 'string' ? redirect : '/')
      } catch (err) {
        ElMessage.error(err.response?.data?.detail || '验证失败，请重试')
      } finally {
        confirming.value = false
      }
    }

    const handleSocialLogin = () => {
      ElMessage.info('第三方登录暂未开通，请使用动态码登录')
    }

    const copySecret = async () => {
      if (!enrollSecret.value) return
      try {
        await navigator.clipboard.writeText(enrollSecret.value)
        ElMessage.success('密钥已复制')
      } catch {
        ElMessage.error('复制失败，请手动选择复制')
      }
    }

    const particleStyle = (n) => {
      const top = `${(n * 37) % 100}%`
      const left = `${(n * 53) % 100}%`
      const delay = `${(n * 0.7) % 5}s`
      const duration = `${5 + (n % 4)}s`
      const size = `${2 + (n % 4)}px`
      return {
        top,
        left,
        animationDelay: delay,
        animationDuration: duration,
        width: size,
        height: size,
      }
    }

    return {
      panel,
      logining,
      enrolling,
      confirming,
      loginForm,
      enrollForm,
      confirmForm,
      errors,
      enrollStep,
      pendingToken,
      qrCodeDataUri,
      enrollSecret,
      switchPanel,
      clearError,
      handleLogin,
      handleEnroll,
      handleEnrollConfirm,
      handleSocialLogin,
      copySecret,
      particleStyle,
    }
  },
}
</script>

<style scoped>
.login-page {
  --bg-deep: #070b14;
  --bg-panel: #0b1021;
  --bg-card: rgba(15, 22, 41, 0.72);
  --bg-card-solid: #0f1629;
  --bg-elevated: #131c33;
  --bg-input: rgba(2, 6, 23, 0.45);
  --bg-hover: rgba(16, 185, 129, 0.08);
  --bg-active: rgba(16, 185, 129, 0.14);
  --border-subtle: rgba(148, 163, 184, 0.12);
  --border-active: rgba(16, 185, 129, 0.45);
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent: #10b981;
  --accent-glow: rgba(16, 185, 129, 0.35);
  --accent-cyan: #06b6d4;
  --danger: #ef4444;
  --radius-sm: 10px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --shadow-card: 0 24px 80px rgba(0, 0, 0, 0.35);
  --shadow-glow: 0 0 0 3px rgba(16, 185, 129, 0.12);

  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  background: var(--bg-deep);
  color: var(--text-primary);
  font-family: var(--font-body);
  overflow: hidden;
}

.brand-panel {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 64px;
  overflow: hidden;
  background:
    radial-gradient(circle at 20% 30%, rgba(16, 185, 129, 0.12), transparent 45%),
    radial-gradient(circle at 80% 70%, rgba(6, 182, 212, 0.1), transparent 45%),
    linear-gradient(135deg, #0a0f1d 0%, #070b14 100%);
}

.mesh-gradient {
  position: absolute;
  inset: 0;
  opacity: 0.6;
  background:
    radial-gradient(at 15% 25%, rgba(16, 185, 129, 0.22) 0px, transparent 45%),
    radial-gradient(at 85% 15%, rgba(6, 182, 212, 0.18) 0px, transparent 40%),
    radial-gradient(at 50% 85%, rgba(16, 185, 129, 0.12) 0px, transparent 45%);
  filter: blur(40px);
  animation: meshFlow 16s ease-in-out infinite alternate;
}

@keyframes meshFlow {
  0% {
    transform: scale(1) translate(0, 0);
  }
  100% {
    transform: scale(1.08) translate(-2%, 2%);
  }
}

.grid-overlay {
  position: absolute;
  inset: 0;
  opacity: 0.08;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.4) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.4) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(to bottom, black, transparent 80%);
}

.market-lines {
  position: absolute;
  inset: 0;
  opacity: 0.35;
}

.market-lines svg {
  width: 100%;
  height: 100%;
}

.market-line {
  fill: none;
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-dasharray: 1200;
  stroke-dashoffset: 1200;
  animation: drawLine 3.5s ease-out forwards;
}

.line-1 {
  stroke: var(--accent);
}
.line-2 {
  stroke: var(--accent-cyan);
  animation-delay: 0.4s;
}
.line-3 {
  stroke: rgba(16, 185, 129, 0.55);
  animation-delay: 0.8s;
}

@keyframes drawLine {
  to {
    stroke-dashoffset: 0;
  }
}

.particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  border-radius: 50%;
  background: var(--accent);
  opacity: 0;
  filter: blur(1px);
  animation: floatParticle 6s ease-in-out infinite;
}

@keyframes floatParticle {
  0%,
  100% {
    opacity: 0;
    transform: translateY(0) scale(0.6);
  }
  25% {
    opacity: 0.55;
  }
  50% {
    opacity: 0.25;
    transform: translateY(-40px) scale(1);
  }
  75% {
    opacity: 0.5;
  }
}

.brand-content {
  position: relative;
  z-index: 2;
  max-width: 520px;
  animation: fadeUp 0.8s ease-out both;
}

.brand-badge {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 10px 18px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid var(--border-subtle);
  margin-bottom: 40px;
  backdrop-filter: blur(8px);
}

.brand-logo {
  width: 28px;
  height: 28px;
  color: var(--accent);
}

.brand-name {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 0.5px;
}

.brand-headline {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 52px;
  line-height: 1.15;
  margin: 0 0 20px 0;
  letter-spacing: -0.02em;
}

.accent-text {
  color: var(--accent);
  text-shadow: 0 0 40px var(--accent-glow);
}

.brand-subtitle {
  color: var(--text-secondary);
  font-size: 17px;
  line-height: 1.7;
  margin: 0 0 48px 0;
  max-width: 420px;
}

.brand-stats {
  display: flex;
  gap: 40px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-value {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 22px;
  color: var(--text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.form-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: var(--bg-panel);
  overflow-y: auto;
}

.form-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 70% 20%, rgba(16, 185, 129, 0.08), transparent 35%),
    radial-gradient(circle at 30% 80%, rgba(6, 182, 212, 0.06), transparent 35%);
  pointer-events: none;
}

.form-card {
  position: relative;
  width: 100%;
  max-width: 440px;
  padding: 40px;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
  animation: cardIn 0.9s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.form-header {
  margin-bottom: 28px;
}

.tab-switcher {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 4px;
  border-radius: var(--radius-sm);
  background: rgba(2, 6, 23, 0.5);
  border: 1px solid var(--border-subtle);
}

.tab-button {
  position: relative;
  z-index: 1;
  padding: 12px 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: color var(--transition-fast);
  font-family: var(--font-body);
}

.tab-button.active {
  color: var(--text-primary);
}

.tab-slider {
  position: absolute;
  top: 4px;
  bottom: 4px;
  width: calc(50% - 4px);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.18), rgba(6, 182, 212, 0.12));
  border: 1px solid rgba(16, 185, 129, 0.25);
  transition: transform var(--transition-base);
}

.tab-slider.left {
  left: 4px;
  transform: translateX(0);
}

.tab-slider.right {
  left: 4px;
  transform: translateX(100%);
}

.form-body {
  animation: fadeUp 0.7s ease-out 0.15s both;
}

.form-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 8px 0;
}

.form-hint {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0 0 28px 0;
}

.form-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.3px;
}

.input-wrap {
  position: relative;
  border-radius: var(--radius-sm);
  background: rgba(2, 6, 23, 0.45);
  border: 1px solid var(--border-subtle);
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.input-wrap:focus-within {
  border-color: var(--border-active);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.12);
}

.input-wrap.error {
  border-color: rgba(239, 68, 68, 0.55);
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.input-wrap input {
  width: 100%;
  padding: 14px 16px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 15px;
  outline: none;
  font-family: var(--font-body);
}

.input-wrap input::placeholder {
  color: var(--text-muted);
}

.field-error {
  margin: 0;
  font-size: 12px;
  color: var(--danger);
  animation: shakeIn 0.3s ease;
}

@keyframes shakeIn {
  from {
    opacity: 0;
    transform: translateX(-4px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.submit-button {
  position: relative;
  width: 100%;
  padding: 15px 24px;
  margin-top: 6px;
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--accent), #059669);
  color: #020617;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
  overflow: hidden;
  font-family: var(--font-body);
  transition:
    transform var(--transition-fast),
    box-shadow var(--transition-fast);
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(16, 185, 129, 0.28);
}

.submit-button:active:not(:disabled) {
  transform: translateY(0);
}

.submit-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    110deg,
    transparent 25%,
    rgba(255, 255, 255, 0.22) 45%,
    transparent 55%
  );
  transform: translateX(-120%);
  transition: transform 0s;
}

.submit-button:hover:not(:disabled) .btn-glow {
  transform: translateX(120%);
  transition: transform 0.7s ease;
}

.divider {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 28px 0 22px 0;
  color: var(--text-muted);
  font-size: 13px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-subtle);
}

.social-login {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.social-button {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
  background: rgba(2, 6, 23, 0.4);
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    transform var(--transition-fast),
    background var(--transition-fast);
}

.social-button:hover {
  border-color: var(--border-active);
  background: rgba(16, 185, 129, 0.08);
  transform: translateY(-2px);
}

.social-button svg {
  width: 22px;
  height: 22px;
}

.qr-wrapper {
  position: relative;
  width: 180px;
  height: 180px;
  margin: 0 auto 20px auto;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  background: #ffffff;
  padding: 10px;
}

.qr-image {
  width: 100%;
  height: 100%;
  display: block;
}

.qr-scan-line {
  position: absolute;
  left: 10px;
  right: 10px;
  top: 10px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  box-shadow: 0 0 12px var(--accent-glow);
  animation: scanLine 2.2s ease-in-out infinite;
}

@keyframes scanLine {
  0%,
  100% {
    top: 10px;
    opacity: 0;
  }
  15% {
    opacity: 1;
  }
  85% {
    opacity: 1;
  }
  50% {
    top: calc(100% - 12px);
  }
}

.secret-block {
  margin-bottom: 20px;
  padding: 14px;
  border-radius: var(--radius-sm);
  background: rgba(2, 6, 23, 0.45);
  border: 1px solid var(--border-subtle);
}

.secret-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.secret-value {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  color: var(--accent);
  word-break: break-all;
  cursor: pointer;
  user-select: all;
}

.copy-icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  fill: var(--text-muted);
  transition: fill var(--transition-fast);
}

.secret-value:hover .copy-icon {
  fill: var(--accent);
}

.copyright {
  position: relative;
  margin-top: 28px;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 992px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    display: none;
  }

  .form-panel {
    min-height: 100vh;
    padding: 32px 24px;
  }

  .form-card {
    padding: 28px;
  }
}

@media (max-width: 480px) {
  .brand-headline {
    font-size: 36px;
  }
}
</style>
