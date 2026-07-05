const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '')

async function readJson(response) {
  const text = await response.text()
  if (!text) {
    return {}
  }

  try {
    return JSON.parse(text)
  } catch {
    throw new Error('后端返回了无法解析的响应。')
  }
}

async function request(path, options) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  const data = await readJson(response)

  if (!response.ok || data.ok === false) {
    throw new Error(data.message || `请求失败：HTTP ${response.status}`)
  }

  return data
}

export function analyzePaper({ paperFile, researchTopic, extractMetrics }) {
  const formData = new FormData()
  formData.append('paper_file', paperFile)
  formData.append('research_topic', researchTopic)
  formData.append('extract_metrics', extractMetrics)

  return request('/api/analyze', {
    method: 'POST',
    body: formData
  })
}

export function sendChatMessage({ message, conversationId }) {
  return request('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId
    })
  })
}

