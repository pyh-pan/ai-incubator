import { Empty, Tag } from 'antd'
import type { ThinkingNode } from '../../types/incubator'

interface NodeInspectorProps {
  node: ThinkingNode | null
}

export default function NodeInspector({ node }: NodeInspectorProps) {
  if (!node) {
    return (
      <aside className="border-l border-slate-200 bg-white p-4 w-80 overflow-y-auto">
        <Empty description="选择一个节点查看详情" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </aside>
    )
  }

  return (
    <aside className="border-l border-slate-200 bg-white p-4 w-80 overflow-y-auto">
      <Tag color="blue">{node.kind}</Tag>
      <h3 className="mt-3 text-lg font-semibold text-slate-900 break-words">{node.title}</h3>
      {node.question && <p className="mt-3 text-sm text-slate-700 break-words">{node.question}</p>}
      {node.summary && <p className="mt-3 text-sm text-slate-600 break-words">{node.summary}</p>}
      {node.answer_summary && (
        <div className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800 break-words">
          {node.answer_summary}
        </div>
      )}
    </aside>
  )
}
