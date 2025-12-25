import { useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import remarkGfm from 'remark-gfm';
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
  title?: string | null;
  document_id?: string | null;
  dataset_id?: string | null;
  url?: string | null;
  download_url?: string | null;
  content?: string | null;
  positions?: string[] | number[][] | null;
  similarity?: number | null;
  vector_similarity?: number | null;
  term_similarity?: number | null;
  doc_type?: string | null;
  image_id?: string | null;
}

interface DocReferenceItem {
  key: string;
  name: string;
  url?: string | null;
  docType?: string | null;
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
  '教师队伍建设新形势有哪些?',
  '"双师型"职教师资培养存在的问题？',
  '素提计划实施的整体情况',
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

const buildSourceCacheKey = (source: ChatMessageSource) => {
  if (source.dataset_id && source.document_id && source.id) {
    return `${source.dataset_id}:${source.document_id}:${source.id}`;
  }
  return null;
};

const extractDocumentName = (chunk: any) =>
  chunk?.document_name ||
  chunk?.docnm_kwd ||
  chunk?.doc_name ||
  chunk?.doc?.name ||
  chunk?.doc?.location ||
  chunk?.document?.document_name ||
  chunk?.document?.doc_name ||
  chunk?.document?.name ||
  chunk?.document?.title ||
  chunk?.title ||
  null;

const extractDocumentUrl = (chunk: any) =>
  chunk?.url ||
  chunk?.download_url ||
  chunk?.doc_url ||
  chunk?.document_url ||
  chunk?.document?.url ||
  chunk?.document?.download_url ||
  chunk?.document?.doc_url ||
  chunk?.document?.document_url ||
  chunk?.document?.download_url ||
  chunk?.download_url ||
  null;

const buildSourceLink = (source: ChatMessageSource) => {
  if (source.url) {
    return source.url;
  }
  if (source.download_url) {
    return source.download_url;
  }
  if (source.dataset_id && source.document_id && source.id) {
    return `/api/v1/assistant/chunks/${source.dataset_id}/${source.document_id}/${source.id}`;
  }
  return '';
};

const normalizeApiPath = (link: string) => {
  if (link.startsWith('/api/v1/')) {
    return link.replace('/api/v1', '');
  }
  return link;
};

const getFilenameFromContentDisposition = (value?: string) => {
  if (!value) {
    return '';
  }
  const utf8Match = value.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch {
      return utf8Match[1];
    }
  }
  const asciiMatch = value.match(/filename=\"?([^\";]+)\"?/i);
  return asciiMatch?.[1] ?? '';
};

const openDocumentLink = async (link: string, name?: string) => {
  if (!link) {
    return;
  }
  if (!link.startsWith('/api/v1/')) {
    window.open(link, '_blank');
    return;
  }
  try {
    const response = await api.get(normalizeApiPath(link), {
      responseType: 'blob',
    });
    const blobUrl = URL.createObjectURL(response.data);
    const filenameFromHeader = getFilenameFromContentDisposition(
      response.headers?.['content-disposition']
    );
    const filename = filenameFromHeader || name || 'document';
    const anchor = document.createElement('a');
    anchor.href = blobUrl;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(blobUrl), 30000);
  } catch (err) {
    console.error('打开文档失败', err);
  }
};

const citationSchema = {
  ...defaultSchema,
  tagNames: [...(defaultSchema.tagNames || []), 'span'],
  attributes: {
    ...defaultSchema.attributes,
    '*': [
      ...(defaultSchema.attributes?.['*'] || []),
      'data-citation-id',
      'data-citation-ids',
      'dataCitationId',
      'dataCitationIds',
    ],
  },
};

const injectCitationSpans = (content: string) => {
  // 匹配多种引用格式: [ID:1], [ID: 2], [ID 3], [1] 等
  const citationPattern = /\[(?:ID\s*[: ]\s*)?(\d+)\]/g;
  const buildCitationSpan = (ids: string[]) => {
    if (ids.length === 1) {
      return `<span data-citation-id="${ids[0]}">引文来源</span>`;
    }
    return `<span data-citation-ids="${ids.join(',')}">引文来源</span>`;
  };

  const moved = content.replace(
    /((?:\[(?:ID\s*[: ]\s*)?\d+\])+\s*)([。！？；，,.!?:;])/g,
    (match, group, punctuation) => {
      const ids = Array.from(group.matchAll(citationPattern), (item) => item[1]);
      if (!ids.length) {
        return match;
      }
      return `${punctuation} ${buildCitationSpan(ids)}`;
    }
  );

  return moved.replace(/(?:\[(?:ID\s*[: ]\s*)?\d+\])+/g, (match) => {
    const ids = Array.from(match.matchAll(citationPattern), (item) => item[1]);
    if (!ids.length) {
      return match;
    }
    return buildCitationSpan(ids);
  });
};

