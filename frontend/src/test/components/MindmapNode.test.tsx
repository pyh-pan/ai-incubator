import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import MindmapNode from '../../components/mindmap/MindmapNode'
import { ReactFlowProvider } from 'reactflow'

describe('MindmapNode', () => {
  const mockNode = {
    id: '1',
    type: 'mindmapNode',
    data: {
      label: '目标用户',
      status: 'unanswered',
      question: '谁是你的目标用户？',
      context: '了解目标用户有助于后续功能设计',
      answer: null,
      extractedPoints: null,
      depth: 1,
    },
    position: { x: 0, y: 0 },
  }

  it('renders node label correctly', () => {
    render(
      <ReactFlowProvider>
        <MindmapNode {...mockNode} selected={false} />
      </ReactFlowProvider>
    )
    expect(screen.getByText('目标用户')).toBeInTheDocument()
  })

  it('shows question icon for unanswered status', () => {
    render(
      <ReactFlowProvider>
        <MindmapNode {...mockNode} selected={false} />
      </ReactFlowProvider>
    )
    const icon = screen.getByRole('img', { hidden: true })
    expect(icon).toHaveClass('text-slate-400')
  })

  it('applies correct styling for unanswered status', () => {
    const { container } = render(
      <ReactFlowProvider>
        <MindmapNode {...mockNode} selected={false} />
      </ReactFlowProvider>
    )
    const nodeElement = container.firstChild as HTMLElement
    expect(nodeElement).toHaveClass('bg-white')
    expect(nodeElement).toHaveClass('border-slate-300')
    expect(nodeElement).toHaveClass('border-dashed')
  })

  it('applies correct styling for answered status', () => {
    const answeredNode = {
      ...mockNode,
      data: {
        ...mockNode.data,
        status: 'answered' as const,
        answer: '新用户',
        extractedPoints: ['想开始写日记', '难以坚持习惯'],
      },
    }
    const { container } = render(
      <ReactFlowProvider>
        <MindmapNode {...answeredNode} selected={false} />
      </ReactFlowProvider>
    )
    const nodeElement = container.firstChild as HTMLElement
    expect(nodeElement).toHaveClass('bg-emerald-50')
    expect(nodeElement).toHaveClass('border-emerald-400')
  })

  it('shows card on hover', async () => {
    render(
      <ReactFlowProvider>
        <MindmapNode {...mockNode} selected={false} />
      </ReactFlowProvider>
    )

    const nodeElement = screen.getByText('目标用户').closest('div')
    fireEvent.mouseEnter(nodeElement!)

    await waitFor(() => {
      expect(screen.getByText('问题：')).toBeInTheDocument()
      expect(screen.getByText('谁是你的目标用户？')).toBeInTheDocument()
    })
  })

  it('opens fixed card on click', async () => {
    render(
      <ReactFlowProvider>
        <MindmapNode {...mockNode} selected={false} />
      </ReactFlowProvider>
    )

    const nodeElement = screen.getByText('目标用户').closest('div')
    fireEvent.click(nodeElement!)

    await waitFor(() => {
      expect(screen.getByText('点击回答')).toBeInTheDocument()
    })
  })
})
