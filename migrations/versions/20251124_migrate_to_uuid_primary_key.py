"""migrate to uuid primary key

Revision ID: 20251124_uuid_pk
Revises: 20251120105430
Create Date: 2025-11-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251124_uuid_pk'
down_revision = '20251120105430'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 删除所有外键约束
    op.drop_constraint('tasks_task_author_id_fkey', 'tasks', type_='foreignkey')
    op.drop_constraint('api_keys_user_id_fkey', 'api_keys', type_='foreignkey')
    
    # 2. 重命名旧的外键列
    op.alter_column('tasks', 'task_author_id', new_column_name='task_author_id_old')
    op.alter_column('api_keys', 'user_id', new_column_name='user_id_old')
    
    # 3. 在 users 表中将 uuid 设为主键
    # 先删除 uuid 的 unique 约束
    op.drop_constraint('users_uuid_key', 'users', type_='unique')
    # 删除旧的主键
    op.drop_constraint('users_pkey', 'users', type_='primary')
    # 将 uuid 设为主键
    op.create_primary_key('users_pkey', 'users', ['uuid'])
    
    # 4. 在 tasks 表中添加新的 task_author_uuid 列并填充数据
    op.add_column('tasks', sa.Column('task_author_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("""
        UPDATE tasks 
        SET task_author_uuid = users.uuid 
        FROM users 
        WHERE tasks.task_author_id_old = users.id
    """)
    op.alter_column('tasks', 'task_author_uuid', nullable=False)
    
    # 5. 在 api_keys 表中添加新的 user_uuid 列并填充数据
    op.add_column('api_keys', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute("""
        UPDATE api_keys 
        SET user_uuid = users.uuid 
        FROM users 
        WHERE api_keys.user_id_old = users.id
    """)
    op.alter_column('api_keys', 'user_uuid', nullable=False)
    
    # 6. 删除旧的 id 列和旧的外键列
    op.drop_column('tasks', 'task_author_id_old')
    op.drop_column('api_keys', 'user_id_old')
    op.drop_column('users', 'id')
    
    # 7. 在 tasks 表中将 uuid 设为主键
    op.drop_constraint('tasks_uuid_key', 'tasks', type_='unique')
    op.drop_constraint('tasks_pkey', 'tasks', type_='primary')
    op.create_primary_key('tasks_pkey', 'tasks', ['uuid'])
    
    # 8. 在 api_keys 表中将 uuid 设为主键
    op.drop_constraint('api_keys_uuid_key', 'api_keys', type_='unique')
    op.drop_constraint('api_keys_pkey', 'api_keys', type_='primary')
    op.create_primary_key('api_keys_pkey', 'api_keys', ['uuid'])
    
    # 9. 重新创建外键约束
    op.create_foreign_key(
        'tasks_task_author_uuid_fkey',
        'tasks', 'users',
        ['task_author_uuid'], ['uuid'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'api_keys_user_uuid_fkey',
        'api_keys', 'users',
        ['user_uuid'], ['uuid']
    )


def downgrade():
    # 1. 删除外键约束
    op.drop_constraint('tasks_task_author_uuid_fkey', 'tasks', type_='foreignkey')
    op.drop_constraint('api_keys_user_uuid_fkey', 'api_keys', type_='foreignkey')
    
    # 2. 在所有表中添加回 id 列
    op.add_column('users', sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=True))
    op.add_column('tasks', sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=True))
    op.add_column('api_keys', sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=True))
    
    # 3. 填充 id 列（使用序列）
    op.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")
    op.execute("SELECT setval('tasks_id_seq', (SELECT MAX(id) FROM tasks))")
    op.execute("SELECT setval('api_keys_id_seq', (SELECT MAX(id) FROM api_keys))")
    
    # 4. 将 id 设为 not null
    op.alter_column('users', 'id', nullable=False)
    op.alter_column('tasks', 'id', nullable=False)
    op.alter_column('api_keys', 'id', nullable=False)
    
    # 5. 恢复主键为 id
    op.drop_constraint('users_pkey', 'users', type_='primary')
    op.drop_constraint('tasks_pkey', 'tasks', type_='primary')
    op.drop_constraint('api_keys_pkey', 'api_keys', type_='primary')
    
    op.create_primary_key('users_pkey', 'users', ['id'])
    op.create_primary_key('tasks_pkey', 'tasks', ['id'])
    op.create_primary_key('api_keys_pkey', 'api_keys', ['id'])
    
    # 6. 恢复 uuid 的 unique 约束
    op.create_unique_constraint('users_uuid_key', 'users', ['uuid'])
    op.create_unique_constraint('tasks_uuid_key', 'tasks', ['uuid'])
    op.create_unique_constraint('api_keys_uuid_key', 'api_keys', ['uuid'])
    
    # 7. 添加旧的外键列
    op.add_column('tasks', sa.Column('task_author_id', sa.BigInteger(), nullable=True))
    op.add_column('api_keys', sa.Column('user_id', sa.BigInteger(), nullable=True))
    
    # 8. 填充旧的外键列
    op.execute("""
        UPDATE tasks 
        SET task_author_id = users.id 
        FROM users 
        WHERE tasks.task_author_uuid = users.uuid
    """)
    op.execute("""
        UPDATE api_keys 
        SET user_id = users.id 
        FROM users 
        WHERE api_keys.user_uuid = users.uuid
    """)
    
    # 9. 设为 not null
    op.alter_column('tasks', 'task_author_id', nullable=False)
    op.alter_column('api_keys', 'user_id', nullable=False)
    
    # 10. 删除新的外键列
    op.drop_column('tasks', 'task_author_uuid')
    op.drop_column('api_keys', 'user_uuid')
    
    # 11. 重新创建外键约束
    op.create_foreign_key('tasks_task_author_id_fkey', 'tasks', 'users', ['task_author_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('api_keys_user_id_fkey', 'api_keys', 'users', ['user_id'], ['id'])

