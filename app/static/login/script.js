// 全局配置
const API_BASE_URL = '/v1';

// 消息提示管理
const MessageManager = {
    show(message, type = 'info', duration = 3000) {
        const messageEl = document.getElementById('message');
        messageEl.textContent = message;
        messageEl.className = `message ${type}`;

        setTimeout(() => {
            messageEl.classList.add('hidden');
        }, duration);
    },

    success(message) {
        this.show(message, 'success');
    },

    error(message) {
        this.show(message, 'error', 5000);
    },

    info(message) {
        this.show(message, 'info');
    }
};

// 标签切换管理
const TabManager = {
    switch(tabId) {
        // 隐藏所有标签内容
        document.querySelectorAll('.tab-content').forEach(el => {
            el.classList.remove('active');
        });

        // 移除所有标签按钮的激活状态
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });

        // 显示目标标签
        const targetTab = document.getElementById(tabId);
        if (targetTab) {
            targetTab.classList.add('active');
        }

        // 激活对应标签按钮（如果存在）
        const targetBtn = document.querySelector(`[data-tab="${tabId}"]`);
        if (targetBtn) {
            targetBtn.classList.add('active');
        }
    },

    showRegister() {
        this.switch('register-form');
    },

    showLogin() {
        this.switch('password-login');
    }
};

// API请求管理
const ApiClient = {
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const token = localStorage.getItem('access_token');

        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            },
            ...options
        };

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                // 检查是否有字段验证错误
                if (data.field_errors && typeof data.field_errors === 'object') {
                    // 构建字段错误消息
                    let errorMessages = [];
                    for (const [field, errors] of Object.entries(data.field_errors)) {
                        // 翻译字段名称为中文
                        const fieldMapping = {
                            'email': '邮箱',
                            'username': '用户名',
                            'password': '密码',
                            'password_confirm': '确认密码'
                        };
                        const fieldName = fieldMapping[field] || field;
                        
                        // 添加所有该字段的错误消息
                        for (const error of errors) {
                            errorMessages.push(`${fieldName}：${error.message}`);
                        }
                    }
                    
                    // 如果有字段错误，抛出包含这些错误的异常
                    if (errorMessages.length > 0) {
                        throw new Error(errorMessages.join('\n'));
                    }
                }
                
                // 否则抛出一般错误消息
                throw new Error(data.message || '请求失败');
            }

            return data;
        } catch (error) {
            console.error('API请求错误:', error);
            throw error;
        }
    },

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async get(endpoint) {
        return this.request(endpoint, {
            method: 'GET'
        });
    }
};

// 认证管理
const AuthManager = {
    setToken(token) {
        localStorage.setItem('access_token', token);
    },

    getToken() {
        return localStorage.getItem('access_token');
    },

    clearToken() {
        localStorage.removeItem('access_token');
    },

    async getProfile() {
        try {
            const user = await ApiClient.get('/users/profile');
            return user;
        } catch (error) {
            this.clearToken();
            throw error;
        }
    },

    async handleLoginSuccess(tokenData) {
        this.setToken(tokenData.access_token);
        MessageManager.success('登录成功！正在获取用户信息...');

        try {
            const user = await this.getProfile();
            MessageManager.info(`欢迎回来，${user.username}！`);
            // 这里可以跳转到用户仪表板或首页
            // window.location.href = '/dashboard';
        } catch (error) {
            MessageManager.error('获取用户信息失败: ' + error.message);
        }
    },

    logout() {
        this.clearToken();
        MessageManager.info('已退出登录');
        window.location.href = '/login';
    }
};

// 表单管理
const FormManager = {
    setLoading(button, loading = true) {
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    },

    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    validatePassword(password) {
        return password && password.length >= 8;
    }
};

