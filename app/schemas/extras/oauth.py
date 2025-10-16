from pydantic import BaseModel


class OAuthLogin(BaseModel):
    code: str


class OAuthProvider(str):
    GOOGLE = "google"
    GITHUB = "github"
    WECHAT = "wechat"
    ALIPAY = "alipay"
