import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from faker import Faker


class EnhancedTestDataGenerator:
    """
    增强版测试数据生成器，支持多种数据类型和关系数据生成
    """

    def __init__(self, locale: str = "zh_CN", seed: Optional[int] = None):
        self.fake = Faker(locale)
        if seed is not None:
            self.fake.seed_instance(seed)
            random.seed(seed)

    def generate_user_data(self, count: int = 1, **kwargs) -> List[Dict[str, Any]]:
        """生成用户数据"""
        users = []

        for _ in range(count):
            user = {
                "username": kwargs.get("username", self.fake.user_name()),
                "email": kwargs.get("email", self.fake.email()),
                "password": kwargs.get("password", self.fake.password(length=12)),
                "full_name": kwargs.get("full_name", self.fake.name()),
                "phone": kwargs.get("phone", self.fake.phone_number()),
                "avatar": kwargs.get("avatar", self.fake.image_url()),
                "is_active": kwargs.get("is_active", random.choice([True, False])),
                "is_superuser": kwargs.get("is_superuser", False),
                "created_at": kwargs.get("created_at", self.fake.date_time_between(start_date="-1y")),
                "updated_at": kwargs.get("updated_at", datetime.now()),
                "last_login": kwargs.get("last_login", self.fake.date_time_between(start_date="-30d")),
                "profile": {
                    "bio": self.fake.text(max_nb_chars=200),
                    "birth_date": self.fake.date_of_birth(minimum_age=18, maximum_age=65),
                    "location": self.fake.address(),
                    "website": self.fake.url(),
                    "social_links": {
                        "twitter": f"@{self.fake.user_name()}",
                        "github": self.fake.user_name(),
                        "linkedin": self.fake.user_name(),
                    },
                },
            }
            users.append(user)

        return users if count > 1 else users[0]

    def generate_task_data(self, count: int = 1, author_id: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """生成任务数据"""
        tasks = []
        statuses = ["pending", "in_progress", "completed", "cancelled"]
        priorities = ["low", "medium", "high", "urgent"]

        for _ in range(count):
            status = kwargs.get("status", random.choice(statuses))
            is_completed = status == "completed"

            task = {
                "title": kwargs.get("title", self.fake.sentence(nb_words=6)),
                "description": kwargs.get("description", self.fake.text(max_nb_chars=500)),
                "status": status,
                "priority": kwargs.get("priority", random.choice(priorities)),
                "is_completed": is_completed,
                "author_id": author_id or random.randint(1, 100),
                "due_date": kwargs.get("due_date", self.fake.date_time_between(start_date="-30d", end_date="+30d")),
                "completed_at": datetime.now() if is_completed else None,
                "created_at": kwargs.get("created_at", self.fake.date_time_between(start_date="-90d")),
                "updated_at": kwargs.get("updated_at", datetime.now()),
                "tags": kwargs.get("tags", [self.fake.word() for _ in range(random.randint(1, 5))]),
                "metadata": {
                    "estimated_hours": random.randint(1, 40),
                    "actual_hours": random.randint(1, 50) if is_completed else None,
                    "complexity": random.choice(["simple", "medium", "complex"]),
                    "category": self.fake.word(),
                },
            }
            tasks.append(task)

        return tasks if count > 1 else tasks[0]

    def generate_auth_data(self, **kwargs) -> Dict[str, Any]:
        """生成认证数据"""
        return {
            "email": kwargs.get("email", self.fake.email()),
            "password": kwargs.get("password", self.fake.password(length=12)),
            "username": kwargs.get("username", self.fake.user_name()),
            "remember_me": kwargs.get("remember_me", random.choice([True, False])),
            "user_agent": kwargs.get("user_agent", self.fake.user_agent()),
            "ip_address": kwargs.get("ip_address", self.fake.ipv4()),
            "login_time": kwargs.get("login_time", datetime.now()),
        }

    def generate_oauth_data(self, provider: str = "google", **kwargs) -> Dict[str, Any]:
        """生成OAuth数据"""
        base_data = {
            "provider": provider,
            "access_token": kwargs.get("access_token", self.fake.sha256(raw_output=False)[:32]),
            "refresh_token": kwargs.get("refresh_token", self.fake.sha256(raw_output=False)[:32]),
            "expires_at": kwargs.get("expires_at", datetime.now() + timedelta(hours=1)),
            "scope": kwargs.get("scope", "openid email profile"),
            "user_info": {
                "id": self.fake.uuid4(),
                "email": self.fake.email(),
                "name": self.fake.name(),
                "picture": self.fake.image_url(),
            },
        }

        if provider == "google":
            base_data["user_info"].update(
                {"given_name": self.fake.first_name(), "family_name": self.fake.last_name(), "locale": "zh-CN"}
            )
        elif provider == "github":
            base_data["user_info"].update(
                {
                    "login": self.fake.user_name(),
                    "html_url": self.fake.url(),
                    "company": self.fake.company(),
                    "location": self.fake.city(),
                }
            )

        return base_data

    def generate_api_response_data(self, endpoint: str, status_code: int = 200, **kwargs) -> Dict[str, Any]:
        """生成API响应数据"""
        base_response = {
            "status_code": status_code,
            "success": 200 <= status_code < 300,
            "message": kwargs.get("message", self.fake.sentence()),
            "timestamp": kwargs.get("timestamp", datetime.now().isoformat()),
            "request_id": kwargs.get("request_id", self.fake.uuid4()),
            "data": kwargs.get("data", {}),
            "metadata": {
                "version": "v1",
                "took": random.randint(10, 500),  # 响应时间（毫秒）
                "server": self.fake.hostname(),
            },
        }

        if 400 <= status_code < 500:
            base_response.update(
                {
                    "error": {
                        "code": f"CLIENT_ERROR_{status_code}",
                        "details": kwargs.get("details", self.fake.text(max_nb_chars=200)),
                    }
                }
            )
        elif status_code >= 500:
            base_response.update({"error": {"code": f"SERVER_ERROR_{status_code}", "details": "Internal server error"}})

        return base_response

    def generate_pagination_data(self, total_items: int = 100, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """生成分页数据"""
        total_pages = (total_items + per_page - 1) // per_page

        return {
            "total": total_items,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "next_page": page + 1 if page < total_pages else None,
            "prev_page": page - 1 if page > 1 else None,
            "items": [],  # 实际项目数据需要另外填充
        }

    def generate_related_data(self, user_count: int = 10, task_count: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """生成关联数据（用户和任务）"""
        users = self.generate_user_data(user_count)
        tasks = []

        # 为每个用户生成任务
        for user in users:
            user_tasks = self.generate_task_data(
                count=random.randint(1, task_count // user_count + 1), author_id=user.get("id", random.randint(1, 1000))
            )
            tasks.extend(user_tasks)

        return {
            "users": users,
            "tasks": tasks,
            "stats": {
                "total_users": len(users),
                "total_tasks": len(tasks),
                "avg_tasks_per_user": len(tasks) / len(users) if users else 0,
            },
        }

    def generate_invalid_data(self, data_type: str = "email", error_type: str = "format") -> Dict[str, Any]:
        """生成无效数据（用于测试验证）"""
        invalid_data = {}

        if data_type == "email":
            if error_type == "format":
                invalid_data["email"] = "invalid-email-format"
            elif error_type == "missing":
                invalid_data["email"] = ""
            elif error_type == "too_long":
                invalid_data["email"] = "a" * 100 + "@example.com"

        elif data_type == "password":
            if error_type == "too_short":
                invalid_data["password"] = "123"
            elif error_type == "too_long":
                invalid_data["password"] = "a" * 1000
            elif error_type == "missing":
                invalid_data["password"] = ""

        elif data_type == "username":
            if error_type == "too_short":
                invalid_data["username"] = "ab"
            elif error_type == "too_long":
                invalid_data["username"] = "a" * 50
            elif error_type == "invalid_chars":
                invalid_data["username"] = "user@name!"

        return {**self.generate_user_data(), **invalid_data}


class TestDataManager:
    """
    测试数据管理器，负责管理和清理测试数据
    """

    def __init__(self):
        self.generator = EnhancedTestDataGenerator()
        self.created_data: Dict[str, List[Any]] = {"users": [], "tasks": [], "auth_sessions": []}

    async def create_test_user(self, **kwargs) -> Dict[str, Any]:
        """创建测试用户"""
        user_data = self.generator.generate_user_data(**kwargs)
        self.created_data["users"].append(user_data)
        return user_data

    async def create_test_task(self, author_id: int, **kwargs) -> Dict[str, Any]:
        """创建测试任务"""
        task_data = self.generator.generate_task_data(author_id=author_id, **kwargs)
        self.created_data["tasks"].append(task_data)
        return task_data

    async def create_test_data_set(self, users: int = 5, tasks_per_user: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """创建完整的测试数据集"""
        data_set = self.generator.generate_related_data(users, users * tasks_per_user)

        self.created_data["users"].extend(data_set["users"])
        self.created_data["tasks"].extend(data_set["tasks"])

        return data_set

    def get_created_users(self) -> List[Dict[str, Any]]:
        """获取已创建的用户数据"""
        return self.created_data["users"]

    def get_created_tasks(self) -> List[Dict[str, Any]]:
        """获取已创建的任务数据"""
        return self.created_data["tasks"]

    def cleanup_data(self, data_type: Optional[str] = None) -> None:
        """清理测试数据"""
        if data_type is None:
            # 清理所有数据
            self.created_data = {"users": [], "tasks": [], "auth_sessions": []}
        elif data_type in self.created_data:
            self.created_data[data_type] = []

    def get_data_stats(self) -> Dict[str, int]:
        """获取数据统计"""
        return {
            "total_users": len(self.created_data["users"]),
            "total_tasks": len(self.created_data["tasks"]),
            "total_auth_sessions": len(self.created_data["auth_sessions"]),
        }


# 创建全局测试数据管理器实例
test_data_manager = TestDataManager()


# 便捷函数
def generate_test_user(**kwargs) -> Dict[str, Any]:
    """生成测试用户"""
    return test_data_manager.generator.generate_user_data(**kwargs)


def generate_test_task(**kwargs) -> Dict[str, Any]:
    """生成测试任务"""
    return test_data_manager.generator.generate_task_data(**kwargs)


def generate_test_auth_data(**kwargs) -> Dict[str, Any]:
    """生成测试认证数据"""
    return test_data_manager.generator.generate_auth_data(**kwargs)


def generate_test_oauth_data(**kwargs) -> Dict[str, Any]:
    """生成测试OAuth数据"""
    return test_data_manager.generator.generate_oauth_data(**kwargs)


def generate_invalid_test_data(data_type: str = "email", error_type: str = "format") -> Dict[str, Any]:
    """生成无效测试数据"""
    return test_data_manager.generator.generate_invalid_data(data_type, error_type)
