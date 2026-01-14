import React, { useState, useEffect } from 'react'
import { Button, Card, List, Spin, message, Empty, Popconfirm } from 'antd'
import { FileTextOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../utils/axios'

const NewsGenerator = () => {
  const [loading, setLoading] = useState(false)
  const [loadingList, setLoadingList] = useState(false)
  const [newsList, setNewsList] = useState([])

  // 页面加载时获取已生成的新闻
  useEffect(() => {
    fetchNewsList()
  }, [])

  // 获取新闻列表
  const fetchNewsList = async () => {
    setLoadingList(true)
    try {
      const response = await api.get('/news/list', {
        params: {
          skip: 0,
          limit: 50  // 获取最近50条
        }
      })
      // 按采集时间倒序排列（最新的在前）
      const sortedNews = response.data.sort((a, b) => {
        const timeA = new Date(a.collected_at || a.publish_time || 0)
        const timeB = new Date(b.collected_at || b.publish_time || 0)
        return timeB - timeA
      })
      setNewsList(sortedNews)
    } catch (error) {
      console.error('获取新闻列表失败:', error)
      // 不显示错误消息，避免干扰用户体验
    } finally {
      setLoadingList(false)
    }
  }

  // 生成新新闻
  const handleGenerate = async () => {
    setLoading(true)
    try {
      const response = await api.post('/news/generate-daily')
      message.success('成功生成5条今日体育新闻！')
      // 生成成功后，重新获取新闻列表
      await fetchNewsList()
    } catch (error) {
      console.error('生成新闻失败:', error)
      message.error(error.response?.data?.detail || '生成新闻失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  // 删除新闻
  const handleDelete = async (newsId, title) => {
    try {
      await api.delete(`/news/${newsId}`)
      message.success(`已删除新闻：${title}`)
      // 删除成功后，重新获取新闻列表
      await fetchNewsList()
    } catch (error) {
      console.error('删除新闻失败:', error)
      message.error(error.response?.data?.detail || '删除新闻失败，请稍后重试')
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>体育日报生成</h1>
        <Button
          type="primary"
          icon={<ReloadOutlined />}
          onClick={handleGenerate}
          loading={loading}
          size="large"
        >
          生成今日日报
        </Button>
      </div>

      {loadingList ? (
        <Spin size="large" style={{ display: 'block', textAlign: 'center', marginTop: '50px' }} />
      ) : loading ? (
        <Spin size="large" style={{ display: 'block', textAlign: 'center', marginTop: '50px' }} />
      ) : newsList.length > 0 ? (
        <div>
          <div style={{ marginBottom: '16px', color: '#666', fontSize: '14px' }}>
            共 {newsList.length} 条新闻（按时间倒序）
          </div>
          <List
            grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2, xl: 2, xxl: 2 }}
            dataSource={newsList}
            renderItem={(item) => (
              <List.Item>
                <Card
                  title={
                    <span>
                      <FileTextOutlined style={{ marginRight: '8px' }} />
                      {item.title}
                    </span>
                  }
                  extra={
                    <Popconfirm
                      title="确定要删除这条新闻吗？"
                      description="删除后无法恢复"
                      onConfirm={() => handleDelete(item.id, item.title)}
                      okText="确定"
                      cancelText="取消"
                      okButtonProps={{ danger: true }}
                    >
                      <Button
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        size="small"
                        style={{ padding: '0 4px' }}
                      />
                    </Popconfirm>
                  }
                  style={{ height: '100%' }}
                  hoverable
                >
                  <p style={{ color: '#666', marginBottom: '12px', minHeight: '60px' }}>
                    {item.content && item.content.length > 150 
                      ? `${item.content.substring(0, 150)}...` 
                      : item.content || '暂无内容'}
                  </p>
                  <div style={{ fontSize: '12px', color: '#999' }}>
                    <div>来源：{item.source || '未知'}</div>
                    <div>
                      采集时间：{item.collected_at 
                        ? new Date(item.collected_at).toLocaleString('zh-CN')
                        : item.publish_time 
                        ? new Date(item.publish_time).toLocaleString('zh-CN')
                        : '未知'}
                    </div>
                    {item.source_url && (
                      <div style={{ marginTop: '8px' }}>
                        <a href={item.source_url} target="_blank" rel="noopener noreferrer" style={{ color: '#1890ff' }}>
                          查看原文
                        </a>
                      </div>
                    )}
                  </div>
                </Card>
              </List.Item>
            )}
          />
        </div>
      ) : (
        <Empty description="点击上方按钮生成今日体育新闻日报" />
      )}
    </div>
  )
}

export default NewsGenerator
