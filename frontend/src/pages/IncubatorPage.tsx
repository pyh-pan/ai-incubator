import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Spin } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  applyNodeChanges,
  addEdge,
} from 'reactflow'
import type { NodeTypes } from 'reactflow'
import 'reactflow/dist/style.css'
import { projectApi, nodeApi } from '../api'
import type { MindmapNode } from '../types'
import MindmapNodeComponent from '../components/mindmap/MindmapNode'

const nodeTypes: NodeTypes = {
  mindmapNode: MindmapNodeComponent,
}

export default function IncubatorPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [nodes, setNodes] = useState<any[]>([])
  const [edges, setEdges] = useState<any[]>([])

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectApi.getById(projectId!),
    enabled: !!projectId,
  })

  const { data: mindmapNodes = [], isLoading: nodesLoading } = useQuery({
    queryKey: ['mindmap', projectId],
    queryFn: () => nodeApi.getByProject(projectId!),
    enabled: !!projectId,
  })

  useEffect(() => {
    const flowNodes = mindmapNodes.map((node: MindmapNode) => ({
      id: node.id,
      type: 'mindmapNode',
      position: node.position || { x: Math.random() * 500, y: Math.random() * 500 },
      data: {
        label: node.label,
        status: node.status,
        question: node.question,
        context: node.context,
        answer: node.answer,
        extractedPoints: node.extracted_points,
        depth: node.depth,
      },
    }))

    const flowEdges = mindmapNodes
      .filter((node: MindmapNode) => node.parent_id)
      .map((node: MindmapNode) => ({
        id: `e-${node.parent_id}-${node.id}`,
        source: node.parent_id!,
        target: node.id,
        animated: true,
        style: { stroke: '#94a3b8', strokeWidth: 2 },
      }))

    setNodes(flowNodes)
    setEdges(flowEdges)
  }, [mindmapNodes])

  const onNodesChange = useCallback((changes: any) => {
    setNodes((nds) => {
      const updated = applyNodeChanges(nds, changes)
      // Sync with backend
      changes.forEach((change: any) => {
        if (change.type === 'position' && change.dragging) {
          // Optional: Debounced save position
        }
      })
      return updated
    })
  }, [])

  const onConnect = useCallback((params: any) => {
    setEdges((eds) => addEdge(params, eds))
  }, [])

  if (projectLoading || nodesLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spin size="large" tip="加载思维导图..." />
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-sky-50">
      <div className="bg-white border-b border-sky-200 px-6 py-3 flex items-center gap-4">
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/projects')}
        >
          返回
        </Button>
        <h1 className="text-xl font-semibold text-slate-800">{project?.title}</h1>
      </div>

      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Background color="#f0f9ff" gap={16} />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              switch (node.data.status) {
                case 'answered':
                  return '#10b981'
                case 'in_progress':
                  return '#0ea5e9'
                default:
                  return '#94a3b8'
              }
            }}
            maskColor="rgb(240, 249, 255, 0.6)"
          />
        </ReactFlow>
      </div>
    </div>
  )
}
