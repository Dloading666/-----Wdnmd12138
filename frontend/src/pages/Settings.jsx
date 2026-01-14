import React, { useState, useEffect } from 'react'
import { Card, Form, Input, Button, message, Divider, Space } from 'antd'
import { SettingOutlined, LockOutlined, LogoutOutlined, UserOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import api from '../utils/axios'
import { removeToken, getUser } from '../utils/auth'

const Settings = () => {
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState(null)
  const [form] = Form.useForm()
  const navigate = useNavigate()

  useEffect(() => {
    fetchUserInfo()
  }, [])

  const fetchUserInfo = async () => {
    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  const handleChangePassword = async (values) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的新密码不一致')
      return
    }

    setLoading(true)
    try {
      await api.post('/auth/change-password', {
        old_password: values.oldPassword,
        new_password: values.newPassword
      })
      message.success('密码修改成功！')
      form.resetFields()
    } catch (error) {
      console.error('修改密码失败:', error)
      message.error(error.response?.data?.detail || '修改密码失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    removeToken()
    message.success('已退出登录')
    navigate('/login')
  }

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1>
          <SettingOutlined style={{ marginRight: '8px' }} />
          设置
        </h1>
      </div>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 用户信息卡片 */}
        <Card title={
          <span>
            <UserOutlined style={{ marginRight: '8px' }} />
            用户信息
          </span>
        }>
          {user && (
            <div>
              <p><strong>用户名：</strong>{user.username}</p>
              <p><strong>邮箱：</strong>{user.email || '未设置'}</p>
              <p><strong>注册时间：</strong>{user.created_at ? new Date(user.created_at).toLocaleString('zh-CN') : '未知'}</p>
            </div>
          )}
        </Card>

        {/* 修改密码卡片 */}
        <Card title={
          <span>
            <LockOutlined style={{ marginRight: '8px' }} />
            修改密码
          </span>
        }>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleChangePassword}
            style={{ maxWidth: '500px' }}
          >
            <Form.Item
              name="oldPassword"
              label="原密码"
              rules={[{ required: true, message: '请输入原密码' }]}
            >
              <Input.Password placeholder="请输入原密码" />
            </Form.Item>

            <Form.Item
              name="newPassword"
              label="新密码"
              rules={[
                { required: true, message: '请输入新密码' },
                { min: 6, message: '密码至少需要6个字符' }
              ]}
            >
              <Input.Password placeholder="请输入新密码（至少6个字符）" />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              label="确认新密码"
              dependencies={['newPassword']}
              rules={[
                { required: true, message: '请确认新密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('newPassword') === value) {
                      return Promise.resolve()
                    }
                    return Promise.reject(new Error('两次输入的新密码不一致'))
                  },
                }),
              ]}
            >
              <Input.Password placeholder="请再次输入新密码" />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                修改密码
              </Button>
            </Form.Item>
          </Form>
        </Card>

        {/* 退出登录卡片 */}
        <Card title={
          <span>
            <LogoutOutlined style={{ marginRight: '8px' }} />
            账户操作
          </span>
        }>
          <Button
            danger
            icon={<LogoutOutlined />}
            onClick={handleLogout}
            size="large"
          >
            退出登录
          </Button>
        </Card>
      </Space>
    </div>
  )
}

export default Settings
