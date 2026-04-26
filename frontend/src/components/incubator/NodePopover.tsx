import { Button, Input, Tag } from 'antd'
import { useEffect, useState } from 'react'
import type { CenterContext, ThinkingNode } from '../../types/incubator'

interface NodePopoverProps {
  node: ThinkingNode
  centerContext: CenterContext
  isThinking: boolean
  onAnswerNode: (nodeId: string, content: string) => void
  onClose: () => void
}

function textList(items: string[]) {
  if (items.length === 0) return null
  return (
    <div className="space-y-1">
      {items.map((item) => (
        <div key={item} className="rounded-md bg-slate-50 px-2 py-1 text-xs leading-5 text-slate-700">
          {item}
        </div>
      ))}
    </div>
  )
}

const kindText: Record<ThinkingNode['kind'], string> = {
  idea: '中心',
  question: '问题',
  answer: '回答',
  insight: '洞察',
  assumption: '假设',
  decision: '决策',
  risk: '风险',
  next_step: '下一步',
  followup: '追问',
}

const statusText: Record<ThinkingNode['status'], string> = {
  open: '待回答',
  answered: '已回答',
  suggested: '建议',
  confirmed: '确认',
  needs_context: '补背景',
  resolved: '完成',
}

export default function NodePopover({ node, centerContext, isThinking, onAnswerNode, onClose }: NodePopoverProps) {
  const [answer, setAnswer] = useState('')
  const isCenter = node.kind === 'idea'
  const canAnswer = !isCenter && node.status !== 'answered'
  const rationale = typeof node.layout?.rationale === 'string' ? node.layout.rationale : node.summary
  const expectedAnswerType =
    typeof node.layout?.expected_answer_type === 'string' ? node.layout.expected_answer_type : null

  useEffect(() => {
    setAnswer('')
  }, [node.id])

  const submit = () => {
    const content = answer.trim()
    if (!content) return
    onAnswerNode(node.id, content)
    setAnswer('')
  }

  return (
    <div className="w-[360px] max-w-[calc(100vw-48px)] rounded-lg border border-slate-200 bg-white p-4 text-left shadow-xl shadow-slate-200/80">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Tag color={node.status === 'answered' ? 'green' : isCenter ? 'blue' : 'cyan'}>{kindText[node.kind]}</Tag>
            <Tag color="default">{statusText[node.status]}</Tag>
          </div>
          <h3 className="mt-2 text-base font-semibold leading-6 text-slate-950 break-words">{node.title}</h3>
        </div>
        <Button size="small" type="text" onClick={onClose} aria-label="关闭节点弹窗">
          ×
        </Button>
      </div>

      {isCenter ? (
        <div className="mt-3 space-y-3">
          <div>
            <div className="text-xs font-medium text-slate-500">初始想法</div>
            <p className="mt-1 text-sm leading-6 text-slate-800 break-words">{centerContext.original_idea}</p>
          </div>
          {centerContext.background_summary && (
            <div>
              <div className="text-xs font-medium text-slate-500">背景信息</div>
              <p className="mt-1 whitespace-pre-line text-sm leading-6 text-slate-800 break-words">
                {centerContext.background_summary}
              </p>
            </div>
          )}
          {textList(centerContext.unresolved_context_gaps)}
        </div>
      ) : (
        <div className="mt-3 space-y-3">
          {node.question && <p className="text-sm leading-6 text-slate-900 break-words">{node.question}</p>}
          {rationale && <p className="rounded-md bg-slate-50 p-3 text-xs leading-5 text-slate-600 break-words">{rationale}</p>}
          {expectedAnswerType && <div className="text-xs text-slate-500">期望回答：{expectedAnswerType}</div>}
          {node.answer_summary && (
            <div className="rounded-md bg-emerald-50 p-3 text-sm leading-6 text-emerald-800 break-words">
              {node.answer_summary}
            </div>
          )}
          {canAnswer && (
            <>
              <Input.TextArea
                value={answer}
                onChange={(event) => setAnswer(event.target.value)}
                rows={4}
                placeholder="输入你对这个问题的回答..."
              />
              <Button type="primary" block loading={isThinking} disabled={!answer.trim()} onClick={submit}>
                确认回答
              </Button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
