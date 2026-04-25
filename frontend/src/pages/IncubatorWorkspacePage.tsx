import { ArrowLeftOutlined } from '@ant-design/icons'
import { Button, Spin, Tag } from 'antd'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ChatPanel from '../components/incubator/ChatPanel'
import MindmapCanvas from '../components/incubator/MindmapCanvas'
import NodeInspector from '../components/incubator/NodeInspector'
import RestructureSuggestionPanel from '../components/incubator/RestructureSuggestionPanel'
import { useIncubatorSession } from '../hooks/useIncubatorSession'
import type { ThinkingNode } from '../types/incubator'

export default function IncubatorWorkspacePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { workspace, isLoading, isThinking, submitTurn } = useIncubatorSession(projectId)
  const [selectedNode, setSelectedNode] = useState<ThinkingNode | null>(null)

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
      <main className="flex-1 grid grid-cols-[380px_minmax(0,1fr)_320px] min-h-0 relative">
        <ChatPanel
          messages={workspace.messages}
          selectedNode={selectedNode}
          isThinking={isThinking}
          onSubmit={(content, nodeId) => submitTurn({ content, source: nodeId ? 'node' : 'chat', node_id: nodeId })}
        />
        <MindmapCanvas nodes={workspace.nodes} selectedNodeId={selectedNode?.id ?? null} onSelectNode={setSelectedNode} />
        <NodeInspector node={selectedNode} />
        <RestructureSuggestionPanel suggestions={workspace.suggestions} />
      </main>
    </div>
  )
}
