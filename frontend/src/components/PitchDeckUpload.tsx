import { useState, type FormEvent } from 'react'
import { getSupabaseBrowserClient } from '../lib/supabase'

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
    setMessage('Encrypting and uploading…')

    try {
      const supabase = getSupabaseBrowserClient()
      const { data: userData, error: userError } = await supabase.auth.getUser()
      if (userError || !userData.user) {
        throw new Error('Sign in before uploading a confidential deck.')
      }
      const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, '-')
      const path = `${userData.user.id}/incoming/${crypto.randomUUID()}-${safeName}`
      const { error } = await supabase.storage.from('pitch-decks').upload(path, file, {
        cacheControl: '3600',
        contentType: file.type,
        upsert: false,
      })

      if (error) throw error
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
        <span className="secure-mark">Private</span>
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