// 密码登录
async function handlePasswordLogin(event) {
    event.preventDefault();

    const form = event.target;
    const email = form.email.value.trim();
    const password = form.password.value;

    // 验证输入
    if (!email || !password) {
        MessageManager.error('请填写邮箱和密码');
        return;
    }

    if (!FormManager.validateEmail(email)) {
        MessageManager.error('请输入有效的邮箱地址');
        return;
    }

    if (!FormManager.validatePassword(password)) {
        MessageManager.error('密码至少需要8个字符');
        return;
    }

    const submitButton = form.querySelector('button[type="submit"]');
    FormManager.setLoading(submitButton, true);

    try {
        const response = await ApiClient.post('/users/login', {
            email,
            password
        });

        await AuthManager.handleLoginSuccess(response);
    } catch (error) {
        MessageManager.error('登录失败: ' + error.message);
    } finally {
        FormManager.setLoading(submitButton, false);
    }
}

// 注册
async function handleRegister(event) {
    event.preventDefault();

    const form = event.target;
    const email = form.email.value.trim();
    const username = form.username.value.trim();
    const password = form.password.value;
    const passwordConfirm = form.password_confirm.value;

    // 验证输入
    if (!email || !username || !password || !passwordConfirm) {
        MessageManager.error('请填写所有字段');
        return;
    }

    if (!FormManager.validateEmail(email)) {
        MessageManager.error('请输入有效的邮箱地址');
        return;
    }

    if (username.length < 3 || username.length > 30) {
        MessageManager.error('用户名长度应在3-30个字符之间');
        return;
    }

    if (!FormManager.validatePassword(password)) {
        MessageManager.error('密码至少需要8个字符');
        return;
    }

    if (password !== passwordConfirm) {
        MessageManager.error('两次输入的密码不一致');
        return;
    }

    const submitButton = form.querySelector('button[type="submit"]');
    FormManager.setLoading(submitButton, true);

    try {
        await ApiClient.post('/users/register', {
            email,
            username,
            password
        });

        MessageManager.success('注册成功！请登录');

        // 清空表单
        form.reset();

        // 切换到登录标签
        TabManager.showLogin();
    } catch (error) {
        MessageManager.error('注册失败: ' + error.message);
    } finally {
        FormManager.setLoading(submitButton, false);
    }
}

// OAuth登录
async function oauthLogin(provider) {
    try {
        MessageManager.info(`正在跳转到${provider}登录...`);

        // 打开OAuth授权页面
        const authUrl = `${API_BASE_URL}/users/oauth/${provider}`;
        window.location.href = authUrl;
    } catch (error) {
        MessageManager.error('OAuth登录失败: ' + error.message);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 绑定表单提交事件
    const passwordLoginForm = document.getElementById('password-login-form');
    if (passwordLoginForm) {
        passwordLoginForm.addEventListener('submit', handlePasswordLogin);
    }

    const registerForm = document.getElementById('register-form-element');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    // 绑定标签切换事件
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            TabManager.switch(tabId);
        });
    });

    // 绑定注册/登录切换链接
    const showRegisterLink = document.getElementById('show-register');
    if (showRegisterLink) {
        showRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            TabManager.showRegister();
        });
    }

    const showLoginLink = document.getElementById('show-login');
    if (showLoginLink) {
        showLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            TabManager.showLogin();
        });
    }

    // 检查是否已登录
    const token = AuthManager.getToken();
    if (token) {
        // 验证token是否有效
        AuthManager.getProfile()
            .then(user => {
                MessageManager.info(`您已登录为 ${user.username}`);
                // 可以选择跳转到仪表板
                // window.location.href = '/dashboard';
            })
            .catch(() => {
                // Token无效，清除
                AuthManager.clearToken();
            });
    }

    console.log('登录页面已初始化');
});

// 添加键盘快捷键支持
document.addEventListener('keydown', (e) => {
    // Enter键提交表单
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
        const form = e.target.closest('form');
        if (form) {
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        }
    }

    // Esc键隐藏消息
    if (e.key === 'Escape') {
        const messageEl = document.getElementById('message');
        if (messageEl && !messageEl.classList.contains('hidden')) {
            messageEl.classList.add('hidden');
        }
    }
});

// 导出到全局作用域（如果需要）
window.LoginPage = {
    oauthLogin,
    AuthManager,
    MessageManager
};
