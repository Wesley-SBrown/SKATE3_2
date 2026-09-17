<!-- web/src/App.vue -->

<script setup>
// manages component's reactivity, network requests & utility funcs w/ Vue3's Composition API

import { ref, reactive, computed } from 'vue'

// create state obj to contain query filters / parameters
const queryState = reactive({
    searchMode: 'quick', // 'quick' or 'advanced'
    searchTerm: '', // single record name lookup
    stationCode: '', // selected or typed
    fromDate: '',
    toDate: '',
    pier: '',
    period: '',
    gain: '',
    orientation: ''
})

const results = ref([])
const loading = ref(false)
const errorMessage = ref('')

const availableStations = ref([
  'MWC', 'PAS', 'TIN', 'FTC', 'BBC', 'RVR', 'HAI'
])

const stationInput = ref('')
const showStationDropDown = ref(false)

const filteredStations = computed(() => {
  if (!stationInput.value) return availableStations.value
  return availableStations.value.filter(code =>
    code.toLowerCase().includes(stationInput.value.toLowerCase)
  )
})

const selectStation = (code) => {
  queryState.stationCode = code
  stationInput.value = code
  showStationDropDown = false
}

// link to cloudflare worker
const CLOUDWATCH_WORKER_URL = 'https://-skate3-2.wsb-wesleybrown.workers.dev'

