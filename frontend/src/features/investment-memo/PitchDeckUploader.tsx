import { useMutation } from '@tanstack/react-query'
import { useRef, useState, type ChangeEvent, type FormEvent } from 'react'

import { ApiError } from '../../api/errors/ApiError'
import { memoService } from '../../api/services/memo.service'

const MAX_DECK_BYTES = 25 * 1024 * 1024

function messageFor(error: unknown): string {
  return error instanceof ApiError ? error.message : 'The pitch deck could not be uploaded.'
}

export function PitchDeckUploader() {
  const [file, setFile] = useState<File | null>(null)
  const [validationError, setValidationError] = useState<string | null>(null)
  const controllerRef = useRef<AbortController | null>(null)
  const upload = useMutation({
    mutationFn: async (selectedFile: File) => {
      const controller = new AbortController()
      controllerRef.current = controller
      return memoService.uploadPitchDeck(selectedFile, controller.signal)
    },
    onSettled: () => { controllerRef.current = null },
  })

  const selectFile = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null
    upload.reset()
    if (!selected) {
      setFile(null)
      return
    }
    if (selected.size > MAX_DECK_BYTES) {
      setFile(null)
      setValidationError('Choose a pitch deck smaller than 25 MB.')
      event.target.value = ''
      return
    }
    setValidationError(null)
    setFile(selected)
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!file) {
      setValidationError('Choose a pitch deck to upload.')
      return
    }
    upload.mutate(file)
  }

  return (
    <form className="media-tool" onSubmit={submit}>
      <div className="media-tool__heading"><span aria-hidden="true">01</span><div><h3>Attach pitch deck</h3><p>Upload one private file to the backend’s pitch-deck storage. Maximum size: 25 MB.</p></div></div>
      <label className="file-input">
        <span>{file ? file.name : 'Choose a pitch deck'}</span>
        <input type="file" onChange={selectFile} disabled={upload.isPending} />
      </label>
      {file ? <p className="media-tool__meta">{(file.size / 1024 / 1024).toFixed(2)} MB</p> : null}
      <p className="form-error" role="alert">{validationError ?? (upload.error ? messageFor(upload.error) : '')}</p>
      {upload.data ? <div className="storage-result" role="status"><strong>Upload stored</strong><code>{upload.data}</code><p>This is a storage identifier, not a public download link.</p></div> : null}
      <div className="media-tool__actions">
        <button className="button button--primary" type="submit" disabled={upload.isPending}>{upload.isPending ? 'Uploading…' : 'Upload deck'}</button>
        {upload.isPending ? <button className="button button--text" type="button" onClick={() => controllerRef.current?.abort()}>Cancel</button> : null}
      </div>
    </form>
  )
}
