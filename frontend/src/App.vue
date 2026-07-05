<script setup>
import { computed, ref } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import {
  ClipboardCopy,
  FileText,
  LoaderCircle,
  MessageSquareText,
  RotateCcw,
  Send,
  Sparkles,
  UploadCloud
} from 'lucide-vue-next'
import { analyzePaper, sendChatMessage } from './api'
import { normalizeApiErrorMessage, validateAnalyzeForm } from './formState'

const STORAGE_KEY = 'researchflow_conversation_id'

marked.use({
  gfm: true,
  breaks: true
})

const paperFile = ref(null)
const fileName = ref('')
const researchTopic = ref('城市空气质量 PM2.5 变化趋势与影响因素分析')
const extractMetrics = ref('PM2.5、PM10、R²、MAE、RMSE、Pearson 相关系数、特征重要性')
const answer = ref('')
const conversationId = ref(localStorage.getItem(STORAGE_KEY) || '')
const followup = ref('')
const loading = ref(false)
const chatting = ref(false)
const errorMessage = ref('')
const copyState = ref('复制结果')

const renderedAnswer = computed(() => {
  if (!answer.value) {
    return ''
  }

  return DOMPurify.sanitize(marked.parse(answer.value))
})

const canChat = computed(() => Boolean(conversationId.value && !loading.value && !chatting.value))

function onFileChange(event) {
  const [file] = event.target.files || []
  paperFile.value = file || null
  fileName.value = file ? file.name : ''
  errorMessage.value = ''
}

function persistConversation(nextConversationId) {
  conversationId.value = nextConversationId || ''
  if (conversationId.value) {
    localStorage.setItem(STORAGE_KEY, conversationId.value)
  }
}

function applyApiResult(data) {
  answer.value = data.answer || ''
  persistConversation(data.conversation_id || conversationId.value)
}

