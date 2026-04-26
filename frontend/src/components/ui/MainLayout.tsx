import { Outlet, useNavigate } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown } from 'antd'
import { LogoutOutlined, UserOutlined, PlusOutlined } from '@ant-design/icons'
import type { ReactNode } from 'react'
import { useAuthStore } from '../../stores/authStore'

export default function MainLayout({ children }: { children?: ReactNode }) {
  const navigate = useNavigate()
  const { user, clearAuth } = useAuthStore()

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  const menuItems = [
    {
      key: 'projects',
      label: '我的项目',
      onClick: () => navigate('/projects'),
    },
    {
      key: 'new',
      label: '创建新项目',
      icon: <PlusOutlined />,
      onClick: () => navigate('/projects/new'),
    },
  ]

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout className="min-h-screen bg-sky-50">
      <Layout.Header className="bg-white border-b border-sky-200 px-3 sm:px-6 sticky top-0 z-50 shadow-sm">
        <div className="flex items-center justify-between gap-3 max-w-7xl mx-auto">
          <div className="flex items-center gap-4 shrink-0">
            <h1
              className="text-xl sm:text-2xl font-semibold leading-none whitespace-nowrap text-sky-600 cursor-pointer"
              onClick={() => navigate('/projects')}
            >
              AI Incubator
            </h1>
          </div>

          <Menu
            mode="horizontal"
            items={menuItems}
            className="border-0 bg-transparent hidden sm:flex flex-1 justify-center min-w-0"
          />

          <div className="flex items-center gap-2 shrink-0">
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div className="flex items-center gap-2 cursor-pointer hover:bg-sky-50 px-2 sm:px-3 py-2 rounded-lg transition-colors">
                <Avatar size="default" className="bg-sky-500">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </Avatar>
                <span className="hidden sm:inline text-sm text-slate-700">{user?.username || 'User'}</span>
              </div>
            </Dropdown>
          </div>
        </div>
      </Layout.Header>

      <Layout.Content className="p-6">
        {children ?? <Outlet />}
      </Layout.Content>
    </Layout>
  )
}
