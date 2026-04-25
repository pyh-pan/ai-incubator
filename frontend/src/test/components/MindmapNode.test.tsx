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

  const renderNode = (node = mockNode) =>
    render(
      <ReactFlowProvider>
        <div className="react-flow">
          <MindmapNode {...node} selected={false} />
        </div>
      </ReactFlowProvider>
    )

  it('renders node label correctly', () => {
    renderNode()
    expect(screen.getByText('目标用户')).toBeInTheDocument()
  })

  it('shows question icon for unanswered status', () => {
    renderNode()
    const icon = screen.getByRole('img', { hidden: true })
    expect(icon).toHaveClass('text-slate-400')
  })

  it('applies correct styling for unanswered status', () => {
    const { container } = renderNode()
    const nodeElement = container.querySelector('.cursor-pointer') as HTMLElement
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
    const { container } = renderNode(answeredNode)
    const nodeElement = container.querySelector('.cursor-pointer') as HTMLElement
    expect(nodeElement).toHaveClass('bg-emerald-50')
    expect(nodeElement).toHaveClass('border-emerald-400')
  })

  it('shows card on hover', async () => {
    renderNode()

    const nodeElement = screen.getByText('目标用户').closest('.cursor-pointer')
    fireEvent.mouseEnter(nodeElement!)

    await waitFor(() => {
      expect(screen.getByText('问题：')).toBeInTheDocument()
      expect(screen.getAllByText('谁是你的目标用户？')).toHaveLength(2)
    })
  })

  it('opens fixed card on click', async () => {
    renderNode()

    const nodeElement = screen.getByText('目标用户').closest('.cursor-pointer')
    fireEvent.click(nodeElement!)

    await waitFor(() => {
      expect(screen.getByText('提交回答')).toBeInTheDocument()
    })
  })
})