const sendQuery = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(CLOUDWATCH_WORKER_URL, {
      method : 'POST',
      headers : {
        'Content-Type' : 'application/json'
      },
      body : JSON.stringify(queryState)
    })
    
    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`)
    }

    const data = await response.json()

    results.value = data
  } catch (err) {
    errorMessage.value = `Query failed: ${err.message}`
  } finally {
    loading.value = false
  }
}

// retrieve thumbnail from gdrive storage
const getThumbnailUrl = (item) => {
  return '<googledrivelink/folder/image>'
}

// copy-to-clipboard & export operations
const copyToClipboard = async (text, successMessage) => {
  try {
    await navigator.clipboard.writeText(text)
    alert(successMessage)
  } catch (err) {
    alert('Falied to copy to clipboard:' + err)
  }
}

const copyJsonResults = () => {
  copyToClipboard(JSON.stringify(results.value, null, 2), 'JSON copied to clipboard!')
}

const copyRsyncScript = () => {
  const scriptLines = results.value.map(
    item => `rsync -avz $<server-address/folder/file>`
  )
  copyToClipboard(scriptLines.join('\n'), 'Rsync download script copied!')
}

// local file creation using Blob & URL.createObjectURL
const downloadLocalFile = (content, filename, contentType) => {
  const blob = new Blob([content], {type : contentType})
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const downloadJsonAsFile = () => {
  downloadLocalFile(
    JSON.stringify(results.value, null, 2),
    'auradb-query-results.json',
    'application/json'
  )
}
</script>

<template>
  <div class="query-widget">
    <div class="header-section">
      <h3>AuraDB Interactive Control Panel</h3>
      <span class="badge" v-if="results.length > 0">{{ results.length }} items found</span>
    </div>

    <!---Mode Switch Tabs-->
    <div class="mode-switcher">
      <button
        :class="['tab-btn', { active: queryState.searchMode === 'quick' }]"
        @click="queryState.searchMode = 'quick'"
      >
        Quick Search (by Record Name)
      </button>
      <button
        :class="['tab-btn', { active: queryState.searchMode === 'advanced' }]"
        @click="queryState.searchMode = 'advanced'"
      >
        Advanced Parameters
      </button>
    </div>

    <!---Input controls: Quick Search Mode-->
    <div v-if="queryState.searchMode === 'quick'" class="controls">
      <div class="input-wrapper">
        <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input
          v-model="queryState.searchTerm" 
          type="text" 
          placeholder="Enter record name (stem)" 
          @keyup.enter="sendQuery"
        />
      </div>
      <button class="btn primary" @click="sendQuery" :disabled="loading">
        {{ loading ? 'Executing...': 'Submit Query' }}
      </button>
    </div>

    <!---Input Controls: Advanced Query Mode-->
    <div v-else class="advanced-controls">
      <div class="form-row">
        <!---Searchable Stations-->
        <div class="form-group dropdown-container">
          <label>Station Code</label>
          <input
            type="text"
            v-model="stationInput"
            @focus="showStationDropDown = true"
            @input="showStationDropDown = true; queryState.stationCode = stationInput"
            placeholder="Type or select station..."
          />
          <div v-if="showStationDropDown && filteredStations.length > 0" class="dropdown-list">
            <div
              v-for="station in filteredStations"
              :key="station"
              class="dropdown-item"
              @click="selectStation(station)"
            >
              {{ station }}
            </div>
          </div>
        </div>

        <!-- Pier -->
        <div class="form-group">
          <label>Pier</label>
          <input type="text" v-model="queryState.pier" placeholder="i.e. I / IV"/>
        </div>

        <!--Orientation-->
        <div class="form-group">
          <label>Orientation</label>
          <input type="text" v-model="queryState.orientation" placeholder="Z/N/E"/>          
        </div>
      </div>

      <div class="form-row">
        <!--From Date-->
        <div class="form-group">
          <label>From Date</label>
          <input type="date" v-model="queryState.fromDate"/>
        </div>

        <!--Through Date-->
        <div class="form-group">
          <label>Through Date</label>
          <input type="date" v-model="queryState.toDate" />
        </div>

        <!--Period-->
        <div class="form-group">
          <label>Period</label>
          <input type="text" v-model="queryState.period" placeholder="i.e. S/L"/>
        </div>

        <!--Gain-->
        <div class="form-group">
          <label>Gain</label>
          <input type="text" v-model="queryState.gain" placeholder="i.e. L/H"/>
        </div>
      </div>

      <div class="advanced-wrapper">
        <button class="btn primary full width" @click="sendQuery" :disabled="loading">
          {{ loading ? 'Executing Advanced Query...' : 'Execute Structured Query' }}
        </button>
      </div>
    </div>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <!---Action Bar-->
    <div v-if="results.length > 0" class="export-actions">
      <span class="action-label">Export:</span>
      <button class="btn-secondary" @click="copyJsonResults">Copy JSON</button>
      <button class="btn-secondary" @click="copyRsyncScript">Copy Rsync Script</button>
      <button class="btn-secondary" @click="downloadJsonAsFile">Download JSON File</button>
    </div>
  
    <!---Results Grid with Thumbnails-->
    <div v-if="results.length > 0" class="results-grid">
      <div v-for="(item,index) in results" :key="index" class="result-card">
        <div class="img-container">
          <img :src="getThumbnailUrl(item)" alt="Thumbnail preview" loading="lazy" />
        </div>
        <div class="metadata">
          <p><strong>Stem:</strong>{{ item.file_stem }}</p>
          <p><strong>Folder:</strong>{{ item.subfolder }}</p>
        </div>
      </div>
    </div>

    <!---Empty State-->
    <div v-if="results.length === 0 && !loading && !errorMessage"  class="empty-state">
      <p>No query executed yet / No results found</p>
    </div>
  </div>
</template>

<style scoped>
.query-widget {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  max-width: 1000px;
  margin: 2rem auto;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 2rem;
  border-radius: 12px;
  background: linear-gradient(145deg, #1e2022, #151719);
  color: #f0f6fc;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header-section h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.badge {
  background: #238636;
  color: white;
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
  border-radius: 99px;
  font-weight: 500;
}

.mode-switcher {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  border-bottom: 1px solid #30363d;
  padding-bottom: 0.75rem;
}

.tab-btn {
  background: #161b22;
  border: 1px solid #30363d;
  color: #8b949e;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn-active {
  background: #21262d;
  color: #f0f0fc;
  border-color: #58a6ff;
  font-weight: 500;
}
.controls {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 1.25rem;
}

.input-wrapper {
  position: relative;
  flex: 1
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #8b949e;
}

.controls input {
  width: 100%;
  padding: 0.75rem 0.75rem 0.75rem 2.5rem;
  background-color: #0d1117;
  border: 1px solid #30363d;
  color: #f0f6fc;
  margin-left: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.controls input:focus {
  outline: none;
  border-color: #58a6ff;
  box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.3);
}

.advanced-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.25rem;
  background: #161b22;
  padding: 1.25rem;
  border-radius: 8px;
  border: 1px solid #30363d;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  position: relative;
}

.form-group label {
  font-size: 0.8rem;
  color: #8b949e;
  font-weight: 500;
}

.form-group input {
  padding: 0.6rem 0.75rem;
  background-color: #0d1117;
  border: 1px solid #30363d;
  color: #f0f6fc;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #58a6ff;
  box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.3);
}

.dropdown-container {
  position: relative;
}

.dropdown-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 150px;
  overflow-y: auto;
  background: #0d1117;
  border: 1px solid #30363d;
  border-top: none;
  border-radius: 0 0 6px 6px;
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}

.dropdown-item {
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
  color: #c9d1d9;
  cursor: pointer;
}

.dropdown-item:hover {
  background: #21262d;
  color: #58a6ff;
}

.advanced-submit-wrapper {
  margin-top: 0.5rem;
}

.full-width {
  width: 100%;
}

.btn {
  padding: 0.75rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.2s ease, transform 0.1s ease;
}

.btn:active {
  transform: scale(0.98);
}

.btn.primary {
  background-color: #238636;
  color: white;
  border-color: rgba(27, 31, 35, 0.15);
}

.btn.primary:hover:not(:disabled) {
  background-color: #2ea043;
}

.btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.secondary {
  background-color: #21262d;
  color: #c9d1d9;
  border-color: #30363d;
}

.btn.secondary:hover {
  background-color: #30363d;
  color: #f0f6fc;
}

.export-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #30363d;
}

.action-label {
  font-size: 0.85rem;
  color: #8b949e;
  margin-right: 0.25rem;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.result-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.result-card:hover {
  transform: translateY(-2px);
  border-color: #8b949e;
}

.img-container {
  width: 100%;
  height: 130px;
  background: #0d1117;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.result-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.metadata {
  padding: 0.75rem;
}

.metadata p {
  font-size: 0.85rem;
  margin: 0.2rem 0;
  color: #c9d1d9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.error {
  color: #f85149;
  background: rgba(248, 81, 73, 0.1);
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid rgba(248, 81, 73, 0.4);
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #8b949e;
  font-size: 0.95rem;
}

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>