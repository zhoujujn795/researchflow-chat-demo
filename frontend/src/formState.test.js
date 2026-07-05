import assert from 'node:assert/strict'
import test from 'node:test'

import { normalizeApiErrorMessage, validateAnalyzeForm } from './formState.js'

test('requires the Dify paper_files input before analysis', () => {
  const result = validateAnalyzeForm({
    paperFile: null,
    researchTopic: 'PM2.5 趋势分析',
    extractMetrics: 'RMSE、MAE'
  })

  assert.equal(result, 'paper_files 必填：请上传一篇 PDF 论文。')
})

test('requires the Dify research_topic input before analysis', () => {
  const result = validateAnalyzeForm({
    paperFile: { name: 'paper.pdf' },
    researchTopic: '   ',
    extractMetrics: 'RMSE、MAE'
  })

  assert.equal(result, 'research_topic 必填：请填写研究主题。')
})

test('requires the Dify extract_metrics input before analysis', () => {
  const result = validateAnalyzeForm({
    paperFile: { name: 'paper.pdf' },
    researchTopic: 'PM2.5 趋势分析',
    extractMetrics: ''
  })

  assert.equal(result, 'extract_metrics 必填：请填写希望提取的指标。')
})

test('keeps unsupported file type validation tied to paper_files', () => {
  const result = validateAnalyzeForm({
    paperFile: { name: 'paper.docx' },
    researchTopic: 'PM2.5 趋势分析',
    extractMetrics: 'RMSE、MAE'
  })

  assert.equal(result, 'paper_files 只支持 PDF 文件。')
})

test('normalizes Dify timeout into a workflow status message', () => {
  const message = normalizeApiErrorMessage('Dify 对话接口超时，请稍后重试或降低论文长度。')

  assert.equal(
    message,
    'Dify 工作流处理超时：文件字段 paper_files 已提交，但阻塞式请求没有在等待时间内拿到报告。请换短一点的 PDF，或在 Vercel/DIFY_TIMEOUT 中提高等待时间。'
  )
})
