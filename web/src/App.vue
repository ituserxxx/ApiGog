<template>
  <div id="app">
    <header>
      <h1>ApiGog</h1>
      <p>API测试工具</p>
    </header>
    <main>
      <div class="status card">
        <h2>系统状态</h2>
        <p v-if="status">{{ status.message }}</p>
        <p v-else>连接中...</p>
      </div>

      <div class="panel card">
        <h2>API 测试</h2>
        <div class="form-grid">
          <div class="field">
            <label>URL 地址（可本地/公网）</label>
            <input v-model="baseUrl" type="text" placeholder="例如：http://localhost:5000" />
          </div>

          <div class="field">
            <label>接口路由</label>
            <input v-model="apiPath" type="text" placeholder="例如：/api/health" />
          </div>

          <div class="field">
            <label>请求方法</label>
            <select v-model="method">
              <option value="GET">GET</option>
              <option value="POST">POST</option>
            </select>
          </div>

          <div class="field span-2">
            <label>Header（JSON）</label>
            <textarea v-model="headersJson" rows="4" placeholder='例如：{"Authorization":"Bearer xxx"}'></textarea>
          </div>

          <div class="field" v-if="method === 'GET'">
            <label>GET 参数（JSON）</label>
            <textarea v-model="getParamsJson" rows="4" placeholder='例如：{"q":"test"}'></textarea>
          </div>

          <div class="field" v-if="method === 'POST'">
            <label>POST 参数（JSON）</label>
            <textarea v-model="postParamsJson" rows="4" placeholder='例如：{"name":"tom"}'></textarea>
          </div>
        </div>

        <div class="actions">
          <button class="primary" :disabled="loading" @click="sendRequest">
            {{ loading ? '请求中...' : '发送请求' }}
          </button>
          <div class="hint" v-if="errorText">{{ errorText }}</div>
        </div>

        <div class="response">
          <div class="response-head">
            <div><b>响应状态：</b>{{ responseStatusText }}</div>
            <div class="muted" v-if="elapsedMs !== null"><b>耗时：</b>{{ elapsedMs }} ms</div>
          </div>
          <pre class="response-body" v-if="prettyResponse">{{ prettyResponse }}</pre>
          <div class="muted" v-else>暂无响应</div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const status = ref(null)
const baseUrl = ref('http://localhost:5000')
const apiPath = ref('/api/health')
const method = ref('GET')

const headersJson = ref('{}')
const getParamsJson = ref('{}')
const postParamsJson = ref('{}')

const loading = ref(false)
const errorText = ref('')

const responseStatusText = ref('')
const elapsedMs = ref(null)
const prettyResponse = ref('')

function joinUrl(base, path) {
  if (!base) return path || ''
  if (!path) return base

  const hasSlashAtEnd = base.endsWith('/')
  const hasSlashAtStart = path.startsWith('/')
  if (hasSlashAtEnd && hasSlashAtStart) return base + path.slice(1)
  if (!hasSlashAtEnd && !hasSlashAtStart) return base + '/' + path
  return base + path
}

function parseJsonOrThrow(text, label) {
  const raw = String(text ?? '').trim()
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw)
    return parsed
  } catch (e) {
    throw new Error(`${label} JSON 格式不正确：${e?.message || e}`)
  }
}

function prettyPrint(data) {
  if (data === undefined) return ''
  if (data === null) return 'null'

  if (typeof data === 'string') {
    try {
      return JSON.stringify(JSON.parse(data), null, 2)
    } catch {
      return data
    }
  }

  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

async function sendRequest() {
  loading.value = true
  errorText.value = ''
  responseStatusText.value = ''
  elapsedMs.value = null
  prettyResponse.value = ''

  const fullUrl = joinUrl(baseUrl.value, apiPath.value)

  let headers = {}
  let getParams = {}
  let postParams = {}

  try {
    headers = parseJsonOrThrow(headersJson.value, 'Header')
    getParams = parseJsonOrThrow(getParamsJson.value, 'GET 参数')
    postParams = parseJsonOrThrow(postParamsJson.value, 'POST 参数')
  } catch (e) {
    errorText.value = e?.message || String(e)
    loading.value = false
    return
  }

  // axios 对 headers 的类型容错有限：这里强制确保是对象
  if (headers === null || typeof headers !== 'object' || Array.isArray(headers)) {
    errorText.value = 'Header 必须是 JSON 对象（例如：{"k":"v"}）'
    loading.value = false
    return
  }

  const config = {
    method: method.value,
    url: fullUrl,
    headers: { ...headers },
    validateStatus: () => true // 让 4xx/5xx 也能拿到响应并显示
  }

  if (method.value === 'GET') {
    config.params = getParams
  } else {
    // POST 以 JSON body 发送
    config.data = postParams
    config.headers['Content-Type'] = config.headers['Content-Type'] || 'application/json'
  }

  const start = Date.now()
  try {
    const resp = await axios.request(config)
    const end = Date.now()

    responseStatusText.value = `${resp.status} ${resp.statusText || ''}`.trim()
    elapsedMs.value = end - start
    prettyResponse.value = prettyPrint(resp.data)
  } catch (e) {
    const end = Date.now()
    elapsedMs.value = end - start

    const resp = e?.response
    const statusCode = resp?.status
    responseStatusText.value = resp
      ? `${statusCode} ${resp.statusText || ''}`.trim()
      : '请求失败'

    prettyResponse.value = prettyPrint(resp?.data ?? e?.message)
    errorText.value = '请求失败，请检查 URL/路由/参数或是否跨域允许'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const response = await axios.get('/api')
    status.value = response.data
  } catch (error) {
    console.error('无法连接到后端服务:', error)
    status.value = { message: '无法连接到后端服务' }
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
  background-color: #f5f5f5;
}

#app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

header {
  text-align: center;
  margin-bottom: 40px;
  padding: 40px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
}

header h1 {
  font-size: 48px;
  margin-bottom: 10px;
}

header p {
  font-size: 20px;
  opacity: 0.9;
}

.card {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.card h2 {
  margin-bottom: 20px;
  color: #333;
}

.card p {
  font-size: 18px;
  color: #666;
}

.panel {
  text-align: left;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.field label {
  display: block;
  font-size: 14px;
  color: #555;
  margin-bottom: 8px;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  border: 1px solid #e6e6e6;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
  background: #fafafa;
}

.field textarea {
  resize: vertical;
}

.span-2 {
  grid-column: span 2;
}

.actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 18px 0;
}

.primary {
  border: none;
  border-radius: 10px;
  padding: 12px 18px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 16px;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(118, 75, 162, 0.2);
}

.primary:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.hint {
  color: #d93025;
  font-size: 14px;
}

.response {
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 16px;
  background: #fcfcfc;
}

.response-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 12px;
}

.muted {
  color: #777;
  font-size: 14px;
}

.response-body {
  white-space: pre-wrap;
  word-break: break-word;
  background: #0b1020;
  color: #e5e7eb;
  border-radius: 8px;
  padding: 14px;
  max-height: 420px;
  overflow: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono',
    'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}
</style>
