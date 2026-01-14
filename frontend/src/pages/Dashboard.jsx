import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Spin } from 'antd'
import { FileTextOutlined, BarChartOutlined } from '@ant-design/icons'
import api from '../utils/axios'
import { getUser } from '../utils/auth'

const Dashboard = () => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await api.get('/dashboard/stats')
      setStats(response.data)
    } catch (error) {
      console.error('获取统计数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <Spin size="large" style={{ display: 'block', textAlign: 'center', marginTop: '50px' }} />
  }

  const user = getUser()

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <h2 style={{ 
          margin: 0, 
          fontSize: '20px', 
          color: '#1890ff',
          fontWeight: 'normal'
        }}>
          {user?.username ? `${user.username}，你好！` : '你好！'}
        </h2>
      </div>
      <h1 style={{ marginBottom: '24px' }}>仪表板</h1>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日新闻"
              value={stats?.today_news_count || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总新闻数"
              value={stats?.total_news_count || 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日报告"
              value={stats?.today_reports_count || 0}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总报告数"
              value={stats?.total_reports_count || 0}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
