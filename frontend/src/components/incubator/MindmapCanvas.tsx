import { useEffect, useRef, useState } from 'react'
import MindElixir from 'mind-elixir'
import 'mind-elixir/style.css'
import type { MindElixirInstance, NodeObj } from 'mind-elixir'
import type { ThinkingNode } from '../../types/incubator'
import { buildMindElixirData } from './thinkingMapAdapter'

interface MindmapCanvasProps {
  nodes: ThinkingNode[]
  selectedNodeId: string | null
  onSelectNode: (node: ThinkingNode) => void
}

const kindLabel: Record<ThinkingNode['kind'], string> = {
  idea: '想法',
  question: '问题',
  answer: '回答',
  insight: '洞察',
  assumption: '假设',
  decision: '决策',
  risk: '风险',
  next_step: '下一步',
}

function getNodeDepth(node: ThinkingNode, nodesById: Map<string, ThinkingNode>) {
  let depth = 0
  let parentId = node.parent_id
  while (parentId && nodesById.has(parentId) && depth < 8) {
    depth += 1
    parentId = nodesById.get(parentId)?.parent_id ?? null
  }
  return depth
}

export default function MindmapCanvas({ nodes, selectedNodeId, onSelectNode }: MindmapCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const instanceRef = useRef<MindElixirInstance | null>(null)
  const nodeMapRef = useRef(new Map<string, ThinkingNode>())
  const [failed, setFailed] = useState(false)

  nodeMapRef.current = new Map(nodes.map((node) => [node.id, node]))

  useEffect(() => {
    if (!containerRef.current) return

    try {
      const data = buildMindElixirData(nodes)

      if (!instanceRef.current) {
        const instance = new MindElixir({
          el: containerRef.current,
          direction: MindElixir.SIDE,
          editable: false,
          contextMenu: false,
          toolBar: true,
          keypress: true,
          overflowHidden: false,
        })

        instance.init(data)
        instance.bus.addListener('selectNodes', (selectedNodes: NodeObj[]) => {
          const selected = selectedNodes[0] ? nodeMapRef.current.get(selectedNodes[0].id) : null
          if (selected) onSelectNode(selected)
        })
        instanceRef.current = instance
      } else {
        instanceRef.current.refresh(data)
      }

      instanceRef.current.toCenter()
      setFailed(false)
    } catch {
      setFailed(true)
    }
  }, [nodes, onSelectNode])

  useEffect(() => {
    return () => {
      instanceRef.current?.destroy()
      instanceRef.current = null
    }
  }, [])

  if (!failed) {
    return <section ref={containerRef} className="h-full w-full bg-white" />
  }

  const nodesById = new Map(nodes.map((node) => [node.id, node]))

  return (
    <section className="h-full min-h-0 bg-slate-50 overflow-auto p-6">
      <div className="min-w-[720px]">
        <div className="text-sm font-semibold text-slate-700 mb-4">思维导图</div>
        <div className="grid gap-3">
          {nodes.map((node) => {
            const depth = getNodeDepth(node, nodesById)
            return (
              <button
                key={node.id}
                type="button"
                onClick={() => onSelectNode(node)}
                className={`text-left rounded-lg border px-4 py-3 bg-white transition ${
                  selectedNodeId === node.id ? 'border-sky-500 shadow-md' : 'border-slate-200 hover:border-sky-300'
                }`}
                style={{ marginLeft: depth * 32 }}
              >
                <div className="text-xs text-slate-500">
                  {kindLabel[node.kind]} · {node.status}
                </div>
                <div className="font-medium text-slate-900 break-words">{node.title}</div>
                {node.summary && <div className="text-sm text-slate-600 mt-1 break-words">{node.summary}</div>}
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}
