import React, { useState, useEffect } from 'react';
import { Form, Input, Button, message, Tabs, Checkbox } from 'antd';
import { useNavigate } from 'react-router-dom';
import api from '../utils/axios';
import { setToken, setUser, isAuthenticated } from '../utils/auth';
import './Login.css';

const Login = () => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');
  const navigate = useNavigate();

  // 如果已经登录，重定向到dashboard
  useEffect(() => {
    if (isAuthenticated()) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  const onLogin = async (values) => {
    setLoading(true);
    try {
      const response = await api.post('/auth/login', {
        username: values.username,
        password: values.password,
      });

      const { access_token } = response.data;
      setToken(access_token);

      // 获取用户信息
      const userResponse = await api.get('/auth/me');
      setUser(userResponse.data);

      message.success('登录成功！');
      navigate('/dashboard');
    } catch (error) {
      console.error('登录失败:', error);
      message.error(error.response?.data?.detail || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  const onRegister = async (values) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次输入的密码不一致');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/register', {
        username: values.username,
        email: values.email,
        password: values.password,
      });

      message.success('注册成功！请登录');
      setActiveTab('login');
    } catch (error) {
      console.error('注册失败:', error);
      message.error(error.response?.data?.detail || '注册失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-container">
        <div className="login-form-panel">
          <div className="form-content">
            <h1 className="form-title">
              {activeTab === 'login' ? '登录' : '注册'}
            </h1>

            {activeTab === 'login' ? (
              <Form
                name="login"
                onFinish={onLogin}
                autoComplete="off"
                className="auth-form"
              >
                <Form.Item
                  name="username"
                  rules={[{ required: true, message: '请输入用户名' }]}
                  className="form-item-custom"
                >
                  <Input
                    className="custom-input-white"
                    placeholder="用户名"
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[{ required: true, message: '请输入密码' }]}
                  className="form-item-custom"
                >
                  <Input.Password
                    className="custom-input-white"
                    placeholder="密码"
                  />
                </Form.Item>

                <Form.Item className="form-options">
                  <Form.Item name="remember" valuePropName="checked" noStyle>
                    <Checkbox className="remember-checkbox">记住密码</Checkbox>
                  </Form.Item>
                  <a href="#" className="forgot-password">忘记密码</a>
                </Form.Item>

                <Form.Item className="form-button-item">
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    className="submit-button"
                  >
                    立即登录
                  </Button>
                </Form.Item>

                <div className="register-link">
                  没有账号? <a href="#" onClick={(e) => { e.preventDefault(); setActiveTab('register'); }}>立即注册</a>
                </div>
              </Form>
            ) : (
              <Form
                name="register"
                onFinish={onRegister}
                autoComplete="off"
                className="auth-form"
              >
                <Form.Item
                  name="username"
                  rules={[
                    { required: true, message: '请输入用户名' },
                    { min: 3, message: '用户名至少3个字符' },
                  ]}
                  className="form-item-custom"
                >
                  <Input
                    className="custom-input-white"
                    placeholder="用户名"
                  />
                </Form.Item>

                <Form.Item
                  name="email"
                  rules={[
                    { required: true, message: '请输入邮箱' },
                    { type: 'email', message: '请输入有效的邮箱地址' },
                  ]}
                  className="form-item-custom"
                >
                  <Input
                    className="custom-input-white"
                    placeholder="邮箱"
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[
                    { required: true, message: '请输入密码' },
                    { min: 6, message: '密码至少6个字符' },
                  ]}
                  className="form-item-custom"
                >
                  <Input.Password
                    className="custom-input-white"
                    placeholder="密码"
                  />
                </Form.Item>

                <Form.Item
                  name="confirmPassword"
                  rules={[
                    { required: true, message: '请确认密码' },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('password') === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject(new Error('两次输入的密码不一致'));
                      },
                    }),
                  ]}
                  className="form-item-custom"
                >
                  <Input.Password
                    className="custom-input-white"
                    placeholder="确认密码"
                  />
                </Form.Item>

                <Form.Item className="form-button-item">
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    className="submit-button"
                  >
                    立即注册
                  </Button>
                </Form.Item>

                <div className="register-link">
                  已有账号? <a href="#" onClick={(e) => { e.preventDefault(); setActiveTab('login'); }}>立即登录</a>
                </div>
              </Form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
