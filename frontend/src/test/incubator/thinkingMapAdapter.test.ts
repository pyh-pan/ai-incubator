import { describe, expect, it } from 'vitest'
import { buildMindElixirData } from '../../components/incubator/thinkingMapAdapter'
import type { ThinkingNode } from '../../types/incubator'

const baseNode = (overrides: Partial<ThinkingNode>): ThinkingNode => ({
  id: 'node-1',
  project_id: 'project-1',
  parent_id: null,
  kind: 'idea',
  status: 'confirmed',
  title: 'Root idea',
  summary: null,
  question: null,
  answer_summary: null,
  sort_order: 0,
  layout: null,
  source_message_ids: [],
  confidence: 100,
  created_at: '2026-04-25T00:00:00',
  updated_at: '2026-04-25T00:00:00',
  ...overrides,
})

describe('buildMindElixirData', () => {
  it('builds a root with children from flat nodes', () => {
    const data = buildMindElixirData([
      baseNode({ id: 'root', title: 'AI diary', kind: 'idea' }),
      baseNode({ id: 'child', parent_id: 'root', title: 'Target user', kind: 'question', status: 'open' }),
    ])

    expect(data.nodeData.id).toBe('root')
    expect(data.nodeData.children?.[0].id).toBe('child')
    expect(data.nodeData.children?.[0].topic).toContain('Target user')
  })

  it('creates fallback root when node list is empty', () => {
    const data = buildMindElixirData([])

    expect(data.nodeData.topic).toBe('Untitled idea')
  })
})
