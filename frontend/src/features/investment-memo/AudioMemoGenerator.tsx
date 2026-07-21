import { useMutation } from '@tanstack/react-query'
import { useRef, useState, type FormEvent } from 'react'

import { ApiError } from '../../api/errors/ApiError'
import { memoService } from '../../api/services/memo.service'

const TEXT_LIMIT = 100_000

type Props = {
  memoId: string
  initialText: string
}

function messageFor(error: unknown): string {
  return error instanceof ApiError ? error.message : 'The audio memo could not be generated.'
}

export function AudioMemoGenerator({ memoId, initialText }: Props) {
  const [text, setText] = useState(initialText)
  const [validationError, setValidationError] = useState<string | null>(null)
  const controllerRef = useRef<AbortController | null>(null)
  const narration = useMutation({
    mutationFn: async (memoText: string) => {
      const controller = new AbortController()
      controllerRef.current = controller
      return memoService.generateAudio(memoId, memoText, controller.signal)
    },
    onSettled: () => { controllerRef.current = null },
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const normalized = text.trim()
    if (!normalized) {
      setValidationError('Enter memo text to narrate.')
      return
    }
    setValidationError(null)
    narration.mutate(normalized)
  }

  return (
    <form className="media-tool" onSubmit={submit}>
      <div className="media-tool__heading"><span aria-hidden="true">02</span><div><h3>Generate audio memo</h3><p>Review the frontend-composed brief before sending it to the backend narration service.</p></div></div>
      <label htmlFor="memo-narration">Narration text</label>
      <textarea id="memo-narration" value={text} maxLength={TEXT_LIMIT} rows={12} disabled={narration.isPending} onChange={(event) => { setText(event.target.value); setValidationError(null); narration.reset() }} />
      <p className="media-tool__meta">{text.length.toLocaleString()} / {TEXT_LIMIT.toLocaleString()} characters</p>
      <p className="form-error" role="alert">{validationError ?? (narration.error ? messageFor(narration.error) : '')}</p>
      {narration.data ? <div className="storage-result" role="status"><strong>Audio stored</strong><code>{narration.data}</code><p>The backend returns a storage identifier; it does not provide a playback URL.</p></div> : null}
      <div className="media-tool__actions">
        <button className="button button--primary" type="submit" disabled={narration.isPending}>{narration.isPending ? 'Generating audio…' : 'Generate audio'}</button>
        {narration.isPending ? <button className="button button--text" type="button" onClick={() => controllerRef.current?.abort()}>Cancel</button> : null}
      </div>
    </form>
  )
}
