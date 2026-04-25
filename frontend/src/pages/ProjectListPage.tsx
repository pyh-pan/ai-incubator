import { useState } from 'react'
import { Button, Card, Modal, Form, Input, Select, message, Empty, Tag, Popconfirm } from 'antd'
import { useNavigate } from 'react-router-dom'
import { PlusOutlined, DeleteOutlined, RocketOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectApi } from '../api'
import type { FrameworkType, Project } from '../types'
import { formatDistanceToNow } from 'date-fns'

const { TextArea } = Input

export default function ProjectListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectApi.list(),
  })

  const createMutation = useMutation({
    mutationFn: projectApi.create,
    onSuccess: () => {
      message.success('项目创建成功')
      setIsModalOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '创建失败')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: projectApi.delete,
    onSuccess: () => {
      message.success('项目已删除')
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除失败')
    },
  })

  const handleCreate = (values: any) => {
    createMutation.mutate(values)
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id)
  }

  const frameworkOptions: { label: string; value: FrameworkType }[] = [
    { label: '产品经理框架', value: 'product_manager' },
    { label: '商业模式画布', value: 'business_canvas' },
    { label: '技术可行性', value: 'technical_feasibility' },
    { label: '苏格拉底式追问', value: 'socratic' },
  ]

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-800">我的项目</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setIsModalOpen(true)}
          size="large"
        >
          创建新项目
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <span className="text-slate-500">加载中...</span>
        </div>
      ) : !projects || projects.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div className="text-center">
              <p className="text-slate-600 mb-4">还没有项目</p>
              <p className="text-slate-500 text-sm">创建你的第一个想法孵化项目</p>
            </div>
          }
        />
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project: Project) => (
            <Card
              key={project.id}
              hoverable
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => navigate(`/projects/${project.id}`)}
              actions={[
                <Popconfirm
                  title="确定删除这个项目吗？"
                  onConfirm={(e) => {
                    e?.stopPropagation()
                    handleDelete(project.id)
                  }}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => e.stopPropagation()}
                  >
                    删除
                  </Button>
                </Popconfirm>,
              ]}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 bg-sky-100 rounded-lg flex items-center justify-center">
                  <RocketOutlined className="text-sky-600" />
                </div>
                <Tag color="sky">{frameworkOptions.find(f => f.value === project.framework)?.label}</Tag>
              </div>
              <h3 className="text-lg font-semibold text-slate-800 mb-2 line-clamp-2">
                {project.title}
              </h3>
              <p className="text-sm text-slate-500">
                创建于 {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
              </p>
            </Card>
          ))}
        </div>
      )}

      <Modal
        title="创建新项目"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
        >
          <Form.Item
            name="title"
            label="想法标题"
            rules={[{ required: true, message: '请输入想法标题' }]}
          >
            <TextArea
              rows={3}
              placeholder="例如：AI 写日记工具、智能学习助手..."
              showCount
              maxLength={200}
            />
          </Form.Item>

          <Form.Item
            name="framework"
            label="思维框架"
            rules={[{ required: true, message: '请选择思维框架' }]}
            initialValue="product_manager"
          >
            <Select options={frameworkOptions} placeholder="选择一个思维框架" />
          </Form.Item>

          <Form.Item className="mb-0">
            <Button type="primary" htmlType="submit" block loading={createMutation.isPending}>
              开始孵化
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
