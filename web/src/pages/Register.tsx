import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Lock, Mail, User, ArrowRight, Sparkles, Shield, Zap } from 'lucide-react';

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
    <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50 overflow-hidden">
      {/* Background grid pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(14,165,233,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(14,165,233,0.03)_1px,transparent_1px)] bg-[size:60px_60px]"></div>

      {/* Animated decorative blobs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-400/10 rounded-full blur-3xl animate-blob"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-400/10 rounded-full blur-3xl animate-blob animation-delay-2000"></div>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-sky-400/8 rounded-full blur-3xl animate-blob animation-delay-4000"></div>

      {/* Left side - Feature showcase */}
      <div className="hidden lg:flex lg:w-1/2 relative items-center justify-center p-16">
        <div className="relative z-10 max-w-lg animate-fade-in-up">
          {/* Logo */}
          <div className="mb-10">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-2xl shadow-xl shadow-indigo-500/30 animate-float mb-6">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-slate-800 via-indigo-700 to-cyan-700 bg-clip-text text-transparent leading-tight mb-4">
              加入我们
            </h1>
            <p className="text-lg text-slate-600 leading-relaxed">
              创建您的账户，开启智能知识库之旅，体验高效的知识检索与问答能力
            </p>
          </div>

          {/* Features */}
          <div className="space-y-5">
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-11 h-11 bg-gradient-to-br from-indigo-100 to-indigo-50 rounded-xl group-hover:from-indigo-200 group-hover:to-indigo-100 transition-all shadow-sm">
                <Zap className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 mb-1">快速开始</h3>
                <p className="text-sm text-slate-500">几步完成注册，立即体验完整功能</p>
              </div>
            </div>
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-11 h-11 bg-gradient-to-br from-sky-100 to-sky-50 rounded-xl group-hover:from-sky-200 group-hover:to-sky-100 transition-all shadow-sm">
                <Shield className="w-5 h-5 text-sky-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 mb-1">安全可靠</h3>
                <p className="text-sm text-slate-500">完善的认证机制与权限控制</p>
              </div>
            </div>
            <div className="flex items-start gap-4 group">
              <div className="flex items-center justify-center w-11 h-11 bg-gradient-to-br from-cyan-100 to-cyan-50 rounded-xl group-hover:from-cyan-200 group-hover:to-cyan-100 transition-all shadow-sm">
                <ArrowRight className="w-5 h-5 text-cyan-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 mb-1">即刻探索</h3>
                <p className="text-sm text-slate-500">注册后直达知识库助手与控制台</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Register form */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
        <div className="w-full max-w-md relative z-10 animate-fade-in-up">
          {/* Mobile logo */}
          <div className="lg:hidden mb-8 text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-xl shadow-lg shadow-indigo-500/30 mb-4">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
              AI 知识库助手
            </h2>
          </div>

          {/* Register card */}
          <div className="bg-white/70 backdrop-blur-xl rounded-3xl shadow-xl shadow-slate-200/50 border border-white/60 p-8 md:p-10">
            <div className="mb-8">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent mb-2">
                创建账户
              </h2>
              <p className="text-slate-500">开始您的智能知识库之旅</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-indigo-500" />
                  邮箱地址
                </Label>
                <div className="relative group">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className={`pl-11 h-11 border-slate-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20 rounded-xl transition-all duration-200 bg-white/80 ${
                      fieldErrors.email ? 'border-red-300' : ''
                    }`}
                    placeholder="your@email.com"
                  />
                </div>
                {fieldErrors.email && (
                  <p className="text-sm text-red-600">{fieldErrors.email}</p>
                )}
              </div>

              {/* Username field */}
              <div className="space-y-2">
                <Label htmlFor="username" className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <User className="w-4 h-4 text-indigo-500" />
                  用户名
                </Label>
                <div className="relative group">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                  <Input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className={`pl-11 h-11 border-slate-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20 rounded-xl transition-all duration-200 bg-white/80 ${
                      fieldErrors.username ? 'border-red-300' : ''
                    }`}
                    placeholder="选择用户名"
                  />
                </div>
                {fieldErrors.username && (
                  <p className="text-sm text-red-600">{fieldErrors.username}</p>
                )}
                <p className="text-xs text-slate-400">只能包含字母、数字、下划线和连字符</p>
              </div>

              {/* Password field */}
              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <Lock className="w-4 h-4 text-indigo-500" />
                  密码
                </Label>
                <div className="relative group">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className={`pl-11 h-11 border-slate-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20 rounded-xl transition-all duration-200 bg-white/80 ${
                      fieldErrors.password ? 'border-red-300' : ''
                    }`}
                    placeholder="创建密码"
                  />
                </div>
                {fieldErrors.password && (
                  <p className="text-sm text-red-600">{fieldErrors.password}</p>
                )}
                <p className="text-xs text-slate-400">至少8个字符，包含大写字母、数字和特殊字符</p>
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
                className="w-full h-11 bg-gradient-to-r from-indigo-500 via-sky-500 to-cyan-500 hover:from-indigo-600 hover:via-sky-600 hover:to-cyan-600 text-white font-semibold shadow-lg shadow-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/40 transition-all duration-300 rounded-xl animate-gradient"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>创建中...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <span>创建账户</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </div>
                )}
              </Button>

              {/* Login link */}
              <div className="text-center pt-5 border-t border-slate-100">
                <p className="text-sm text-slate-500">
                  已有账号?{' '}
                  <Link
                    to="/login"
                    className="text-indigo-600 hover:text-indigo-700 font-semibold hover:underline transition-all"
                  >
                    立即登录
                  </Link>
                </p>
              </div>
            </form>
          </div>

          {/* Tech decoration */}
          <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-400">
            <div className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></div>
            <span>快速注册 · 安全认证 · 即刻体验</span>
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse animation-delay-2000"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
