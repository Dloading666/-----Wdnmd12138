import React from 'react'
import { Layout, Menu, Dropdown, Avatar, Space } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  FileTextOutlined,
  BarChartOutlined,
  MessageOutlined,
  LogoutOutlined,
  UserOutlined,
  SettingOutlined
} from '@ant-design/icons'
import { removeToken, getUser } from '../utils/auth'

const { Sider } = Layout

const Sidebar = ({ collapsed, setCollapsed }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const user = getUser()

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/news',
      icon: <FileTextOutlined />,
      label: '体育日报',
    },
    {
      key: '/report',
      icon: <BarChartOutlined />,
      label: '分析报告',
    },
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: '智能助手',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ]

  const handleMenuClick = ({ key }) => {
    navigate(key)
  }

  const handleLogout = () => {
    removeToken()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'user',
      icon: <UserOutlined />,
      label: user?.username || '用户',
      disabled: true,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={setCollapsed}
      width={250}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        background: '#001529',
        zIndex: 1000
      }}
    >
      <div style={{ 
        height: '64px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: '#fff',
        fontSize: collapsed ? '16px' : '18px',
        fontWeight: 'bold',
        borderBottom: '1px solid #1f1f1f',
        padding: collapsed ? '0 16px' : '0 24px'
      }}>
        {collapsed ? '体育' : '体育智能分析'}
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ borderRight: 0 }}
      />
      
      <div style={{ 
        position: 'absolute', 
        bottom: 0, 
        left: 0, 
        right: 0, 
        padding: '16px',
        borderTop: '1px solid #1f1f1f'
      }}>
        <Dropdown menu={{ items: userMenuItems }} placement="topLeft">
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            color: '#fff',
            cursor: 'pointer',
            padding: '8px',
            borderRadius: '4px',
            transition: 'background 0.3s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
          >
            <Avatar size="small" icon={<UserOutlined />} style={{ marginRight: collapsed ? 0 : '8px' }} />
            {!collapsed && (
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user?.username || '用户'}
              </span>
            )}
          </div>
        </Dropdown>
      </div>
    </Sider>
  )
}

export default Sidebar
