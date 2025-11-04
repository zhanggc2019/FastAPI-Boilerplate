import uvicorn

from app.core.config import config

if __name__ == "__main__":
    uvicorn.run(
        app="app.core.server:app",
        reload=True if config.ENVIRONMENT != "production" else False,
        workers=1,
    )
