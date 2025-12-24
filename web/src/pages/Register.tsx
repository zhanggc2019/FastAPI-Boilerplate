import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Lock, Mail, User, ArrowRight, Sparkles } from 'lucide-react';

export default function Register() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setFieldErrors({});

    try {
      await api.post('/users/register', {
        email,
        username,
        password,
      });
      navigate('/login');
    } catch (err: any) {
      console.error(err);

      // 处理验证错误
      if (err.response?.status === 422 && err.response?.data?.detail?.field_errors) {
        const errors: Record<string, string> = {};
        const fieldErrorsData = err.response.data.detail.field_errors;

        for (const [field, fieldErrorList] of Object.entries(fieldErrorsData)) {
          if (Array.isArray(fieldErrorList) && fieldErrorList.length > 0) {
            errors[field] = (fieldErrorList[0] as any).message || '验证失败';
          }
        }

        setFieldErrors(errors);
        setError('请检查输入的信息');
      } else if (err.response?.data?.message) {
        // 处理其他业务错误
        setError(err.response.data.message);
      } else {
        setError('注册失败，请稍后重试');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
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
              <Sparkles className="w-8 h-8" />
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
                <Sparkles className="w-5 h-5 text-violet-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white mb-1">快速开始</h3>
                <p className="text-sm text-gray-400">几步完成注册，立即体验完整功能</p>
              </div>
            </div>
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-10 h-10 bg-fuchsia-500/20 rounded-lg group-hover:bg-fuchsia-500/30 transition-colors">
                <Lock className="w-5 h-5 text-fuchsia-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white mb-1">安全可靠</h3>
                <p className="text-sm text-gray-400">完善的认证机制与权限控制</p>
              </div>
            </div>
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-10 h-10 bg-pink-500/20 rounded-lg group-hover:bg-pink-500/30 transition-colors">
                <ArrowRight className="w-5 h-5 text-pink-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white mb-1">即刻探索</h3>
                <p className="text-sm text-gray-400">注册后直达知识库助手与控制台</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - White form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden mb-8 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl mb-4">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">FastAPI</h2>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">创建用户</h2>
            <p className="text-gray-600">Get started with your free account today.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email field */}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-gray-700">
                Email
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className={`pl-10 h-11 border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${
                    fieldErrors.email ? 'border-red-500' : ''
                  }`}
                  placeholder="Enter your email"
                />
              </div>
              {fieldErrors.email && (
                <p className="text-sm text-red-600">{fieldErrors.email}</p>
              )}
            </div>

            {/* Username field */}
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium text-gray-700">
                Username
              </Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className={`pl-10 h-11 border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${
                    fieldErrors.username ? 'border-red-500' : ''
                  }`}
                  placeholder="Choose a username"
                />
              </div>
              {fieldErrors.username && (
                <p className="text-sm text-red-600">{fieldErrors.username}</p>
              )}
              <p className="text-xs text-gray-500">只能包含字母、数字、下划线和连字符</p>
            </div>

            {/* Password field */}
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium text-gray-700">
                Password
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className={`pl-10 h-11 border-gray-300 focus:border-blue-500 focus:ring-blue-500 ${
                    fieldErrors.password ? 'border-red-500' : ''
                  }`}
                  placeholder="Create a password"
                />
              </div>
              {fieldErrors.password && (
                <p className="text-sm text-red-600">{fieldErrors.password}</p>
              )}
              <p className="text-xs text-gray-500">至少8个字符，包含大写字母、数字和特殊字符</p>
            </div>

            {/* Error message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            {/* Submit button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-11 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-medium shadow-lg shadow-blue-500/30 transition-all duration-200"
            >
              {isLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Creating account...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2">
                  <span>创建用户</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              )}
            </Button>

            {/* Login link */}
            <div className="text-center pt-4">
              <p className="text-sm text-gray-600">
                已有账号?{' '}
                <Link
                  to="/login"
                  className="text-blue-600 hover:text-blue-700 font-semibold"
                >
                  登录
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
