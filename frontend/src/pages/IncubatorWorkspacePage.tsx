import { ArrowLeftOutlined } from '@ant-design/icons'
import { Button, Spin, Tag } from 'antd'
import { useState, type PointerEvent as ReactPointerEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ChatPanel from '../components/incubator/ChatPanel'
import MindmapCanvas from '../components/incubator/MindmapCanvas'
import RestructureSuggestionPanel from '../components/incubator/RestructureSuggestionPanel'
import { useIncubatorSession } from '../hooks/useIncubatorSession'
import type { ThinkingNode } from '../types/incubator'

export default function IncubatorWorkspacePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { workspace, isLoading, isThinking, submitTurn, answerNode, acceptSuggestion, rejectSuggestion } = useIncubatorSession(projectId)
  const [selectedNode, setSelectedNode] = useState<ThinkingNode | null>(null)
  const [leftWidth, setLeftWidth] = useState(340)

  const startResize = (event: ReactPointerEvent<HTMLDivElement>) => {
    event.preventDefault()
    const startX = event.clientX
    const startWidth = leftWidth
    const onMove = (moveEvent: globalThis.PointerEvent) => {
      const next = Math.min(520, Math.max(280, startWidth + moveEvent.clientX - startX))
      setLeftWidth(next)
    }
    const onUp = () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
  }

  if (isLoading || !workspace) {
    return (
      <div className="h-[calc(100vh-112px)] flex items-center justify-center">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-112px)] flex flex-col bg-white border border-slate-200 rounded-lg overflow-hidden">
      <header className="h-14 border-b border-slate-200 px-4 flex items-center gap-3 shrink-0">
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/projects')}>
          返回
        </Button>
        <h1 className="text-lg font-semibold text-slate-900 flex-1 truncate">{workspace.title}</h1>
        {workspace.thinking_stage && <Tag color="geekblue">{workspace.thinking_stage}</Tag>}
        {workspace.thinking_mode && <Tag color="purple">{workspace.thinking_mode}</Tag>}
      </header>
      <main className="flex-1 grid min-h-0 relative" style={{ gridTemplateColumns: `${leftWidth}px 6px minmax(0, 1fr)` }}>
        <ChatPanel
          messages={workspace.messages}
          selectedNode={selectedNode}
          isThinking={isThinking}
          onSubmit={(content) => submitTurn({ content, source: 'chat' })}
        />
        <div
          className="cursor-col-resize border-r border-slate-200 bg-slate-100 hover:bg-sky-100"
          onPointerDown={startResize}
          aria-label="调整左侧宽度"
        />
        <MindmapCanvas
          nodes={workspace.nodes}
          centerContext={workspace.center_context}
          selectedNodeId={selectedNode?.id ?? null}
          isThinking={isThinking}
          onSelectNode={setSelectedNode}
          onAnswerNode={answerNode}
        />
        <RestructureSuggestionPanel
          suggestions={workspace.suggestions}
          onAccept={acceptSuggestion}
          onReject={rejectSuggestion}
        />
      </main>
    </div>
  )
}
