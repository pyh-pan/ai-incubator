import { Alert, Button } from 'antd'
import type { RestructureSuggestion } from '../../types/incubator'

interface Props {
  suggestions: RestructureSuggestion[]
  onAccept: (id: string) => void
  onReject: (id: string) => void
}

export default function RestructureSuggestionPanel({ suggestions, onAccept, onReject }: Props) {
  if (suggestions.length === 0) return null

  return (
    <div className="absolute right-4 top-4 w-80 space-y-3">
      {suggestions.map((suggestion) => (
        <Alert
          key={suggestion.id}
          type="info"
          showIcon
          message="AI 建议重组导图"
          description={
            <div>
              <p>{suggestion.rationale}</p>
              <div className="mt-3 flex gap-2">
                <Button size="small" type="primary" onClick={() => onAccept(suggestion.id)}>
                  接受
                </Button>
                <Button size="small" onClick={() => onReject(suggestion.id)}>
                  拒绝
                </Button>
              </div>
            </div>
          }
        />
      ))}
    </div>
  )
}
