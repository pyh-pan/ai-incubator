import type { MindElixirData, NodeObj } from 'mind-elixir'
import type { ThinkingNode } from '../../types/incubator'

const kindText: Record<ThinkingNode['kind'], string> = {
  idea: '想法',
  question: '问题',
  answer: '回答',
  insight: '洞察',
  assumption: '假设',
  decision: '决策',
  risk: '风险',
  next_step: '下一步',
}

const branchColors: Record<ThinkingNode['kind'], string> = {
  idea: '#2563eb',
  question: '#7c3aed',
  answer: '#059669',
  insight: '#0891b2',
  assumption: '#d97706',
  decision: '#16a34a',
  risk: '#dc2626',
  next_step: '#4f46e5',
}

export function buildMindElixirData(nodes: ThinkingNode[]): MindElixirData {
  if (nodes.length === 0) {
    return { nodeData: { id: 'root', topic: 'Untitled idea', children: [] } }
  }

  const byId = new Map<string, NodeObj>()

  nodes.forEach((node) => {
    byId.set(node.id, {
      id: node.id,
      topic: node.title,
      tags: [kindText[node.kind], node.status],
      children: [],
      branchColor: branchColors[node.kind],
      note: node.summary ?? node.question ?? undefined,
    })
  })

  let root: NodeObj | null = null

  nodes.forEach((node) => {
    const current = byId.get(node.id)
    if (!current) return

    if (!node.parent_id || !byId.has(node.parent_id)) {
      if (!root) root = current
      return
    }

    const parent = byId.get(node.parent_id)
    parent?.children?.push(current)
  })

  const fallbackRoot = byId.values().next().value
  if (!fallbackRoot) {
    return { nodeData: { id: 'root', topic: 'Untitled idea', children: [] } }
  }

  return { nodeData: root ?? fallbackRoot }
}
