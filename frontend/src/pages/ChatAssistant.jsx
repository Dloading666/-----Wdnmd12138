import React, { useState, useRef, useEffect } from 'react'
import { Input, Button, Card, Avatar, Spin, message } from 'antd'
import { SendOutlined, UserOutlined, RobotOutlined } from '@ant-design/icons'
import api from '../utils/axios'
import './ChatAssistant.css'

const { TextArea } = Input

const ChatAssistant = () => {
  const [messages, setMessages] = useState([
    {
      type: 'assistant',
      content: '你好！我是体育智能助手，可以帮您解答体育相关问题，生成日报，分析报告等。有什么可以帮您的吗？'
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!inputValue.trim()) {
      return
    }

    const userMessage = {
      type: 'user',
      content: inputValue
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    try {
      const response = await api.post('/chat/message', {
        message: inputValue
      })

      const assistantMessage = {
        type: 'assistant',
        content: response.data.response
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('发送消息失败:', error)
      message.error('发送消息失败，请稍后重试')
      const errorMessage = {
        type: 'assistant',
        content: '抱歉，处理您的请求时出现了错误，请稍后重试。'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-container">
      <div style={{ marginBottom: '16px' }}>
        <h1>智能助手</h1>
        <p style={{ color: '#666' }}>与AI助手对话，获取体育分析和建议</p>
      </div>

      <Card className="chat-card">
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`chat-message ${msg.type === 'user' ? 'user-message' : 'assistant-message'}`}
            >
              <Avatar
                icon={msg.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
                style={{
                  backgroundColor: msg.type === 'user' ? '#1890ff' : '#52c41a',
                  marginRight: '12px',
                  marginLeft: msg.type === 'user' ? '12px' : '0'
                }}
              />
              <div className="message-content">
                <div className="message-bubble">
                  {msg.content}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-message assistant-message">
              <Avatar
                icon={<RobotOutlined />}
                style={{ backgroundColor: '#52c41a', marginRight: '12px' }}
              />
              <div className="message-content">
                <Spin size="small" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入您的问题..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{ marginRight: '8px' }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={loading}
            disabled={!inputValue.trim()}
          >
            发送
          </Button>
        </div>
      </Card>
    </div>
  )
}

export default ChatAssistant
