import { useState, type FormEvent } from 'react'

const MAX_FILE_SIZE = 25 * 1024 * 1024

export function PitchDeckUpload() {
  const [file, setFile] = useState<File>()
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('PDF or PowerPoint · 25 MB maximum')

  async function uploadPitchDeck(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file) return

    if (file.size > MAX_FILE_SIZE) {
      setStatus('error')
      setMessage('That deck is larger than 25 MB.')
      return
    }

    setStatus('uploading')
    setMessage('Uploading to MongoDB…')

    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch(
        `${import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:9000'}/v1/memos/pitch-deck`,
        { method: 'POST', body: formData },
      )
      if (!response.ok) {
        const body = await response.json().catch(() => undefined)
        throw new Error(body?.detail ?? 'Upload failed. Try again.')
      }
      setStatus('success')
      setMessage('Deck received. Screening can begin.')
      setFile(undefined)
      event.currentTarget.reset()
    } catch (error) {
      setStatus('error')
      setMessage(error instanceof Error ? error.message : 'Upload failed. Try again.')
    }
  }

  return (
    <article className="panel upload-panel">
      <div className="panel__heading">
        <div>
          <p className="eyebrow">New opportunity</p>
          <h2>Upload a pitch deck</h2>
        </div>
        <span className="secure-mark">MongoDB</span>
      </div>
      <form onSubmit={uploadPitchDeck}>
        <label className="file-drop">
          <span className="file-drop__icon" aria-hidden="true">↗</span>
          <span>{file?.name ?? 'Choose a deck'}</span>
          <input
            type="file"
            accept=".pdf,.ppt,.pptx,application/pdf,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation"
            onChange={(event) => {
              setFile(event.target.files?.[0])
              setStatus('idle')
              setMessage('PDF or PowerPoint · 25 MB maximum')
            }}
          />
        </label>
        <div className="upload-footer">
          <p className={`form-message form-message--${status}`} aria-live="polite">
            {message}
          </p>
          <button type="submit" disabled={!file || status === 'uploading'}>
            {status === 'uploading' ? 'Uploading' : 'Start review'}
          </button>
        </div>
      </form>
    </article>
  )
}
