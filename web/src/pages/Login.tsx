import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Lock, Mail, ArrowRight, Eye, EyeOff, Shield, Zap, Sparkles } from 'lucide-react';

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
    <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50 overflow-hidden">
      {/* Background grid pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(14,165,233,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(14,165,233,0.03)_1px,transparent_1px)] bg-[size:60px_60px]"></div>

      {/* Animated decorative blobs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-sky-400/10 rounded-full blur-3xl animate-blob"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-400/10 rounded-full blur-3xl animate-blob animation-delay-2000"></div>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-cyan-400/8 rounded-full blur-3xl animate-blob animation-delay-4000"></div>

      {/* Left side - Feature showcase */}
      <div className="hidden lg:flex lg:w-1/2 relative items-center justify-center p-16">
        <div className="relative z-10 max-w-lg animate-fade-in-up">
          {/* Logo */}
          <div className="mb-10">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-sky-500 to-indigo-500 rounded-2xl shadow-xl shadow-sky-500/30 animate-float mb-6">
              <Zap className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-slate-800 via-sky-700 to-indigo-700 bg-clip-text text-transparent leading-tight mb-4">
              AI 知识库助手
            </h1>
            <p className="text-lg text-slate-600 leading-relaxed">
              构建现代化知识库服务，提供高效的知识检索与智能问答能力
            </p>
          </div>

          {/* Features */}
          <div className="space-y-5">
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-11 h-11 bg-gradient-to-br from-sky-100 to-sky-50 rounded-xl group-hover:from-sky-200 group-hover:to-sky-100 transition-all shadow-sm">
                <Shield className="w-5 h-5 text-sky-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 mb-1">智能知识构建</h3>
                <p className="text-sm text-slate-500">支持多源文档接入，自动解析与结构化，快速构建高质量知识库</p>
              </div>
            </div>
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-11 h-11 bg-gradient-to-br from-indigo-100 to-indigo-50 rounded-xl group-hover:from-indigo-200 group-hover:to-indigo-100 transition-all shadow-sm">
                <Sparkles className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 mb-1">精准知识检索</h3>
                <p className="text-sm text-slate-500">基于语义理解的智能检索，快速定位关键信息与答案</p>
              </div>
            </div>
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-11 h-11 bg-gradient-to-br from-cyan-100 to-cyan-50 rounded-xl group-hover:from-cyan-200 group-hover:to-cyan-100 transition-all shadow-sm">
                <Lock className="w-5 h-5 text-cyan-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 mb-1">智能问答体验</h3>
                <p className="text-sm text-slate-500">结合大模型能力，实现上下文理解的知识库问答与推理</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
        <div className="w-full max-w-md relative z-10 animate-fade-in-up">
          {/* Mobile logo */}
          <div className="lg:hidden mb-8 text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-sky-500 to-indigo-500 rounded-xl shadow-lg shadow-sky-500/30 mb-4">
              <Zap className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
              AI 知识库助手
            </h2>
          </div>

          {/* Login card */}
          <div className="bg-white/70 backdrop-blur-xl rounded-3xl shadow-xl shadow-slate-200/50 border border-white/60 p-8 md:p-10">
            <div className="mb-8">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent mb-2">
                欢迎回来
              </h2>
              <p className="text-slate-500">登录到您的账户</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-sky-500" />
                  邮箱地址
                </Label>
                <div className="relative group">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-sky-500 transition-colors" />
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="pl-11 h-11 border-slate-200 focus:border-sky-400 focus:ring-2 focus:ring-sky-500/20 rounded-xl transition-all duration-200 bg-white/80"
                    placeholder="your@email.com"
                  />
                </div>
              </div>

              {/* Password field */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                    <Lock className="w-4 h-4 text-sky-500" />
                    密码
                  </Label>
                  <button
                    type="button"
                    className="text-sm text-sky-600 hover:text-sky-700 font-medium transition-colors"
                  >
                    忘记密码?
                  </button>
                </div>
                <div className="relative group">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-sky-500 transition-colors" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="pl-11 pr-11 h-11 border-slate-200 focus:border-sky-400 focus:ring-2 focus:ring-sky-500/20 rounded-xl transition-all duration-200 bg-white/80"
                    placeholder="输入您的密码"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-lg hover:bg-slate-100"
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
              <div className="flex items-center">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-300 text-sky-500 focus:ring-2 focus:ring-sky-500/20 transition-all cursor-pointer"
                  />
                  <span className="text-sm text-slate-600 group-hover:text-slate-800 transition-colors">
                    记住我
                  </span>
                </label>
              </div>

              {/* Error message */}
              {error && (
                <div className="bg-red-50/90 backdrop-blur-sm border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm flex items-center gap-2 animate-shake">
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
                className="w-full h-11 bg-gradient-to-r from-sky-500 via-indigo-500 to-cyan-500 hover:from-sky-600 hover:via-indigo-600 hover:to-cyan-600 text-white font-semibold shadow-lg shadow-sky-500/30 hover:shadow-xl hover:shadow-sky-500/40 transition-all duration-300 rounded-xl animate-gradient"
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
              <div className="text-center pt-5 border-t border-slate-100">
                <p className="text-sm text-slate-500">
                  还没有账号?{' '}
                  <Link
                    to="/register"
                    className="text-sky-600 hover:text-sky-700 font-semibold hover:underline transition-all"
                  >
                    免费注册
                  </Link>
                </p>
              </div>
            </form>
          </div>

          {/* Tech decoration */}
          <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-400">
            <div className="w-2 h-2 rounded-full bg-sky-400 animate-pulse"></div>
            <span>安全加密 · 智能检索 · 实时响应</span>
            <div className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse animation-delay-2000"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
