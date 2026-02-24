import { Button } from 'antd'
import { useNavigate } from 'react-router-dom'
import { BulbOutlined, ThunderboltOutlined, RocketOutlined } from '@ant-design/icons'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 to-sky-100">
      <nav className="bg-white border-b border-sky-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-sky-600">AI Incubator</h1>
          <div className="flex gap-3">
            <Button type="default" onClick={() => navigate('/login')}>
              登录
            </Button>
            <Button type="primary" onClick={() => navigate('/register')}>
              注册
            </Button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-16 animate-fade-in">
          <h2 className="text-5xl font-bold text-slate-800 mb-6">
            让想法孵化成可执行的概念
          </h2>
          <p className="text-xl text-slate-600 mb-8 max-w-2xl mx-auto">
            AI 驱动的想法完善工具，通过提问刺激思考，以思维导图可视化，帮助你从模糊到清晰
          </p>
          <div className="flex gap-4 justify-center">
            <Button type="primary" size="large" onClick={() => navigate('/register')}>
              开始使用
            </Button>
            <Button size="large" onClick={() => navigate('/login')}>
              了解更多
            </Button>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white p-8 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 bg-sky-100 rounded-xl flex items-center justify-center mb-4">
              <BulbOutlined className="text-2xl text-sky-600" />
            </div>
            <h3 className="text-xl font-semibold text-slate-800 mb-3">智能提问</h3>
            <p className="text-slate-600">
              AI 基于你的想法动态生成问题，引导你深入思考，发现思维盲区
            </p>
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 bg-sky-100 rounded-xl flex items-center justify-center mb-4">
              <ThunderboltOutlined className="text-2xl text-sky-600" />
            </div>
            <h3 className="text-xl font-semibold text-slate-800 mb-3">思维导图</h3>
            <p className="text-slate-600">
              可视化你的思考过程，自由切换分支，保留完整的演化历史
            </p>
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 bg-sky-100 rounded-xl flex items-center justify-center mb-4">
              <RocketOutlined className="text-2xl text-sky-600" />
            </div>
            <h3 className="text-xl font-semibold text-slate-800 mb-3">灵活框架</h3>
            <p className="text-slate-600">
              产品经理、商业模式、技术可行性等多种框架，适应不同类型想法
            </p>
          </div>
        </div>

        <div className="bg-sky-600 rounded-2xl p-12 text-center text-white">
          <h3 className="text-2xl font-bold mb-4">准备好孵化你的想法了吗？</h3>
          <p className="text-sky-100 mb-6 text-lg">
            加入数千名创作者和创业者，开始你的想法孵化之旅
          </p>
          <Button type="primary" size="large" className="bg-white text-sky-600 hover:bg-sky-50" onClick={() => navigate('/register')}>
            免费开始
          </Button>
        </div>
      </main>

      <footer className="bg-slate-800 text-slate-300 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p>© 2026 AI Incubator. 想法孵化，从模糊到清晰。</p>
        </div>
      </footer>
    </div>
  )
}
