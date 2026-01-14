import React, { useState, useEffect } from 'react'
import { Button, Card, List, Spin, message, Empty, Tag, Popconfirm, Descriptions, Collapse, Tooltip, Progress, Modal } from 'antd'
import { BarChartOutlined, ReloadOutlined, DeleteOutlined, EyeOutlined, DownloadOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../utils/axios'
import './AnalysisReport.css'

const AnalysisReport = () => {
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [reports, setReports] = useState([])
  const [progressVisible, setProgressVisible] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState('')

  useEffect(() => {
    fetchReports()
  }, [])

  const fetchReports = async () => {
    setLoading(true)
    try {
      const response = await api.get('/report/list?limit=10')
      setReports(response.data)
    } catch (error) {
      console.error('获取报告列表失败:', error)
      message.error('获取报告列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    setAnalyzing(true)
    setProgressVisible(true)
    setProgress(0)
    setProgressMessage('开始分析...')
    
    // 获取token用于SSE请求
    const token = localStorage.getItem('sports_analysis_token')
    if (!token) {
      message.error('未登录，请先登录')
      setAnalyzing(false)
      setProgressVisible(false)
      return
    }
    
    // 获取API基础URL
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin.replace(':5173', ':8000')
    const apiUrl = `${apiBaseUrl}/api/report/analyze`
    
    // 使用fetch + ReadableStream接收SSE事件
    let reader = null
    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache'
        }
      })
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('没有需要分析的新闻，请先生成今日日报')
        } else if (response.status === 401) {
          throw new Error('未登录或token已过期，请重新登录')
        } else {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
      }
      
      if (!response.body) {
        throw new Error('响应体为空')
      }
      
      reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留最后一个不完整的行
        
        for (const line of lines) {
          if (line.trim() === '') continue
          
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6).trim()
              if (!jsonStr) continue
              
              const data = JSON.parse(jsonStr)
              
              if (data.status === 'success') {
                setProgress(100)
                setProgressMessage('报告生成完成！')
                message.success('分析完成！')
                // 刷新报告列表
                await fetchReports()
                // 延迟关闭进度条，让用户看到完成状态
                setTimeout(() => {
                  setProgressVisible(false)
                  setAnalyzing(false)
                }, 1500)
                return
              } else if (data.status === 'error') {
                setProgressVisible(false)
                setAnalyzing(false)
                message.error(data.error || data.message || '分析失败')
                return
              } else {
                setProgress(data.progress || 0)
                setProgressMessage(data.message || '处理中...')
              }
            } catch (e) {
              console.error('解析SSE数据失败:', e, '原始数据:', line)
            }
          }
        }
      }
    } catch (error) {
      console.error('分析失败:', error)
      setProgressVisible(false)
      setAnalyzing(false)
      
      if (error.message?.includes('timeout') || error.name === 'TimeoutError') {
        message.error('分析超时，LLM生成报告需要较长时间。请检查网络连接或稍后重试。')
      } else if (error.message?.includes('404') || error.message?.includes('没有需要分析的新闻')) {
        message.warning(error.message || '没有需要分析的新闻，请先生成今日日报')
      } else if (error.message?.includes('401') || error.message?.includes('未登录')) {
        message.error(error.message || '未登录，请先登录')
      } else {
        message.error(error.message || '分析失败，请稍后重试')
      }
    } finally {
      // 清理reader
      if (reader) {
        try {
          reader.cancel()
        } catch (e) {
          // 忽略取消错误
        }
      }
    }
  }

  const handleDelete = async (reportId, title) => {
    try {
      await api.delete(`/report/${reportId}`)
      message.success(`已删除报告：${title}`)
      // 删除成功后，重新获取报告列表
      await fetchReports()
    } catch (error) {
      console.error('删除报告失败:', error)
      message.error(error.response?.data?.detail || '删除报告失败，请稍后重试')
    }
  }

  const handleDownloadMd = async (reportId, title) => {
    try {
      const res = await api.get(`/report/${reportId}/download-md`, { responseType: 'blob' })
      const blob = new Blob([res.data], { type: 'text/markdown;charset=utf-8' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${(title || `report-${reportId}`).replace(/[\\/:*?"<>|]/g, '-')}.md`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('下载MD失败:', error)
      message.error(error.response?.data?.detail || '下载MD失败，请稍后重试')
    }
  }

  if (loading) {
    return <Spin size="large" style={{ display: 'block', textAlign: 'center', marginTop: '50px' }} />
  }

  return (
    <div>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>分析报告</h1>
        <Button
          type="primary"
          icon={<BarChartOutlined />}
          onClick={handleAnalyze}
          loading={analyzing}
          size="large"
        >
          分析今日新闻
        </Button>
      </div>

      {/* 进度条模态框 */}
      <Modal
        title="正在分析新闻"
        open={progressVisible}
        closable={false}
        maskClosable={false}
        footer={null}
        width={500}
      >
        <div style={{ padding: '20px 0' }}>
          <Progress 
            percent={progress} 
            status={progress === 100 ? 'success' : 'active'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
          <div style={{ marginTop: '16px', textAlign: 'center', color: '#666' }}>
            {progressMessage}
          </div>
        </div>
      </Modal>

      {reports.length > 0 ? (
        <div>
          <div style={{ marginBottom: '16px', color: '#666', fontSize: '14px' }}>
            共 {reports.length} 份报告（按时间倒序）
          </div>
          <List
            dataSource={reports}
            renderItem={(item) => (
              <List.Item>
                <Card
                  title={
                    <span>
                      <BarChartOutlined style={{ marginRight: '8px' }} />
                      {item.title || `分析报告 - ${new Date(item.report_date).toLocaleDateString('zh-CN')}`}
                    </span>
                  }
                  extra={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Tag color="blue">{item.analysis_type || '日报分析'}</Tag>
                      <Tooltip title="下载MD">
                        <Button
                          type="text"
                          icon={<DownloadOutlined />}
                          size="small"
                          style={{ padding: '0 4px' }}
                          onClick={() => handleDownloadMd(item.id, item.title)}
                        />
                      </Tooltip>
                      <Popconfirm
                        title="确定要删除这份报告吗？"
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
                    </div>
                  }
                  style={{ width: '100%' }}
                  hoverable
                >
                  <Collapse 
                    ghost
                    items={[
                      {
                        key: 'summary',
                        label: '查看摘要',
                        children: (
                          <div className="markdown-content">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {item.summary || item.content || '暂无摘要'}
                            </ReactMarkdown>
                          </div>
                        )
                      },
                      ...(item.content && item.content !== item.summary ? [{
                        key: 'content',
                        label: '查看完整内容',
                        children: (
                          <div className="markdown-content">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {item.content}
                            </ReactMarkdown>
                          </div>
                        )
                      }] : [])
                    ]}
                  />
                  
                  {item.statistics && (
                    <div style={{ marginTop: '16px', marginBottom: '12px' }}>
                      <Descriptions title="统计数据" size="small" column={2} bordered>
                        <Descriptions.Item label="新闻数量">
                          {item.statistics.total_news || 0}
                        </Descriptions.Item>
                        {item.statistics.teams_count !== undefined && (
                          <Descriptions.Item label="涉及球队">
                            {item.statistics.teams_count || 0}
                          </Descriptions.Item>
                        )}
                        {item.statistics.players_count !== undefined && (
                          <Descriptions.Item label="涉及球员">
                            {item.statistics.players_count || 0}
                          </Descriptions.Item>
                        )}
                        {item.statistics.categories && Object.keys(item.statistics.categories).length > 0 && (
                          <Descriptions.Item label="类别分布" span={2}>
                            {Object.entries(item.statistics.categories).map(([key, value]) => (
                              <Tag key={key} style={{ marginRight: '8px', marginTop: '4px' }}>
                                {key}: {value}
                              </Tag>
                            ))}
                          </Descriptions.Item>
                        )}
                        {item.statistics.teams && item.statistics.teams.length > 0 && (
                          <Descriptions.Item label="涉及球队列表" span={2}>
                            {item.statistics.teams.map((team, idx) => (
                              <Tag key={idx} style={{ marginRight: '8px', marginTop: '4px' }}>
                                {team}
                              </Tag>
                            ))}
                          </Descriptions.Item>
                        )}
                        {item.statistics.players && item.statistics.players.length > 0 && (
                          <Descriptions.Item label="涉及球员列表" span={2}>
                            {item.statistics.players.map((player, idx) => (
                              <Tag key={idx} style={{ marginRight: '8px', marginTop: '4px' }}>
                                {player}
                              </Tag>
                            ))}
                          </Descriptions.Item>
                        )}
                      </Descriptions>
                    </div>
                  )}
                  
                  {item.sentiment_analysis && item.sentiment_analysis.sentiment && (
                    <div style={{ marginTop: '12px' }}>
                      <Descriptions title="情感分析" size="small" column={3} bordered>
                        <Descriptions.Item label="整体情感">
                          <Tag color={
                            item.sentiment_analysis.sentiment === '正面' ? 'green' :
                            item.sentiment_analysis.sentiment === '负面' ? 'red' : 'default'
                          }>
                            {item.sentiment_analysis.sentiment}
                          </Tag>
                        </Descriptions.Item>
                        {item.sentiment_analysis.positive_score !== undefined && (
                          <Descriptions.Item label="正面得分">
                            {item.sentiment_analysis.positive_score}
                          </Descriptions.Item>
                        )}
                        {item.sentiment_analysis.negative_score !== undefined && (
                          <Descriptions.Item label="负面得分">
                            {item.sentiment_analysis.negative_score}
                          </Descriptions.Item>
                        )}
                      </Descriptions>
                    </div>
                  )}
                  
                  <div style={{ marginTop: '16px', fontSize: '12px', color: '#999', borderTop: '1px solid #f0f0f0', paddingTop: '12px' }}>
                    <div>生成时间: {new Date(item.created_at).toLocaleString('zh-CN')}</div>
                    {item.news_ids && item.news_ids.length > 0 && (
                      <div style={{ marginTop: '4px' }}>
                        分析新闻数: {item.news_ids.length} 条
                      </div>
                    )}
                  </div>
                </Card>
              </List.Item>
            )}
          />
        </div>
      ) : (
        <Empty description="暂无分析报告，点击上方按钮开始分析" />
      )}
    </div>
  )
}

export default AnalysisReport
