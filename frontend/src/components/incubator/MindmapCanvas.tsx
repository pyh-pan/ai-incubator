import { useMemo, useState } from 'react'
import type { CenterContext, ThinkingNode } from '../../types/incubator'
import NodePopover from './NodePopover'

interface MindmapCanvasProps {
  nodes: ThinkingNode[]
  centerContext: CenterContext
  selectedNodeId: string | null
  isThinking: boolean
  onSelectNode: (node: ThinkingNode | null) => void
  onAnswerNode: (nodeId: string, content: string) => void
}

interface LayoutNode {
  node: ThinkingNode
  x: number
  y: number
  width: number
  height: number
  depth: number
}

const NODE_WIDTH = 264
const NODE_HEIGHT = 82
const ROOT_WIDTH = 286
const ROOT_HEIGHT = 92
const GAP_X = 356
const GAP_Y = 28
const TOP_PAD = 42
const LEFT_PAD = 48

const statusText: Record<ThinkingNode['status'], string> = {
  open: '待回答',
  answered: '已回答',
  suggested: '建议',
  confirmed: '确认',
  needs_context: '补背景',
  resolved: '完成',
}

const nodeAccent = ['#2563eb', '#0891b2', '#d97706', '#16a34a', '#dc2626']

function sortNodes(nodes: ThinkingNode[]) {
  return [...nodes].sort((a, b) => a.sort_order - b.sort_order || a.created_at.localeCompare(b.created_at))
}

function buildLayout(nodes: ThinkingNode[]) {
  if (nodes.length === 0) return { layoutNodes: [] as LayoutNode[], width: 720, height: 360, links: [] as [LayoutNode, LayoutNode][] }

  const byParent = new Map<string | null, ThinkingNode[]>()
  sortNodes(nodes).forEach((node) => {
    const key = node.parent_id && nodes.some((candidate) => candidate.id === node.parent_id) ? node.parent_id : null
    byParent.set(key, [...(byParent.get(key) ?? []), node])
  })

  const root = byParent.get(null)?.[0] ?? nodes[0]
  const layoutNodes: LayoutNode[] = []
  let nextY = TOP_PAD

  const walk = (node: ThinkingNode, depth: number): LayoutNode => {
    const children = sortNodes(byParent.get(node.id) ?? [])
    const width = depth === 0 ? ROOT_WIDTH : NODE_WIDTH
    const height = depth === 0 ? ROOT_HEIGHT : NODE_HEIGHT
    const childLayouts = children.map((child) => walk(child, depth + 1))
    const y =
      childLayouts.length > 0
        ? (childLayouts[0].y + childLayouts[childLayouts.length - 1].y) / 2
        : (() => {
            const current = nextY
            nextY += height + GAP_Y
            return current
          })()
    const layoutNode = { node, x: LEFT_PAD + depth * GAP_X, y, width, height, depth }
    layoutNodes.push(layoutNode)
    return layoutNode
  }

  walk(root, 0)

  const byId = new Map(layoutNodes.map((item) => [item.node.id, item]))
  const links: [LayoutNode, LayoutNode][] = []
  layoutNodes.forEach((item) => {
    if (!item.node.parent_id) return
    const parent = byId.get(item.node.parent_id)
    if (parent) links.push([parent, item])
  })

  const width = Math.max(760, Math.max(...layoutNodes.map((item) => item.x + item.width)) + 420)
  const height = Math.max(420, Math.max(...layoutNodes.map((item) => item.y + item.height)) + 100)
  return { layoutNodes, width, height, links }
}

function connectorPath(parent: LayoutNode, child: LayoutNode) {
  const startX = parent.x + parent.width
  const startY = parent.y + parent.height / 2
  const endX = child.x
  const endY = child.y + child.height / 2
  const mid = Math.max(96, (endX - startX) * 0.48)
  return `M ${startX} ${startY} C ${startX + mid} ${startY}, ${endX - mid} ${endY}, ${endX} ${endY}`
}

function nodeText(node: ThinkingNode) {
  if (node.kind === 'idea') return node.title
  return node.title || node.question || '未命名问题'
}

