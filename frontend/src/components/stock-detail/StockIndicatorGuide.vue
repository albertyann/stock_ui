<template>
  <el-card class="mt-20 indicator-guide-card">
    <template #header>
      <div class="card-header">
        <span>指标说明</span>
        <el-tag type="success" size="small">真突破（可关注）</el-tag>
      </div>
    </template>

    <div class="indicator-guide">
      <div class="guide-feature">
        均线多头，MACD金叉，大单流入，OBV新高，ADX走强
      </div>

      <div class="guide-section">
        <div class="guide-title">MA (5,10,20)</div>
        <div class="guide-text">5&gt;10&gt;20，股价沿5日线攀升。</div>
      </div>

      <div class="guide-section">
        <div class="guide-title">MACD</div>
        <div class="guide-text">DIF上穿DEA，红柱渐长，在零轴上方二次金叉。</div>
      </div>

      <div class="guide-section">
        <div class="guide-title">大单/DDX</div>
        <div class="guide-text">连续3日大单净流入，DDX红柱逐日放大（非脉冲）。</div>
      </div>

      <div class="guide-section">
        <div class="guide-title">OBV</div>
        <div class="guide-text">随股价创新高，OBV同步创120日新高。</div>
      </div>

      <div class="guide-section">
        <div class="guide-title">ADX</div>
        <div class="guide-text">从20升至35，+DI在-DI上方。</div>
      </div>

      <el-divider />

      <div class="guide-summary">
        <div class="summary-line">
          <span class="summary-label">综合判断：</span>强趋势+资金健康+量价配合。
        </div>
        <div class="summary-line">
          <span class="summary-label">操作：</span>沿5日线持有，ADX&gt;50且走平考虑减仓。
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
// 纯静态的指标说明卡片
</script>

<style scoped>
.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 指标说明卡片 */
.indicator-guide-card .guide-feature {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 12px;
  padding: 8px 10px;
  background-color: var(--bg-input);
  border-radius: 4px;
}

.indicator-guide-card .guide-section {
  margin-bottom: 10px;
}

.indicator-guide-card .guide-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.indicator-guide-card .guide-text {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.indicator-guide-card .guide-summary {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.8;
}

.indicator-guide-card .summary-line {
  margin-bottom: 4px;
}

.indicator-guide-card .summary-label {
  font-weight: 600;
  color: var(--text-primary);
}
</style>
