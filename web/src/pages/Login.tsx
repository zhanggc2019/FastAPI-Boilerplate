import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Lock, Mail, ArrowRight, Sparkles, Eye, EyeOff, Shield, Zap } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await api.post('/users/login', {
        email,
        password,
      });

      localStorage.setItem('token', response.data.access_token);
      api.defaults.headers.common.Authorization = `Bearer ${response.data.access_token}`;
      console.info('[auth] login token stored', response.data.access_token ? 'yes' : 'no');
      navigate('/chatbot');
    } catch (err: any) {
      console.error(err);

      // 处理不同类型的错误
      if (err.response?.status === 401) {
        setError('邮箱或密码错误，请重试');
      } else if (err.response?.status === 422) {
        setError('请输入有效的邮箱和密码');
      } else if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else {
        setError('登录失败，请稍后重试');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-white to-violet-50">
      {/* Left side - Dark with gradient and animations */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
        {/* Animated gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-violet-600/20 via-fuchsia-600/20 to-pink-600/20 animate-pulse"></div>

        {/* Animated decorative elements */}
        <div className="absolute top-20 left-20 w-72 h-72 bg-violet-500/20 rounded-full blur-3xl animate-blob"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-fuchsia-500/20 rounded-full blur-3xl animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-pink-500/10 rounded-full blur-3xl animate-blob animation-delay-4000"></div>

        {/* Grid pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]"></div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-16 text-white">
          <div className="mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-2xl mb-6 shadow-2xl shadow-violet-500/50 animate-float">
              <Zap className="w-8 h-8" />
            </div>
            <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-white via-violet-200 to-fuchsia-200 bg-clip-text text-transparent leading-tight">
              欢迎使用 AI 知识库助手
              
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed whitespace-nowrap">
              构建现代化知识库服务，提供高效的知识检索与智能问答能力
            </p>
          </div>

          <div className="space-y-6">
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-10 h-10 bg-violet-500/20 rounded-lg group-hover:bg-violet-500/30 transition-colors">
                <Shield className="w-5 h-5 text-violet-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white mb-1">📚智能知识构建</h3>
                <p className="text-sm text-gray-400">支持多源文档接入，自动解析与结构化，快速构建高质量知识库</p>
              </div>
            </div>
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-10 h-10 bg-fuchsia-500/20 rounded-lg group-hover:bg-fuchsia-500/30 transition-colors">
                <Lock className="w-5 h-5 text-fuchsia-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white mb-1">🔍 精准知识检索</h3>
                <p className="text-sm text-gray-400">基于语义理解的智能检索，快速定位关键信息与答案</p>
              </div>
            </div>
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-10 h-10 bg-pink-500/20 rounded-lg group-hover:bg-pink-500/30 transition-colors">
                <Sparkles className="w-5 h-5 text-pink-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white mb-1">🤖 智能问答体验</h3>
                <p className="text-sm text-gray-400">结合大模型能力，实现上下文理解的知识库问答与推理</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Form with glass effect */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-violet-50/50 via-transparent to-fuchsia-50/50"></div>

        <div className="w-full max-w-md relative z-10">
          {/* Mobile logo */}
          <div className="lg:hidden mb-8 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-xl mb-3 shadow-lg shadow-violet-500/30 animate-float">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-xl font-bold bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
              FastAPI Boilerplate
            </h2>
          </div>

          {/* Login card with glass effect */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-violet-500/10 border border-white/20 p-8 md:p-10">
            <div className="mb-8">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-2">
                欢迎回来
              </h2>
              <p className="text-gray-600">登录到您的账户</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-violet-500" />
                  邮箱地址
                </Label>
                <div className="relative group">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-violet-500 transition-colors" />
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="pl-10 h-12 border-2 border-gray-200 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 rounded-xl transition-all duration-200 hover:border-gray-300"
                    placeholder="your@email.com"
                  />
                </div>
              </div>

              {/* Password field */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <Lock className="w-4 h-4 text-violet-500" />
                    密码
                  </Label>
                  <button
                    type="button"
                    className="text-sm text-violet-600 hover:text-violet-700 font-medium transition-colors hover:underline"
                  >
                    忘记密码?
                  </button>
                </div>
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-violet-500 transition-colors" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="pl-10 pr-12 h-12 border-2 border-gray-200 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 rounded-xl transition-all duration-200 hover:border-gray-300"
                    placeholder="输入您的密码"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              {/* Remember me checkbox */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-2 border-gray-300 text-violet-600 focus:ring-2 focus:ring-violet-500/20 transition-all cursor-pointer"
                  />
                  <span className="text-sm text-gray-600 group-hover:text-gray-900 transition-colors">
                    记住我
                  </span>
                </label>
              </div>

              {/* Error message */}
              {error && (
                <div className="bg-red-50/80 backdrop-blur-sm border-2 border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm flex items-center gap-2 animate-shake">
                  <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-white text-xs font-bold">!</span>
                  </div>
                  {error}
                </div>
              )}

              {/* Submit button */}
              <Button
                type="submit"
                disabled={isLoading}
                className="w-full h-12 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700 text-white font-semibold shadow-xl shadow-violet-500/30 hover:shadow-2xl hover:shadow-violet-500/40 transition-all duration-300 rounded-xl group"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>登录中...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <span>登录</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </div>
                )}
              </Button>

              {/* Register link */}
              <div className="text-center pt-6 border-t border-gray-100">
                <p className="text-sm text-gray-600">
                  还没有账号?{' '}
                  <Link
                    to="/register"
                    className="text-violet-600 hover:text-violet-700 font-semibold hover:underline transition-all"
                  >
                    免费注册
                  </Link>
                </p>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
