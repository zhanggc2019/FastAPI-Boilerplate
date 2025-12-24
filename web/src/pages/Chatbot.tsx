import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bot,
  History,
  Loader2,
  LogOut,
  MessageSquare,
  Plus,
  Search,
  Send,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import api from '@/lib/api';

type ChatRole = 'user' | 'assistant' | 'system';

interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  sources?: ChatMessageSource[];
}

interface ConversationSummary {
  uuid: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface ChatMessageSource {
  id?: string | null;
  document_name?: string | null;
  document_id?: string | null;
  dataset_id?: string | null;
  url?: string | null;
  content?: string | null;
  positions?: string[] | number[][] | null;
  similarity?: number | null;
  vector_similarity?: number | null;
  term_similarity?: number | null;
  doc_type?: string | null;
  image_id?: string | null;
}

const parseTimestamp = (value: string) => {
  if (!value) {
    return new Date();
  }
  const hasTimezone = /[zZ]|[+-]\d{2}:\d{2}$/.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
};

const formatTime = (value: string) =>
  parseTimestamp(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });

const exampleQuestions = [
  '如何定义“双师型”教师？',
  '企业导师参与教学有哪些要求？',
  '职业教育实训基地建设的核心指标是什么？',
  '教师实践管理制度的关键要点？',
];

const extractSources = (content: string) => {
  const normalized = content.replace(/\r\n/g, '\n');
  let mainText = normalized;
  let sourceBlock = '';

  if (normalized.includes('\n---')) {
    const parts = normalized.split('\n---');
    mainText = parts.slice(0, -1).join('\n---').trim();
    sourceBlock = parts[parts.length - 1].trim();
  } else if (/\n来源[:：]/.test(normalized)) {
    const parts = normalized.split(/\n来源[:：]/);
    mainText = parts[0].trim();
    sourceBlock = parts.slice(1).join('\n来源：').trim();
  } else {
    const lines = normalized.split('\n');
    let idx = lines.length - 1;
    while (idx >= 0 && lines[idx].trim() === '') {
      idx -= 1;
    }
    let start = idx;
    while (start >= 0 && /^[\-\*\u2022]\s+/.test(lines[start].trim())) {
      start -= 1;
    }
    if (start < idx) {
      mainText = lines.slice(0, start + 1).join('\n').trim();
      sourceBlock = lines.slice(start + 1, idx + 1).join('\n').trim();
    }
  }

  const sources = sourceBlock
    .split('\n')
    .map((line) => line.replace(/^[\-\*\u2022]\s+/, '').trim())
    .filter(Boolean);

  return {
    mainText: mainText || normalized.trim(),
    sources,
  };
};

const buildSourceLink = (source: ChatMessageSource) => {
  if (source.url) {
    return source.url;
  }
  if (source.dataset_id && source.document_id && source.id) {
    return `/api/v1/assistant/chunks/${source.dataset_id}/${source.document_id}/${source.id}`;
  }
  return '';
};

const formatSourceLabel = (source: ChatMessageSource) => {
  if (source.document_name) {
    return source.document_name;
  }
  if (source.content && source.content.length <= 80) {
    return source.content;
  }
  return '未知文档';
};

const formatSimilarity = (source: ChatMessageSource) => {
  const similarity = source.similarity ?? source.vector_similarity;
  if (typeof similarity === 'number') {
    return `${(similarity * 100).toFixed(1)}%`;
  }
  return null;
};

const getSourceIcon = (source: ChatMessageSource) => {
  if (source.doc_type === 'pdf' || source.document_name?.endsWith('.pdf')) {
    return 'PDF';
  }
  if (source.doc_type === 'docx' || source.document_name?.endsWith('.docx')) {
    return 'DOC';
  }
  if (source.doc_type === 'txt' || source.document_name?.endsWith('.txt')) {
    return 'TXT';
  }
  if (source.image_id) {
    return 'IMG';
  }
  return 'DOC';
};

