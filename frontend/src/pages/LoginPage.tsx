import { Form, Input, Button, message, Card, Typography } from 'antd'
import { useNavigate, Link } from 'react-router-dom'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '../api'
import type { ApiError, LoginRequest } from '../types'
import { useAuthStore } from '../stores/authStore'

const { Text } = Typography

export default function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [form] = Form.useForm()

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setAuth(data.user, data.access_token)
      message.success('登录成功')
      navigate('/projects')
    },
    onError: (error: ApiError) => {
      message.error(error.response?.data?.detail || '登录失败')
    },
  })

  const onFinish = (values: LoginRequest) => {
    loginMutation.mutate(values)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 to-sky-100 flex items-center justify-center p-6">
      <Card className="w-full max-w-md shadow-lg animate-fade-in">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-sky-600 mb-2">AI Incubator</h1>
          <Text className="text-slate-600">登录到你的账户</Text>
        </div>

        <Form
          form={form}
          name="login"
          onFinish={onFinish}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input
              prefix={<UserOutlined className="text-slate-400" />}
              placeholder="邮箱"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined className="text-slate-400" />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              loading={loginMutation.isPending}
            >
              登录
            </Button>
          </Form.Item>

          <div className="text-center">
            <Text className="text-slate-600">
              还没有账户？{' '}
              <Link to="/register" className="text-sky-600 font-medium">
                立即注册
              </Link>
            </Text>
          </div>
        </Form>
      </Card>
    </div>
  )
}
