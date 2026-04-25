import { useState, useCallback } from 'react'
import { Handle, Position } from 'reactflow'
import type { NodeProps } from 'reactflow'
import { QuestionCircleOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import type { NodeStatus } from '../../types'

interface MindmapNodeData {
  label: string
  status: NodeStatus
  question?: string
  context?: string
  answer?: string
  extractedPoints?: string[]
  depth: number
}

interface CardPosition {
  x: number
  y: number
}

export default function MindmapNode({ data }: NodeProps<MindmapNodeData>) {
  const [showCard, setShowCard] = useState(false)
  const [cardPosition, setCardPosition] = useState<CardPosition>({ x: 0, y: 0 })
  const [isFixed, setIsFixed] = useState(false)

  const onMouseEnter = useCallback((e: React.MouseEvent) => {
    if (!isFixed) {
      const container = e.currentTarget.closest('.react-flow')
      if (!container) return

      const containerRect = container.getBoundingClientRect()
      const nodeRect = e.currentTarget.getBoundingClientRect()

      // Calculate position to avoid overflow
      let x = nodeRect.right - containerRect.left + 10
      let y = nodeRect.top - containerRect.top

      // Adjust if card would overflow right
      if (x + 400 > containerRect.width) {
        x = nodeRect.left - containerRect.left - 410
      }

      // Adjust if card would overflow bottom
      if (y + 300 > containerRect.height) {
        y = containerRect.height - 310
      }

      setCardPosition({ x, y })
      setShowCard(true)
    }
  }, [isFixed])

  const onMouseLeave = useCallback(() => {
    if (!isFixed) {
      setShowCard(false)
    }
  }, [isFixed])

  const onClick = useCallback(() => {
    setIsFixed(!isFixed)
  }, [isFixed])

  const getStatusIcon = () => {
    switch (data.status) {
      case 'answered':
        return <CheckCircleOutlined className="text-emerald-500" />
      case 'in_progress':
        return <ClockCircleOutlined className="text-sky-500" />
      default:
        return <QuestionCircleOutlined className="text-slate-400" />
    }
  }

  const getNodeStyle = () => {
    const baseStyle = "px-4 py-2 rounded-lg border-2 transition-all cursor-pointer "
    switch (data.status) {
      case 'answered':
        return `${baseStyle}bg-emerald-50 border-emerald-400 text-emerald-700`
      case 'in_progress':
        return `${baseStyle}bg-sky-50 border-sky-400 text-sky-700 shadow-md`
      default:
        return `${baseStyle}bg-white border-slate-300 border-dashed text-slate-500`
    }
  }

  return (
    <>
      <div
        className={getNodeStyle()}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
        onClick={onClick}
        style={{ minWidth: '120px', maxWidth: '200px' }}
      >
        <div className="flex items-center gap-2 mb-1">
          {getStatusIcon()}
          <span className="font-medium text-sm">{data.label}</span>
        </div>
        {data.question && (
          <p className="text-xs text-slate-600 line-clamp-2">{data.question}</p>
        )}
      </div>

      <Handle type="target" position={Position.Left} className="!bg-sky-400" />
      <Handle type="source" position={Position.Right} className="!bg-sky-400" />

      {showCard && !isFixed && (
        <div
          className="absolute bg-white rounded-xl shadow-2xl border border-slate-200 p-5 w-96 z-50 animate-fade-in"
          style={{
            left: cardPosition.x,
            top: cardPosition.y,
          }}
          onMouseEnter={() => setShowCard(true)}
          onMouseLeave={onMouseLeave}
        >
          <div className="flex items-start justify-between mb-3">
            <h4 className="text-lg font-semibold text-slate-800">{data.label}</h4>
            <button
              onClick={() => setShowCard(false)}
              className="text-slate-400 hover:text-slate-600"
            >
              ✕
            </button>
          </div>

          {data.question && (
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">问题：</p>
              <p className="text-sm text-slate-600">{data.question}</p>
            </div>
          )}

          {data.context && (
            <div className="mb-4">
              <p className="text-xs font-medium text-slate-700 mb-1">背景信息：</p>
              <p className="text-xs text-slate-600">{data.context}</p>
            </div>
          )}

          {data.answer && data.extractedPoints && (
            <div className="mb-4">
              <p className="text-xs font-medium text-slate-700 mb-1">核心观点：</p>
              <ul className="text-xs text-slate-600 list-disc list-inside">
                {data.extractedPoints.map((point, idx) => (
                  <li key={idx}>{point}</li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={onClick}
            className="w-full py-2 bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition-colors text-sm font-medium"
          >
            {isFixed ? '编辑回答' : '点击回答'}
          </button>
        </div>
      )}

      {isFixed && (
        <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl border border-slate-200 p-6 w-[500px] max-w-[90vw] max-h-[80vh] overflow-y-auto z-50">
          <div className="flex items-start justify-between mb-4">
            <h4 className="text-xl font-semibold text-slate-800">{data.label}</h4>
            <button
              onClick={() => setIsFixed(false)}
              className="text-slate-400 hover:text-slate-600 text-xl"
            >
              ✕
            </button>
          </div>

          {data.question && (
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">问题：</p>
              <p className="text-base text-slate-800">{data.question}</p>
            </div>
          )}

          {data.context && (
            <div className="mb-4 p-3 bg-sky-50 rounded-lg">
              <p className="text-xs font-medium text-slate-700 mb-1">背景信息：</p>
              <p className="text-sm text-slate-600">{data.context}</p>
            </div>
          )}

          <textarea
            className="w-full p-3 border border-slate-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-sky-400"
            rows={6}
            placeholder="在这里输入你的想法..."
            defaultValue={data.answer || ''}
          />

          <div className="flex gap-3 mt-4">
            <button className="flex-1 py-2 bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition-colors font-medium">
              提交回答
            </button>
            <button
              onClick={() => setIsFixed(false)}
              className="px-6 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
            >
              取消
            </button>
          </div>
        </div>
      )}
    </>
  )
}
