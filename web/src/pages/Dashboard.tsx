import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Trash2, Key, Eye, EyeOff, Copy, Check } from 'lucide-react';
import { Label } from '@/components/ui/label';

interface ApiKey {
  key: string;  // 加密后的 key (用于删除操作)
  plaintext_key: string;  // 明文 key (用于显示和复制)
  name: string;
  created_at: string;
  is_active: boolean;
  user_uuid: string;
}

export default function Dashboard() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [error, setError] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const fetchApiKeys = async () => {
    try {
      const response = await api.get('/api-keys');
      setApiKeys(response.data);
    } catch (error) {
      console.error('Failed to fetch API keys', error);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const createApiKey = async () => {
    // 验证输入
    if (!newKeyName.trim()) {
      setError('请输入 API Key 名称');
      return;
    }

    setIsCreating(true);
    setError('');

    try {
      await api.post('/api-keys', { name: newKeyName.trim() });
      setNewKeyName('');
      fetchApiKeys();
    } catch (err: any) {
      console.error('Failed to create API key', err);
      if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else {
        setError('创建失败,请稍后重试');
      }
    } finally {
      setIsCreating(false);
    }
  };

  const deleteApiKey = async (encryptedKey: string) => {
    if (!confirm('确定要删除这个 API Key 吗?')) {
      return;
    }

    try {
      // 使用加密后的 key 作为路径参数
      await api.delete(`/api-keys/${encodeURIComponent(encryptedKey)}`);
      fetchApiKeys();
    } catch (error) {
      console.error('Failed to delete API key', error);
      alert('删除失败,请稍后重试');
    }
  };

  const toggleKeyVisibility = (encryptedKey: string) => {
    setVisibleKeys(prev => {
      const newSet = new Set(prev);
      if (newSet.has(encryptedKey)) {
        newSet.delete(encryptedKey);
      } else {
        newSet.add(encryptedKey);
      }
      return newSet;
    });
  };

  const copyToClipboard = async (key: string, encryptedKey: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopiedKey(encryptedKey);
      setTimeout(() => setCopiedKey(null), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard', error);
      alert('复制失败,请手动复制');
    }
  };

  const maskKey = (key: string) => {
    if (key.length <= 8) return '••••••••';
    return key.substring(0, 8) + '••••••••••••••••••••••••';
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="w-5 h-5" />
            创建 API Key
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="keyName" className="text-sm font-medium text-gray-700">
                API Key 名称 <span className="text-red-500">*</span>
              </Label>
              <div className="flex gap-4">
                <div className="flex-1">
                  <Input
                    id="keyName"
                    placeholder="例如: Production API Key"
                    value={newKeyName}
                    onChange={(e) => {
                      setNewKeyName(e.target.value);
                      setError('');
                    }}
                    className={error ? 'border-red-500' : ''}
                    disabled={isCreating}
                  />
                  {error && (
                    <p className="mt-1 text-sm text-red-600">{error}</p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">
                    为您的 API Key 设置一个易于识别的名称
                  </p>
                </div>
                <Button
                  onClick={createApiKey}
                  disabled={isCreating || !newKeyName.trim()}
                  className="whitespace-nowrap"
                >
                  {isCreating ? '创建中...' : '创建'}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>您的 API Keys</CardTitle>
        </CardHeader>
        <CardContent>
          {apiKeys.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Key className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p>还没有创建任何 API Key</p>
              <p className="text-sm mt-1">创建一个 API Key 来开始使用</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名称</TableHead>
                  <TableHead>Key</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.map((apiKey) => {
                  const isVisible = visibleKeys.has(apiKey.key);
                  const isCopied = copiedKey === apiKey.key;
                  // 使用明文 key 进行显示和复制
                  const displayKey = apiKey.plaintext_key || apiKey.key;

                  return (
                    <TableRow key={apiKey.key}>
                      <TableCell className="font-medium">{apiKey.name}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <code className="font-mono text-sm bg-gray-50 px-2 py-1 rounded">
                            {isVisible ? displayKey : maskKey(displayKey)}
                          </code>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => toggleKeyVisibility(apiKey.key)}
                              className="h-8 w-8"
                              title={isVisible ? '隐藏' : '显示'}
                            >
                              {isVisible ? (
                                <EyeOff className="h-4 w-4 text-gray-500" />
                              ) : (
                                <Eye className="h-4 w-4 text-gray-500" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => copyToClipboard(displayKey, apiKey.key)}
                              className="h-8 w-8"
                              title="复制"
                            >
                              {isCopied ? (
                                <Check className="h-4 w-4 text-green-500" />
                              ) : (
                                <Copy className="h-4 w-4 text-gray-500" />
                              )}
                            </Button>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{new Date(apiKey.created_at).toLocaleDateString('zh-CN')}</TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          apiKey.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {apiKey.is_active ? '激活' : '未激活'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deleteApiKey(apiKey.key)}
                          className="hover:bg-red-50"
                          title="删除"
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