const formatSourceLabel = (source: ChatMessageSource) => {
  if (source.title) {
    return source.title;
  }
  if (source.document_name) {
    return source.document_name;
  }
  if (source.content && source.content.length <= 80) {
    return source.content;
  }
  return '未知文档';
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

const formatSimilarity = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }
  return `${(value * 100).toFixed(2)}%`;
};

const resolveSourceByIndex = (sources: ChatMessageSource[], index: number) => {
  if (!Number.isFinite(index)) {
    return undefined;
  }
  if (sources[index]) {
    return sources[index];
  }
  if (index > 0 && sources[index - 1]) {
    return sources[index - 1];
  }
  return undefined;
};

const normalizePositions = (positions: unknown) => {
  if (!Array.isArray(positions)) {
    return undefined;
  }
  const flattened = positions.flatMap((item) => (Array.isArray(item) ? item : [item]));
  const normalized = flattened.filter(
    (item) => typeof item === 'number' || typeof item === 'string'
  );
  return normalized.length ? normalized : undefined;
};

const buildReferenceDocs = (sources: ChatMessageSource[]) => {
  const map = new Map<string, DocReferenceItem>();
  sources.forEach((source) => {
    const label = formatSourceLabel(source);
    const key = source.document_id || label;
    if (!key || map.has(key)) {
      return;
    }
    map.set(key, {
      key,
      name: label,
      url: source.url || source.download_url || null,
      docType: source.doc_type || null,
    });
  });
  return Array.from(map.values());
};

const ReferenceHoverCard = ({
  source,
}: {
  source?: ChatMessageSource;
  index: number;
}) => {
  const label = source ? formatSourceLabel(source) : `引用`;
  const link = source ? buildSourceLink(source) : '';
  const preview = source?.content?.trim();
  const docType = getSourceIcon(source || {});

  return (
    <span className="group/citation relative inline-flex items-center mx-1.5">
      <span className="cursor-pointer rounded border border-sky-200 bg-sky-50 px-1.5 py-0.5 text-[11px] font-semibold text-sky-600 hover:text-sky-700">
        引文来源
      </span>
      {source && (
        <div className="invisible absolute left-0 top-full z-50 mt-2 w-[420px] max-w-[70vw] rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-700 shadow-xl opacity-0 transition-all duration-200 group-hover/citation:visible group-hover/citation:opacity-100">
          {preview && (
            <p className="max-h-40 overflow-auto leading-relaxed text-slate-700">{preview}</p>
          )}
          <div className="mt-3 text-[11px] text-slate-500">
            相似度: {formatSimilarity(source.similarity)}，语义相似度:{' '}
            {formatSimilarity(source.vector_similarity)}，关键词相似度:{' '}
            {formatSimilarity(source.term_similarity)}
          </div>
          <div className="mt-3 flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
            <span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-600">
              {docType}
            </span>
            {link ? (
              <button
                type="button"
                className="truncate text-left text-xs font-medium text-slate-700 hover:text-sky-600"
                title={label}
                onClick={() => openDocumentLink(link, label)}
              >
                {label}
              </button>
            ) : (
              <span className="truncate text-xs font-medium text-slate-700" title={label}>
                {label}
              </span>
            )}
          </div>
        </div>
      )}
    </span>
  );
};

