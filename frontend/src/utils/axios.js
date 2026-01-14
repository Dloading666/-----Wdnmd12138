import axios from 'axios';
import { getToken, removeToken } from './auth';

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 增加到120秒，因为LLM分析需要较长时间
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加token
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // token过期或无效，清除token并跳转到登录页
      removeToken();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
