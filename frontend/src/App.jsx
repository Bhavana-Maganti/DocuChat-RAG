import { useState } from 'react'

const API = 'http://localhost:8000'

export default function App() {
  const [file, setFile] = useState(null)
  const [uploadStatus, setUploadStatus] = useState('')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function upload() {
    if (!file) return
    setUploadStatus('Uploading & indexing...')
    setError('')
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch(`${API}/upload`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setUploadStatus(`Indexed ${data.chunks_indexed} chunks from ${data.file}`)
    } catch (e) {
      setError(String(e))
      setUploadStatus('')
    }
  }

  async function ask() {
    if (!question.trim()) return
    setLoading(true)
    setError('')
    setAnswer(null)
    try {
      const res = await fetch(`${API}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      if (!res.ok) throw new Error(await res.text())
      setAnswer(await res.json())
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="wrap">
      <h1>DocuChat</h1>
      <div className="sub">Upload a PDF and ask questions. Answers include source citations.</div>

      <div className="card">
        <strong>1. Upload a PDF</strong>
        <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
          <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files[0])} />
          <button onClick={upload} disabled={!file}>Index</button>
        </div>
        {uploadStatus && <div style={{ marginTop: 8, color: '#22c55e' }}>{uploadStatus}</div>}
      </div>

      <div className="card">
        <strong>2. Ask a question</strong>
        <textarea
          placeholder="e.g. What does section 3 say about refund policy?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          style={{ marginTop: 10 }}
        />
        <div style={{ marginTop: 10 }}>
          <button onClick={ask} disabled={loading || !question.trim()}>
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </div>
      </div>

      {error && <div className="card" style={{ borderColor: '#ef4444' }}>Error: {error}</div>}

      {answer && (
        <div className="card">
          <strong>Answer</strong>
          <div className="answer" style={{ marginTop: 8 }}>{answer.answer}</div>
          {answer.sources?.length > 0 && (
            <div className="sources">
              <div style={{ marginTop: 14, marginBottom: 6 }}>Sources:</div>
              {answer.sources.map((s, i) => (
                <div className="src" key={i}>
                  <span className="pill">{s.source}{s.page != null ? ` · p.${s.page + 1}` : ''}</span>
                  {s.snippet}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