const ReferenceHoverGroup = ({
  items,
}: {
  items: Array<{ index: number; source?: ChatMessageSource }>;
}) => {
  return (
    <span className="group/citation relative inline-flex items-center mx-1.5">
      <span className="cursor-pointer rounded border border-sky-200 bg-sky-50 px-1.5 py-0.5 text-[11px] font-semibold text-sky-600 hover:text-sky-700">
        引文来源
      </span>
      <div className="invisible absolute left-0 top-full z-50 mt-2 w-[420px] max-w-[70vw] rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-700 shadow-xl opacity-0 transition-all duration-200 group-hover/citation:visible group-hover/citation:opacity-100">
        <div className="space-y-2">
          {items.map((item) => {
            const source = item.source;
            const label = source ? formatSourceLabel(source) : `引用`;
            const link = source ? buildSourceLink(source) : '';
            const docType = getSourceIcon(source || {});
            const preview = source?.content?.trim();
            return (
              <div
                key={`${item.index}-${label}`}
                className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"
              >
                {preview && (
                  <p className="mb-1 max-h-24 overflow-auto leading-relaxed text-slate-700">
                    {preview}
                  </p>
                )}
                <div className="flex items-center gap-2">
                  <span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-600">
                    {docType}
                  </span>
                  {link ? (
                    <button
                      type="button"
                      className="truncate text-left text-xs font-medium text-slate-700 hover:text-sky-600"
                      title={label}
                      onClick={() => openDocumentLink(link, label)}
                    >
                      {label}
                    </button>
                  ) : (
                    <span className="truncate text-xs font-medium text-slate-700" title={label}>
                      {label}
                    </span>
                  )}
                </div>
                {source && (
                  <div className="mt-1 text-[11px] text-slate-500">
                    相似度: {formatSimilarity(source.similarity)}，语义相似度:{' '}
                    {formatSimilarity(source.vector_similarity)}，关键词相似度:{' '}
                    {formatSimilarity(source.term_similarity)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </span>
  );
};

const ChatReferenceDocumentList = ({ sources }: { sources: ChatMessageSource[] }) => {
  const docs = useMemo(() => buildReferenceDocs(sources), [sources]);
  if (!docs.length) return null;
  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {docs.map((doc) => (
        <div
          key={doc.key}
          className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700"
        >
          <span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-600">
            {getSourceIcon({ doc_type: doc.docType || undefined, document_name: doc.name })}
          </span>
          {doc.url ? (
            <button
              type="button"
              className="max-w-[260px] truncate text-left font-medium text-slate-800 hover:text-sky-600"
              title={doc.name}
              onClick={() => openDocumentLink(doc.url ?? '', doc.name)}
            >
              {doc.name}
            </button>
          ) : (
            <span className="max-w-[260px] truncate font-medium text-slate-800" title={doc.name}>
              {doc.name}
            </span>
          )}
        </div>
      ))}
    </div>
  );
};

const MarkdownMessage = ({
  content,
  sources,
}: {
  content: string;
  sources: ChatMessageSource[];
}) => {
  if (!content) {
    return null;
  }
  const withCitations = injectCitationSpans(content);
  return (
    <div className="text-sm md:text-base leading-snug text-slate-800 prose prose-slate prose-p:my-0 prose-headings:my-1 prose-ul:my-0 prose-ol:my-0 prose-li:my-0 prose-p:leading-5 prose-li:leading-5 prose-ol:pl-4 prose-ul:pl-4 prose-li:pl-0.5 max-w-none prose-span:font-normal prose-span:text-inherit [&_li>p]:inline [&_li>p]:m-0">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, [rehypeSanitize, citationSchema]]}
        components={{
          span: ({ node, children, ...props }) => {
            const castProps = props as Record<string, string>;
            const citationIds = castProps['data-citation-ids'] || castProps.dataCitationIds;
            if (citationIds) {
              const indices = citationIds
                .split(',')
                .map((value) => Number(value))
                .filter((value) => Number.isFinite(value));
              const items = indices.map((index) => ({
                index,
                source: resolveSourceByIndex(sources, index),
              }));
              return <ReferenceHoverGroup items={items} />;
            }

            const citationId = castProps['data-citation-id'] || castProps.dataCitationId;
            if (citationId) {
              const index = Number(citationId);
              const source = resolveSourceByIndex(sources, index);
              // 如果没有对应的 source，仍然显示引用但没有悬浮效果
              return <ReferenceHoverCard source={source} index={index} />;
            }
            return <span>{children}</span>;
          },
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="text-sky-600 hover:text-sky-700 underline underline-offset-2"
            >
              {children}
            </a>
          ),
          h1: ({ children }) => <h1 className="text-lg font-semibold">{children}</h1>,
          h2: ({ children }) => <h2 className="text-base font-semibold">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-semibold">{children}</h3>,
          ul: ({ children }) => <ul className="list-disc pl-5 space-y-0.5">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 space-y-0.5">{children}</ol>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-slate-200 pl-3 text-slate-600 my-1">
              {children}
            </blockquote>
          ),
        }}
      >
        {withCitations}
      </ReactMarkdown>
    </div>
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
  const sourceCacheRef = useRef<Map<string, ChatMessageSource>>(new Map());
  const renamedConversationsRef = useRef<Set<string>>(new Set());

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

  const hydrateSource = async (source: ChatMessageSource) => {
    const cacheKey = buildSourceCacheKey(source);
    if (!cacheKey) {
      return source;
    }

    const cached = sourceCacheRef.current.get(cacheKey);
    if (cached && (cached.document_name || cached.title || cached.url || cached.download_url || cached.doc_type)) {
      return {
        ...source,
        document_name: source.document_name || cached.document_name,
        title: source.title || cached.title,
        url: source.url || cached.url,
        download_url: source.download_url || cached.download_url,
        doc_type: source.doc_type || cached.doc_type,
      };
    }

    if (source.document_name && (source.url || source.download_url)) {
      sourceCacheRef.current.set(cacheKey, {
        document_name: source.document_name,
        title: source.title,
        url: source.url,
        download_url: source.download_url,
        doc_type: source.doc_type,
      });
      return source;
    }

    try {
      const response = await api.get(`/assistant/chunks/${source.dataset_id}/${source.document_id}/${source.id}`);
      const chunk = response.data;
      const documentName = extractDocumentName(chunk);
      const documentTitle = chunk?.title || chunk?.document?.title || null;
      const documentUrl = extractDocumentUrl(chunk);
      const downloadUrl = chunk?.download_url || chunk?.document?.download_url || null;
      const docType = chunk?.doc_type || source.doc_type || null;
      const merged: ChatMessageSource = {
        ...source,
        document_name: source.document_name || documentName || undefined,
        title: source.title || documentTitle || undefined,
        url: source.url || documentUrl || undefined,
        download_url: source.download_url || downloadUrl || undefined,
        doc_type: docType || undefined,
      };
      sourceCacheRef.current.set(cacheKey, {
        document_name: merged.document_name,
        title: merged.title,
        url: merged.url,
        download_url: merged.download_url,
        doc_type: merged.doc_type,
      });
      return merged;
    } catch (fetchError) {
      console.warn('获取来源详情失败', fetchError);
      return source;
    }
  };

  const hydrateSources = async (sources: ChatMessageSource[]) => {
    if (!sources.length) {
      return sources;
    }
    return Promise.all(sources.map((source) => hydrateSource(source)));
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
      const normalized = items.map((item) => ({
        id: item.uuid,
        role: item.role,
        content: item.content,
        createdAt: item.created_at,
        sources: item.sources || undefined,
      }));
      const hydrated = await Promise.all(
        normalized.map(async (item) => {
          if (!item.sources?.length) {
            return item;
          }
          const sources = await hydrateSources(item.sources);
          return { ...item, sources };
        })
      );
      setMessages(hydrated);
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

  const deriveConversationTitle = (content: string) => {
    const cleaned = content.replace(/\s+/g, ' ').trim();
    if (!cleaned) {
      return '';
    }
    const limit = 32;
    if (cleaned.length <= limit) {
      return cleaned;
    }
    return `${cleaned.slice(0, limit)}…`;
  };

  const maybeRenameConversation = async (conversationId: string, content: string) => {
    if (renamedConversationsRef.current.has(conversationId)) {
      return;
    }
    const currentTitle =
      conversations.find((item) => item.uuid === conversationId)?.title ?? '新会话';
    if (currentTitle !== '新会话') {
      renamedConversationsRef.current.add(conversationId);
      return;
    }
    const nextTitle = deriveConversationTitle(content);
    if (!nextTitle) {
      return;
    }
    try {
      const response = await api.patch(`/chats/${conversationId}`, { title: nextTitle });
      const updated = response.data as ConversationSummary;
      renamedConversationsRef.current.add(conversationId);
      setConversations((prev) =>
        prev.map((item) => (item.uuid === conversationId ? { ...item, title: updated.title } : item))
      );
    } catch (err) {
      console.error('更新会话标题失败', err);
    }
  };

  const updateAssistantMessage = (messageId: string, append: string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId ? { ...message, content: message.content + append } : message
      )
    );
  };

  const updateMessageSources = (messageId: string, sources: ChatMessageSource[]) => {
    setMessages((prev) =>
      prev.map((message) => (message.id === messageId ? { ...message, sources } : message))
    );
  };

  const extractContent = (payload: any) =>
    payload?.choices?.[0]?.message?.content ||
    payload?.choices?.[0]?.delta?.content ||
    payload?.data?.answer ||
    payload?.answer ||
    '';

  const extractReferences = (payload: any): ChatMessageSource[] => {
    const reference =
      payload?.reference ||
      payload?.data?.reference ||
      payload?.choices?.[0]?.message?.reference ||
      payload?.choices?.[0]?.delta?.reference;

    const docNameById = new Map<string, string>();
    const docAggs = reference?.doc_aggs;
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

    const rawChunks = Array.isArray(reference)
      ? reference
      : Array.isArray(reference?.chunks)
        ? reference?.chunks
        : reference?.chunks && typeof reference?.chunks === 'object'
          ? Object.values(reference.chunks)
          : [];

    if (!rawChunks?.length) {
      return [];
    }

    return rawChunks.map((chunk: any) => {
      const documentId = chunk.document_id || chunk.doc_id;
      return {
        id: chunk.id || chunk.chunk_id,
        document_name:
          chunk.document_name ||
          chunk.docnm_kwd ||
          chunk.doc_name ||
          docNameById.get(documentId),
        title: chunk.title,
        document_id: documentId,
        dataset_id: chunk.dataset_id || chunk.kb_id,
        url: chunk.url || chunk.doc_url,
        download_url: chunk.download_url,
        content: chunk.content || chunk.content_with_weight,
        positions: normalizePositions(chunk.positions || chunk.position_int),
        similarity: chunk.similarity,
        vector_similarity: chunk.vector_similarity,
        term_similarity: chunk.term_similarity,
        doc_type: chunk.doc_type || chunk.doc_type_kwd,
        image_id: chunk.image_id || chunk.img_id,
      };
    });
  };

  const sendMessage = async () => {
    if (!inputValue.trim()) {
      return;
    }
    if (isSending) {
      return;
    }

    let conversationId: string | null = activeId || null;
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
      void maybeRenameConversation(conversationId, userMessage.content);

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

      // 使用流式处理，无论 Content-Type 如何，只要 isStreaming=true 且 response.body 存在
      if (isStreaming && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let assistantContent = '';
        let assistantSources: ChatMessageSource[] = [];

        try {
          while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() ?? '';

            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed) {
                continue;
              }
              if (!trimmed.startsWith('data:')) {
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
                  updateMessageSources(assistantMessage.id, references);
                  void (async () => {
                    const hydrated = await hydrateSources(references);
                    assistantSources = hydrated;
                    updateMessageSources(assistantMessage.id, hydrated);
                  })();
                }
              } catch {
                continue;
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
        const finalSources = assistantSources.length ? await hydrateSources(assistantSources) : undefined;
        await api.post(`/chats/${conversationId}/messages`, {
          role: 'assistant',
          content: assistantContent || '暂未获取到回答',
          sources: finalSources?.length ? finalSources : undefined,
        });
      } else {
        const payloadJson = await response.json();
        const answer = extractContent(payloadJson);
        const references = await hydrateSources(extractReferences(payloadJson));
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
                    <div className="whitespace-pre-wrap">
                      {(() => {
                        if (message.role !== 'assistant') {
                          return <MarkdownMessage content={message.content || ''} sources={[]} />;
                        }
                        const displaySources = message.sources?.length
                          ? message.sources
                          : extractSources(message.content).sources.map((item) => ({ content: item }) as ChatMessageSource);
                        const contentToDisplay = message.sources?.length
                          ? message.content
                          : extractSources(message.content).mainText;
                        return (
                          <MarkdownMessage
                            content={contentToDisplay || (isSending ? '正在检索知识库...' : '')}
                            sources={displaySources}
                          />
                        );
                      })()}
                    </div>
                    {message.role === 'assistant' && (() => {
                      const sources = message.sources?.length
                        ? message.sources
                        : extractSources(message.content).sources.map((item) => ({ content: item }) as ChatMessageSource);
                      if (!sources.length) return null;
                      return <ChatReferenceDocumentList sources={sources} />;
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
