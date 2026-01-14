import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import Sidebar from './components/Sidebar'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import NewsGenerator from './pages/NewsGenerator'
import AnalysisReport from './pages/AnalysisReport'
import ChatAssistant from './pages/ChatAssistant'
import Settings from './pages/Settings'
import './App.css'

const { Content } = Layout

function App() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Navigate to="/dashboard" replace />
            </ProtectedRoute>
          }
        />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout style={{ minHeight: '100vh' }}>
                <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
                <Layout style={{ marginLeft: collapsed ? 80 : 250, transition: 'margin-left 0.2s' }}>
                  <Content style={{ margin: '16px', padding: '24px', background: '#fff', borderRadius: '8px', minHeight: 'calc(100vh - 32px)' }}>
                    <Routes>
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/news" element={<NewsGenerator />} />
                      <Route path="/report" element={<AnalysisReport />} />
                      <Route path="/chat" element={<ChatAssistant />} />
                      <Route path="/settings" element={<Settings />} />
                    </Routes>
                  </Content>
                </Layout>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  )
}

export default App
