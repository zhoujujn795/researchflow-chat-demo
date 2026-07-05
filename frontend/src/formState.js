export function validateAnalyzeForm({ paperFile, researchTopic, extractMetrics }) {
  if (!paperFile) {
    return 'paper_files 必填：请上传一篇 PDF 论文。'
  }

  if (!paperFile.name?.toLowerCase().endsWith('.pdf')) {
    return 'paper_files 只支持 PDF 文件。'
  }

  if (!researchTopic?.trim()) {
    return 'research_topic 必填：请填写研究主题。'
  }

  if (!extractMetrics?.trim()) {
    return 'extract_metrics 必填：请填写希望提取的指标。'
  }

  return ''
}

export function normalizeApiErrorMessage(message) {
  if (!message) {
    return '分析请求失败。'
  }

  if (message.includes('paper_files is required')) {
    return 'paper_files 必填：Dify 没收到论文文件变量。请确认已上传 PDF，并重新部署 GitHub main 分支上的最新后端代码。'
  }

  if (message.includes('Dify 对话接口超时') || message.includes('请求超时')) {
    return 'Dify 工作流处理超时：文件字段 paper_files 已提交，但阻塞式请求没有在等待时间内拿到报告。请换短一点的 PDF，或在 Vercel/DIFY_TIMEOUT 中提高等待时间。'
  }

  return message
}