export default function MindmapCanvas({
  nodes,
  centerContext,
  selectedNodeId,
  isThinking,
  onSelectNode,
  onAnswerNode,
}: MindmapCanvasProps) {
  const [popoverNodeId, setPopoverNodeId] = useState<string | null>(null)
  const { layoutNodes, width, height, links } = useMemo(() => buildLayout(nodes), [nodes])
  const selectedLayout = layoutNodes.find((item) => item.node.id === (popoverNodeId ?? selectedNodeId)) ?? null

  const selectNode = (node: ThinkingNode) => {
    setPopoverNodeId(node.id)
    onSelectNode(node)
  }

  return (
    <section className="relative h-full min-h-0 overflow-auto bg-[#f7f9fb]">
      <div className="absolute left-5 top-4 z-10 rounded-md border border-slate-200 bg-white/90 px-3 py-2 text-xs text-slate-500 shadow-sm">
        {nodes.filter((node) => node.kind === 'question' || node.kind === 'followup').length} 个问题节点
      </div>

      <div className="relative" style={{ width, height }}>
        <svg className="absolute inset-0 pointer-events-none" width={width} height={height}>
          {links.map(([parent, child]) => (
            <path
              key={`${parent.node.id}-${child.node.id}`}
              d={connectorPath(parent, child)}
              fill="none"
              stroke={nodeAccent[child.depth % nodeAccent.length]}
              strokeLinecap="round"
              strokeWidth={child.node.status === 'answered' ? 3 : 2}
              opacity={child.node.status === 'answered' ? 0.72 : 0.42}
            />
          ))}
        </svg>

        {layoutNodes.map((item) => {
          const isRoot = item.depth === 0
          const selected = selectedNodeId === item.node.id || popoverNodeId === item.node.id
          const accent = nodeAccent[item.depth % nodeAccent.length]
          return (
            <button
              key={item.node.id}
              type="button"
              onClick={() => selectNode(item.node)}
              className={`absolute text-left transition duration-150 ${
                selected ? 'scale-[1.015] shadow-xl shadow-slate-300/80' : 'shadow-md shadow-slate-200/80 hover:shadow-lg'
              }`}
              style={{ left: item.x, top: item.y, width: item.width, height: item.height }}
            >
              <div
                className={`h-full w-full overflow-hidden rounded-lg border ${
                  isRoot ? 'border-blue-800 bg-blue-700 text-white' : 'border-slate-200 bg-white text-slate-900'
                }`}
              >
                {!isRoot && <div className="h-full w-1.5 float-left" style={{ backgroundColor: accent }} />}
                <div className={isRoot ? 'p-4' : 'p-3 pl-5'}>
                  <div className={`line-clamp-2 text-sm font-semibold leading-5 ${isRoot ? 'text-white' : 'text-slate-950'}`}>
                    {nodeText(item.node)}
                  </div>
                  {!isRoot && (
                    <div className="mt-2 flex items-center gap-2 text-[11px]">
                      <span className={item.node.status === 'answered' ? 'text-emerald-700' : 'text-slate-500'}>
                        {statusText[item.node.status]}
                      </span>
                      {item.node.kind === 'followup' && <span className="text-cyan-700">追问</span>}
                    </div>
                  )}
                  {isRoot && (
                    <div className="mt-2 text-xs leading-5 text-blue-100">
                      {centerContext.context_sufficiency === 'sufficient' ? '背景已形成' : '等待补充背景'}
                    </div>
                  )}
                </div>
              </div>
            </button>
          )
        })}

        {selectedLayout && (
          <div
            className="absolute z-20"
            style={{
              left:
                selectedLayout.depth === 0
                  ? selectedLayout.x + selectedLayout.width + 18
                  : Math.max(16, selectedLayout.x - 382),
              top: Math.max(16, selectedLayout.y - 22),
            }}
          >
            <NodePopover
              node={selectedLayout.node}
              centerContext={centerContext}
              isThinking={isThinking}
              onAnswerNode={onAnswerNode}
              onClose={() => {
                setPopoverNodeId(null)
                onSelectNode(null)
              }}
            />
          </div>
        )}
      </div>
    </section>
  )
}
