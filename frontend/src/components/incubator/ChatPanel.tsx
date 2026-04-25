import { Button, Input, Spin, Tag } from 'antd'
import { useState } from 'react'
import type { ConversationMessageV2, ThinkingNode } from '../../types/incubator'

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
              className={`inline-block max-w-[88%] rounded-lg px-3 py-2 text-sm leading-6 ${
                msg.role === 'user' ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-800'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {isThinking && <Spin size="small" tip="AI 正在思考..." />}
      </div>

      <div className="p-4 border-t border-slate-200">
        <Input.TextArea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          rows={4}
          placeholder="回答 AI 的问题，或围绕选中节点继续思考..."
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
