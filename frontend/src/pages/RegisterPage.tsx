import { Form, Input, Button, message, Card, Typography } from 'antd'
import { useNavigate, Link } from 'react-router-dom'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '../api'
import { useAuthStore } from '../stores/authStore'

const { Text } = Typography

export default function RegisterPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [form] = Form.useForm()

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      setAuth(data.user, data.access_token)
      message.success('注册成功')
      navigate('/projects')
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '注册失败')
    },
  })

  const onFinish = (values: any) => {
    registerMutation.mutate(values)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 to-sky-100 flex items-center justify-center p-6">
      <Card className="w-full max-w-md shadow-lg animate-fade-in">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-sky-600 mb-2">AI Incubator</h1>
          <Text className="text-slate-600">创建新账户</Text>
        </div>

        <Form
          form={form}
          name="register"
          onFinish={onFinish}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 2, message: '用户名至少2个字符' },
            ]}
          >
            <Input
              prefix={<UserOutlined className="text-slate-400" />}
              placeholder="用户名"
            />
          </Form.Item>

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
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined className="text-slate-400" />}
              placeholder="密码（至少6个字符）"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined className="text-slate-400" />}
              placeholder="确认密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              loading={registerMutation.isPending}
            >
              注册
            </Button>
          </Form.Item>

          <div className="text-center">
            <Text className="text-slate-600">
              已有账户？{' '}
              <Link to="/login" className="text-sky-600 font-medium">
                立即登录
              </Link>
            </Text>
          </div>
        </Form>
      </Card>
    </div>
  )
}
