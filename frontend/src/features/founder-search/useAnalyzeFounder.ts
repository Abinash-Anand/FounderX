import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRef } from 'react'

import { founderService } from '../../api/services/founder.service'
import type { FounderAnalysisModel } from '../../entities/founder/founderAnalysis.models'
import { founderAnalysisKeys } from './founderAnalysis.keys'

type AnalyzeVariables = {
  query: string
}

export function useAnalyzeFounder() {
  const queryClient = useQueryClient()
  const controllerRef = useRef<AbortController | null>(null)

  const mutation = useMutation({
    mutationFn: async ({ query }: AnalyzeVariables) => {
      controllerRef.current?.abort()
      const controller = new AbortController()
      controllerRef.current = controller
      return founderService.analyze(query, controller.signal)
    },
    onSuccess: (analysis, { query }) => {
      queryClient.setQueryData<FounderAnalysisModel>(founderAnalysisKeys.query(query), analysis)
      queryClient.setQueryData<FounderAnalysisModel>(founderAnalysisKeys.active(), analysis)
    },
    onSettled: () => {
      controllerRef.current = null
    },
  })

  return {
    ...mutation,
    cancel: () => controllerRef.current?.abort(),
  }
}