async function startAnalyze() {
  errorMessage.value = ''
  copyState.value = '复制结果'

  const validationError = validateAnalyzeForm({
    paperFile: paperFile.value,
    researchTopic: researchTopic.value,
    extractMetrics: extractMetrics.value
  })

  if (validationError) {
    errorMessage.value = validationError
    return
  }

  loading.value = true
  answer.value = ''

  try {
    const data = await analyzePaper({
      paperFile: paperFile.value,
      researchTopic: researchTopic.value,
      extractMetrics: extractMetrics.value
    })
    applyApiResult(data)
  } catch (error) {
    errorMessage.value = normalizeApiErrorMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function askFollowup() {
  const message = followup.value.trim()
  if (!message) {
    return
  }

  if (!conversationId.value) {
    errorMessage.value = '请先完成一次论文分析。'
    return
  }

  chatting.value = true
  errorMessage.value = ''

  try {
    const data = await sendChatMessage({
      message,
      conversationId: conversationId.value
    })
    applyApiResult(data)
    followup.value = ''
  } catch (error) {
    errorMessage.value = normalizeApiErrorMessage(error.message || '追问请求失败。')
  } finally {
    chatting.value = false
  }
}

async function copyAnswer() {
  if (!answer.value) {
    return
  }

  await navigator.clipboard.writeText(answer.value)
  copyState.value = '已复制'
  window.setTimeout(() => {
    copyState.value = '复制结果'
  }, 1600)
}

function clearSession() {
  paperFile.value = null
  fileName.value = ''
  answer.value = ''
  followup.value = ''
  errorMessage.value = ''
  conversationId.value = ''
  copyState.value = '复制结果'
  localStorage.removeItem(STORAGE_KEY)
}
</script>

<template>
  <main class="app-shell">
    <div class="console-frame">
      <header class="banner">
        <div class="brand-block">
          <div class="brand-kicker">
            <span class="pulse-dot"></span>
            ResearchFlow Agent Console
          </div>
          <h1>科研文献数据化分析智能体</h1>
          <p>论文 PDF → 指标提取 → 数据集构建 → 科研分析报告</p>
        </div>

        <div class="tag-row" aria-label="技术标签">
          <span>Dify</span>
          <span>MinerU</span>
          <span>AI Agent</span>
          <span>Workflow</span>
        </div>
      </header>

      <section class="workflow-strip" aria-label="工作流">
        <div class="flow-step">
          <FileText :size="18" />
          <span>Paper PDF</span>
        </div>
        <div class="flow-line"></div>
        <div class="flow-step">
          <Sparkles :size="18" />
          <span>Metrics</span>
        </div>
        <div class="flow-line"></div>
        <div class="flow-step">
          <MessageSquareText :size="18" />
          <span>Report</span>
        </div>
      </section>

      <section class="workspace-grid">
        <aside class="panel input-panel">
          <div class="panel-heading">
            <span>Dify 输入表单</span>
            <span class="required-count">3 必填</span>
          </div>

          <div class="input-map" aria-label="Dify 输入字段映射">
            <div class="map-row">
              <code>paper_files</code>
              <span>论文 PDF 文件</span>
              <b>必填</b>
            </div>
            <div class="map-row">
              <code>research_topic</code>
              <span>研究主题</span>
              <b>必填</b>
            </div>
            <div class="map-row">
              <code>extract_metrics</code>
              <span>提取指标</span>
              <b>必填</b>
            </div>
          </div>

          <label class="upload-zone">
            <input type="file" accept="application/pdf,.pdf" @change="onFileChange" />
            <span class="field-label">
              <code>paper_files</code>
              <em>必填</em>
            </span>
            <UploadCloud :size="34" />
            <strong>{{ fileName || '上传论文 PDF' }}</strong>
            <small>对应 Dify 的文件列表变量</small>
          </label>

          <label class="field">
            <span class="field-label">
              <code>research_topic</code>
              <em>必填</em>
            </span>
            <small>研究主题</small>
            <textarea v-model="researchTopic" rows="4" placeholder="例如：城市空气质量 PM2.5 变化趋势与影响因素分析"></textarea>
          </label>

          <label class="field">
            <span class="field-label">
              <code>extract_metrics</code>
              <em>必填</em>
            </span>
            <small>希望提取的指标</small>
            <textarea v-model="extractMetrics" rows="5" placeholder="例如：PM2.5、PM10、R²、MAE、RMSE、Pearson 相关系数"></textarea>
          </label>

          <div class="button-row">
            <button class="primary-button" type="button" :disabled="loading" @click="startAnalyze">
              <LoaderCircle v-if="loading" class="spin" :size="18" />
              <Sparkles v-else :size="18" />
              <span>{{ loading ? '分析中' : '开始分析' }}</span>
            </button>
            <button class="ghost-button" type="button" @click="clearSession">
              <RotateCcw :size="18" />
              <span>清空会话</span>
            </button>
          </div>
        </aside>

        <section class="panel result-panel">
          <div class="panel-heading result-heading">
            <span>分析结果</span>
            <button class="small-button" type="button" :disabled="!answer" @click="copyAnswer">
              <ClipboardCopy :size="16" />
              <span>{{ copyState }}</span>
            </button>
          </div>

          <div v-if="errorMessage" class="error-box">
            <strong>请求未完成</strong>
            <span>{{ errorMessage }}</span>
          </div>

          <div v-if="loading" class="loading-state">
            <LoaderCircle class="spin" :size="34" />
            <strong>Dify 工作流处理中</strong>
            <span>已提交 paper_files，正在等待报告返回</span>
          </div>

          <article v-else-if="answer" class="markdown-body" v-html="renderedAnswer"></article>

          <div v-else class="empty-state">
            <FileText :size="42" />
            <strong>等待论文分析</strong>
            <span>结果会在这里以 Markdown 报告形式呈现</span>
          </div>

          <div class="conversation-bar">
            <span>conversation_id</span>
            <code>{{ conversationId || '尚未建立会话' }}</code>
          </div>
        </section>
      </section>

      <footer class="followup-panel">
        <div class="followup-input">
          <MessageSquareText :size="20" />
          <input
            v-model="followup"
            :disabled="!canChat"
            type="text"
            placeholder="继续追问：帮我生成研究空白、横向对比表或汇报稿"
            @keyup.enter="askFollowup"
          />
        </div>
        <button class="primary-button send-button" type="button" :disabled="!canChat || chatting" @click="askFollowup">
          <LoaderCircle v-if="chatting" class="spin" :size="18" />
          <Send v-else :size="18" />
          <span>{{ chatting ? '发送中' : '发送' }}</span>
        </button>
      </footer>
    </div>
  </main>
</template>
