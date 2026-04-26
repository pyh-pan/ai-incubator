import { Button, Input, Spin, Tag } from 'antd'
import { useState } from 'react'
import type { ConversationMessageV2, QuestionBatchItem, ThinkingNode } from '../../types/incubator'

interface ChatPanelProps {
  messages: ConversationMessageV2[]
  selectedNode: ThinkingNode | null
  isThinking: boolean
  onSubmit: (content: string, nodeId?: string | null) => void
}

export default function ChatPanel({ messages, selectedNode, isThinking, onSubmit }: ChatPanelProps) {
  const [value, setValue] = useState('')

  const submit = () => {
    const content = value.trim()
    if (!content) return
    onSubmit(content, selectedNode?.id ?? null)
    setValue('')
  }

  return (
    <section className="h-full min-h-0 flex flex-col border-r border-slate-200 bg-white">
      <div className="px-4 py-3 border-b border-slate-200">
        <div className="text-sm font-semibold text-slate-800">思考对话</div>
        {selectedNode && (
          <Tag className="mt-2 max-w-full whitespace-normal" color="blue">
            围绕节点：{selectedNode.title}
          </Tag>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg) => (
          <div key={msg.id} className={msg.role === 'user' ? 'text-right' : 'text-left'}>
            <div
              className={`inline-block max-w-[90%] rounded-lg px-3 py-2 text-sm leading-6 ${
                msg.role === 'user' ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-800'
              }`}
            >
              <MessageBody message={msg} />
            </div>
          </div>
        ))}
        {isThinking && <Spin size="small" description="AI 正在思考..." />}
      </div>

      <div className="p-4 border-t border-slate-200">
        <Input.TextArea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          rows={4}
          placeholder="可以一次回答多个问题，例如按问题标题分段说明..."
          onPressEnter={(event) => {
            if (!event.shiftKey) {
              event.preventDefault()
              submit()
            }
          }}
        />
        <Button type="primary" block className="mt-3" loading={isThinking} onClick={submit}>
          发送
        </Button>
      </div>
    </section>
  )
}

function MessageBody({ message }: { message: ConversationMessageV2 }) {
  if (message.role === 'user') return <span className="whitespace-pre-line break-words">{message.content}</span>

  const metadata = message.message_metadata
  const questions = metadata?.background_questions ?? metadata?.question_batch ?? metadata?.follow_up_questions
  const reasoning = metadata?.visible_reasoning_summary

  return (
    <div className="space-y-3 text-left">
      {reasoning && (
        <details className="rounded-md bg-slate-200/70 px-2 py-1 text-xs leading-5 text-slate-500">
          <summary className="cursor-pointer select-none">思考过程</summary>
          <p className="mt-1 whitespace-pre-line break-words">{reasoning}</p>
        </details>
      )}
      {questions && questions.length > 0 ? (
        <QuestionBatch questions={questions} />
      ) : (
        <span className="whitespace-pre-line break-words">{message.content}</span>
      )}
    </div>
  )
}

function QuestionBatch({ questions }: { questions: QuestionBatchItem[] }) {
  return (
    <div className="space-y-2">
      {questions.map((item, index) => (
        <div key={`${item.question}-${index}`} className="rounded-md bg-white px-3 py-2 shadow-sm shadow-slate-200/70">
          <div className="text-xs font-semibold text-slate-500">
            {item.short_title || `问题 ${index + 1}`}
          </div>
          <div className="mt-1 text-sm leading-6 text-slate-900 break-words">{item.question}</div>
          {(item.why_this_matters || item.why_needed) && (
            <div className="mt-1 text-xs leading-5 text-slate-500 break-words">{item.why_this_matters || item.why_needed}</div>
          )}
        </div>
      ))}
    </div>
  )
}
