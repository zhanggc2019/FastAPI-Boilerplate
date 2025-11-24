-- 迁移 API Keys 表: 使用加密的 key 作为主键
-- 执行前请备份数据库!

BEGIN;

-- 1. 创建临时表保存旧数据
CREATE TABLE api_keys_backup AS SELECT * FROM api_keys;

-- 2. 删除旧表
DROP TABLE api_keys CASCADE;

-- 3. 创建新表 (使用 key 作为主键)
CREATE TABLE api_keys (
    key VARCHAR NOT NULL PRIMARY KEY,  -- 加密后的 key 作为主键
    user_uuid UUID NOT NULL REFERENCES users(uuid),
    name VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. 创建索引
CREATE INDEX idx_api_keys_user_uuid ON api_keys(user_uuid);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);

-- 注意: 旧数据需要手动迁移,因为需要加密 key
-- 如果有旧数据,请使用 Python 脚本进行迁移

COMMIT;

-- 验证
SELECT 
    tablename, 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'api_keys';

\d api_keys

