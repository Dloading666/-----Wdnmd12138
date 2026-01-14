// Token管理工具

const TOKEN_KEY = 'sports_analysis_token';
const USER_KEY = 'sports_analysis_user';

// 保存token
export const setToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
};

// 获取token
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

// 删除token
export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

// 保存用户信息
export const setUser = (user) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

// 获取用户信息
export const getUser = () => {
  const userStr = localStorage.getItem(USER_KEY);
  return userStr ? JSON.parse(userStr) : null;
};

// 检查是否已登录
export const isAuthenticated = () => {
  return !!getToken();
};