const renderContentWithCitations = (content: string, sources: ChatMessageSource[]) => {
  if (!sources?.length) return content;

  // 将 [1], [2] 等引文标记转换为可点击的链接
  const citationRegex = /\[(\d+)\]/g;
  const parts: Array<string | { type: 'citation'; index: number }> = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = citationRegex.exec(content)) !== null) {
    // 添加匹配前的文本
    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index));
    }
    // 添加引文
    const index = parseInt(match[1], 10) - 1; // 转换为 0-based 索引
    parts.push({ type: 'citation', index });
    lastIndex = match.index + match[0].length;
  }

  // 添加剩余文本
  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return (
    <>
      {parts.map((part, i) => {
        if (typeof part === 'string') {
          return <span key={`text-${i}-${part.slice(0, 10)}`}>{part}</span>;
        }
        const source = sources[part.index];
        const link = source ? buildSourceLink(source) : '';
        return (
          <sup key={`citation-${part.index}`} className="ml-0.5">
            {link ? (
              <a
                href={link}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-sky-50 text-sky-500 text-[8px] font-medium hover:bg-sky-100 hover:text-sky-600 transition no-underline border border-sky-200"
                title={source ? formatSourceLabel(source) : `来源 ${part.index + 1}`}
              >
                {part.index + 1}
              </a>
            ) : (
              <span
                className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-slate-50 text-slate-400 text-[8px] font-medium border border-slate-200"
                title={`来源 ${part.index + 1}`}
              >
                {part.index + 1}
              </span>
            )}
          </sup>
        );
      })}
    </>
  );
};

const createId = () => {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

export default function Chatbot() {
  const navigate = useNavigate();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeId, setActiveId] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [searchValue, setSearchValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const [userLabel, setUserLabel] = useState('');
  const messageEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login', { replace: true });
    }
  }, [navigate]);

  const fetchConversations = async (keyword?: string) => {
    try {
      const response = await api.get('/chats/', {
        params: keyword ? { keyword } : undefined,
      });
      const items = response.data as ConversationSummary[];
      setConversations(items);
      if (!activeId || !items.some((item) => item.uuid === activeId)) {
        setActiveId(items[0]?.uuid ?? '');
      }
    } catch (err) {
      console.error(err);
      setError('加载聊天记录失败');
    }
  };

  const fetchMessages = async (conversationId: string) => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    try {
      const response = await api.get(`/chats/${conversationId}/messages`);
      const items = response.data as Array<{
        uuid: string;
        role: ChatRole;
        content: string;
        created_at: string;
        sources?: ChatMessageSource[] | null;
      }>;
      setMessages(
        items.map((item) => ({
          id: item.uuid,
          role: item.role,
          content: item.content,
          createdAt: item.created_at,
          sources: item.sources || undefined,
        }))
      );
    } catch (err) {
      console.error(err);
      setError('加载消息失败');
    }
  };

  useEffect(() => {
    fetchConversations(searchValue.trim() || undefined);
  }, [searchValue]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeId, messages]);

  useEffect(() => {
    if (activeId) {
      fetchMessages(activeId);
    }
  }, [activeId]);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await api.get('/users/profile');
        const profile = response.data as { email?: string; username?: string };
        setUserLabel(profile.username || profile.email || '已登录');
      } catch (err) {
        console.error(err);
        setUserLabel('已登录');
      }
    };
    fetchProfile();
  }, []);

  const filteredConversations = useMemo(() => conversations, [conversations]);

  const handleNewChat = async (): Promise<string | null> => {
    try {
      const response = await api.post('/chats/', { title: '新会话' });
      const created = response.data as ConversationSummary;
      setInputValue('');
      setError('');
      setMessages([]);
      await fetchConversations();
      setActiveId(created.uuid);
      return created.uuid;
    } catch (err) {
      console.error(err);
      setError('新建聊天失败');
      return null;
    }
  };

  const handleDeleteConversation = async (id: string) => {
    try {
      await api.delete(`/chats/${id}`);
      await fetchConversations();
      if (activeId === id) {
        setActiveId('');
        setMessages([]);
      }
    } catch (err) {
      console.error(err);
      setError('删除聊天失败');
    }
  };

  const updateAssistantMessage = (messageId: string, append: string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId ? { ...message, content: message.content + append } : message
      )
    );
  };

  const extractContent = (payload: any) =>
    payload?.choices?.[0]?.message?.content ||
    payload?.choices?.[0]?.delta?.content ||
    payload?.answer ||
    '';

  const extractReferences = (payload: any): ChatMessageSource[] => {
    const reference =
      payload?.reference ||
      payload?.data?.reference ||
      payload?.choices?.[0]?.message?.reference ||
      payload?.choices?.[0]?.delta?.reference;
    const docAggs = reference?.doc_aggs;
    const docNameById = new Map<string, string>();
    if (Array.isArray(docAggs)) {
      docAggs.forEach((item: any) => {
        if (item?.doc_id && item?.doc_name) {
          docNameById.set(item.doc_id, item.doc_name);
        }
      });
    } else if (docAggs && typeof docAggs === 'object') {
      Object.values(docAggs).forEach((item: any) => {
        if (item?.doc_id && item?.doc_name) {
          docNameById.set(item.doc_id, item.doc_name);
        }
      });
    }
    const chunks = reference?.chunks;
    if (Array.isArray(chunks)) {
      return chunks.map((chunk: any) => ({
        id: chunk.id,
        document_name: chunk.document_name || docNameById.get(chunk.document_id),
        document_id: chunk.document_id,
        dataset_id: chunk.dataset_id,
        url: chunk.url,
        content: chunk.content,
        positions: Array.isArray(chunk.positions) ? chunk.positions : undefined,
        similarity: chunk.similarity,
        vector_similarity: chunk.vector_similarity,
        term_similarity: chunk.term_similarity,
        doc_type: chunk.doc_type,
        image_id: chunk.image_id,
      }));
    }
    if (chunks && typeof chunks === 'object') {
      return Object.values(chunks).map((chunk: any) => ({
        id: chunk.id,
        document_name: chunk.document_name || docNameById.get(chunk.document_id),
        document_id: chunk.document_id,
        dataset_id: chunk.dataset_id,
        url: chunk.url,
        content: chunk.content,
        positions: Array.isArray(chunk.positions) ? chunk.positions : undefined,
        similarity: chunk.similarity,
        vector_similarity: chunk.vector_similarity,
        term_similarity: chunk.term_similarity,
        doc_type: chunk.doc_type,
        image_id: chunk.image_id,
      }));
    }
    return [];
  };

  const sendMessage = async () => {
    if (!inputValue.trim()) {
      return;
    }
    if (isSending) {
      return;
    }

    let conversationId = activeId;
    if (!conversationId) {
      conversationId = await handleNewChat();
    }
    if (!conversationId) {
      setIsSending(false);
      return;
    }
    const userMessage: ChatMessage = {
      id: createId(),
      role: 'user',
      content: inputValue.trim(),
      createdAt: new Date().toISOString(),
    };
    const assistantMessage: ChatMessage = {
      id: createId(),
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString(),
    };

    setInputValue('');
    setError('');
    setIsSending(true);
    const nextMessages = [...messages, userMessage, assistantMessage];
    setMessages(nextMessages);

    try {
      await api.post(`/chats/${conversationId}/messages`, {
        role: 'user',
        content: userMessage.content,
      });

      const token = localStorage.getItem('token');
      const payload = {
        messages: [...messages, userMessage].map((message) => ({
          role: message.role,
          content: message.content,
        })),
        extra_body: { reference: true },
        stream: isStreaming,
      };

      const response = await fetch('/api/v1/assistant/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText || '请求失败');
      }

      const contentType = response.headers.get('content-type') || '';
      if (isStreaming && response.body && contentType.includes('text/event-stream')) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let assistantContent = '';
        let assistantSources: ChatMessageSource[] = [];
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith('data:')) {
              continue;
            }
            const data = trimmed.replace(/^data:\s*/, '');
            if (data === '[DONE]') {
              break;
            }
            try {
              const parsed = JSON.parse(data);
              const delta = extractContent(parsed);
              if (delta) {
                assistantContent += delta;
                updateAssistantMessage(assistantMessage.id, delta);
              }
              const references = extractReferences(parsed);
              if (references.length) {
                assistantSources = references;
                setMessages((prev) =>
                  prev.map((message) =>
                    message.id === assistantMessage.id ? { ...message, sources: references } : message
                  )
                );
              }
            } catch {
              continue;
            }
          }
        }
        await api.post(`/chats/${conversationId}/messages`, {
          role: 'assistant',
          content: assistantContent || '暂未获取到回答',
          sources: assistantSources.length ? assistantSources : undefined,
        });
      } else {
        const payloadJson = await response.json();
        const answer = extractContent(payloadJson);
        const references = extractReferences(payloadJson);
        updateAssistantMessage(assistantMessage.id, answer || '暂未获取到回答');
        setMessages((prev) =>
          prev.map((message) =>
            message.id === assistantMessage.id ? { ...message, sources: references } : message
          )
        );
        await api.post(`/chats/${conversationId}/messages`, {
          role: 'assistant',
          content: answer || '暂未获取到回答',
          sources: references.length ? references : undefined,
        });
      }
      await fetchConversations();
    } catch (err: any) {
      console.error(err);
      setError(err.message || '发送失败，请稍后重试');
      updateAssistantMessage(assistantMessage.id, '请求失败，请稍后重试。');
    } finally {
      setIsSending(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50 text-slate-900 overflow-hidden">
      <div className="flex h-full">
        <aside className="w-full md:w-80 border-r border-slate-200/80 bg-white/70 backdrop-blur-xl flex flex-col">
          <div className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-300/40">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Knowledge Base</p>
                  <h1 className="text-base font-semibold leading-tight">知识库助手</h1>
                </div>
              </div>
            </div>

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <Input
                placeholder="搜索聊天历史"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="pl-9 bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 h-9 text-sm"
              />
            </div>

            <Button
              onClick={handleNewChat}
              className="w-full bg-gradient-to-r from-indigo-500 via-sky-500 to-cyan-400 text-white font-semibold hover:opacity-90 h-9 text-sm"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              新建聊天
            </Button>
          </div>

          <div className="px-3 pb-3 flex-1 min-h-0">
            <div className="flex items-center gap-1.5 px-2 text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2">
              <History className="w-3 h-3" />
              历史记录
            </div>
            <div className="space-y-1.5 overflow-y-auto pr-1.5 h-[calc(100%-1.5rem)]">
              {filteredConversations.map((conversation) => (
                <div
                  key={conversation.uuid}
                  className={`group w-full rounded-xl border px-3 py-2 transition ${
                    activeId === conversation.uuid
                      ? 'border-sky-300 bg-sky-50'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <button
                      type="button"
                      onClick={() => setActiveId(conversation.uuid)}
                      className="flex-1 text-left min-w-0"
                    >
                      <p className="font-medium text-sm text-slate-900 truncate">{conversation.title}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {formatTime(conversation.updated_at)}
                      </p>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteConversation(conversation.uuid)}
                      className="opacity-0 group-hover:opacity-100 transition text-slate-400 hover:text-slate-900 flex-shrink-0"
                      aria-label="删除会话"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="px-3 pb-3 mt-auto">
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white/80 px-2.5 py-1.5 text-xs text-slate-600">
              <div className="min-w-0">
                <p className="text-[9px] uppercase tracking-[0.2em] text-slate-400">当前账号</p>
                <p className="truncate font-medium text-slate-700 text-xs">{userLabel}</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleLogout}
                className="text-slate-500 hover:text-slate-900 hover:bg-slate-100 h-7 w-7"
              >
                <LogOut className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        </aside>

        <main className="flex-1 flex flex-col min-h-0">
          <header className="border-b border-slate-200 bg-white/80 backdrop-blur-xl px-4 py-2.5 shrink-0">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] uppercase tracking-[0.3em] text-slate-400">Smart Retrieval</p>
                <h2 className="text-base font-semibold text-slate-900 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-sky-500" />
                  {conversations.find((item) => item.uuid === activeId)?.title || '新会话'}
                </h2>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <label className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={isStreaming}
                    onChange={(e) => setIsStreaming(e.target.checked)}
                    className="accent-sky-500"
                  />
                  流式输出
                </label>
              </div>
            </div>
          </header>

          <section className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">
            {messages.length ? (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-3xl px-5 py-4 shadow-md ${
                      message.role === 'user'
                        ? 'bg-sky-50 text-slate-900 border border-sky-100'
                        : 'bg-white text-slate-900 border border-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-500 mb-2">
                      {message.role === 'user' ? (
                        <MessageSquare className="w-3 h-3 text-sky-500" />
                      ) : (
                        <Bot className="w-3 h-3 text-sky-500" />
                      )}
                      {message.role === 'user' ? 'You' : 'Assistant'}
                    </div>
                    <p className="whitespace-pre-wrap leading-relaxed text-sm md:text-base text-slate-800">
                      {(() => {
                        if (message.role !== 'assistant') {
                          return message.content || (message.role === 'assistant' && isSending ? '思考中…' : '');
                        }
                        const displaySources = message.sources?.length
                          ? message.sources
                          : extractSources(message.content).sources.map((item) => ({ content: item }) as ChatMessageSource);
                        const contentToDisplay = message.sources?.length
                          ? message.content
                          : extractSources(message.content).mainText;
                        // 如果有来源数据，使用带引文链接的渲染
                        if (displaySources.length > 0) {
                          return renderContentWithCitations(contentToDisplay || (isSending ? '思考中…' : ''), displaySources);
                        }
                        return contentToDisplay || (isSending ? '思考中…' : '');
                      })()}
                    </p>
                    {message.role === 'assistant' && (() => {
                      const sources = message.sources?.length
                        ? message.sources
                        : extractSources(message.content).sources.map((item) => ({ content: item }) as ChatMessageSource);
                      if (!sources.length) return null;
                      return (
                        <div className="mt-4 rounded-2xl border border-sky-200 bg-gradient-to-br from-sky-50/80 to-indigo-50/80 px-4 py-3">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <div className="w-5 h-5 rounded-full bg-sky-500 flex items-center justify-center">
                                <span className="text-[10px] font-semibold text-white">[{sources.length}]</span>
                              </div>
                              <p className="uppercase tracking-[0.22em] text-[11px] font-semibold text-sky-700">参考来源</p>
                            </div>
                          </div>
                          <ul className="space-y-2">
                            {sources.map((source, index) => {
                              const similarity = formatSimilarity(source);
                              const docType = getSourceIcon(source);
                              const link = buildSourceLink(source);
                              return (
                                <li key={`${source.id || source.document_name || source.content || index}`}>
                                  <div className="group flex items-start gap-2 rounded-xl border border-sky-100 bg-white/60 px-3 py-2 hover:border-sky-300 hover:bg-white hover:shadow-sm transition">
                                    <span className="inline-flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-indigo-400 text-[10px] font-semibold text-white shadow-sm">
                                      {index + 1}
                                    </span>
                                    <div className="min-w-0 flex-1">
                                      <div className="flex items-center gap-1.5 mb-1">
                                        <span className="inline-flex items-center rounded-md bg-slate-100 px-1.5 py-0.5 text-[9px] font-semibold text-slate-600">
                                          {docType}
                                        </span>
                                        <span className="truncate text-xs font-medium text-slate-800">
                                          {formatSourceLabel(source)}
                                        </span>
                                      </div>
                                      {source.content && source.content.length > 0 && (
                                        <p className="text-[10px] text-slate-500 line-clamp-2 leading-relaxed">
                                          {source.content}
                                        </p>
                                      )}
                                      {link && (
                                        <a
                                          href={link}
                                          target="_blank"
                                          rel="noreferrer"
                                          className="inline-flex items-center gap-1 mt-1.5 text-[10px] text-sky-600 hover:text-sky-700 font-medium underline underline-offset-2"
                                        >
                                          查看原文
                                        </a>
                                      )}
                                    </div>
                                    {similarity && (
                                      <div className="flex flex-col items-end gap-1 flex-shrink-0">
                                        <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                                          {similarity}
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                </li>
                              );
                            })}
                          </ul>
                        </div>
                      );
                    })()}
                    <p className="text-[11px] text-slate-500 mt-3">{formatTime(message.createdAt)}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-500">
                <div className="w-12 h-12 rounded-2xl bg-white shadow-sm border border-slate-200 flex items-center justify-center mb-3">
                  <Bot className="w-6 h-6 text-sky-500" />
                </div>
                <h3 className="text-base font-semibold text-slate-900">开始你的第一条提问</h3>
                <p className="text-xs mt-1.5 max-w-md text-slate-400">
                  连接知识库，用自然语言检索答案，支持多轮对话与历史检索。
                </p>
                <div className="mt-4 grid gap-2 w-full max-w-lg sm:grid-cols-2">
                  {exampleQuestions.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => {
                        setInputValue(question);
                        sendMessage();
                      }}
                      className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-left text-xs text-slate-700 shadow-sm hover:border-sky-200 hover:text-slate-900 hover:shadow-md transition"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div ref={messageEndRef} />
          </section>

          <footer className="border-t border-slate-200 bg-white/80 backdrop-blur-xl px-4 py-3 shrink-0">
            {error && (
              <div className="mb-2 text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-xl px-3 py-1.5">
                {error}
              </div>
            )}
            <div className="flex gap-2 items-end">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="输入你的问题，支持多轮上下文"
                className="flex-1 bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 h-10 text-sm"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
              />
              <Button
                onClick={sendMessage}
                disabled={!inputValue.trim() || isSending}
                className="h-10 px-4 bg-gradient-to-r from-sky-500 via-indigo-500 to-purple-500 text-white font-semibold hover:opacity-90 text-sm"
              >
                {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </div>
            <p className="text-[10px] text-slate-500 mt-2 flex items-center gap-1.5">
              <Sparkles className="w-2.5 h-2.5 text-sky-500" />
              系统会自动保存聊天历史到服务器，便于快速检索与追溯。
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
}
