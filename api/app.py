import asyncio
import logging
import traceback
import json
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response

from api.routers.users import router as users_router
from api.routers.products import router as products_router
from api.routers.orders import router as orders_router
from api.routers.cities import router as cities_router
from api.routers.catalog import router as catalog_router
from api.routers.feedback import router as feedback_router
from api.routers.broadcast import router as broadcast_router

from bot.main import setup_handlers, init_models
from bot.loader import bot, dp 

import uvicorn

logging.basicConfig(level=logging.INFO)

class CharsetMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                # Проверяем, есть ли уже заголовок content-type
                has_content_type = False
                for i, (name, value) in enumerate(headers):
                    if name.lower() == b"content-type":
                        has_content_type = True
                        if b"application/json" in value:
                            # Check if charset is already specified
                            if b"charset" not in value:
                                headers[i] = (name, value + b"; charset=utf-8")
                            elif b"utf-8" not in value:
                                # Replace existing charset with utf-8
                                decoded_value = value.decode('latin-1')  # Safe decode
                                if "charset=" in decoded_value:
                                    # Replace charset parameter
                                    updated_value = re.sub(r'charset=[^;]*', 'charset=utf-8', decoded_value)
                                    headers[i] = (name, updated_value.encode('latin-1'))
                                else:
                                    headers[i] = (name, value + b"; charset=utf-8")
                        break
                
                if not has_content_type:
                    headers.append((b"content-type", b"application/json; charset=utf-8"))
                
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    
    setup_handlers() 
    
    logging.info("Starting Telegram Bot...")
    bot_task = asyncio.create_task(dp.start_polling(bot))
    
    yield

    logging.info("Stopping Telegram Bot...")
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass
    await bot.session.close()

app = FastAPI(
    title="Vape Shop Mini App API",
    lifespan=lifespan
)

app.add_middleware(CharsetMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://uniquely-courteous-polecat.cloudpub.ru"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Expose Content-Type header so clients can see the charset
    expose_headers=["Content-Type"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logging.info(f"Response status: {response.status_code}")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Логирует все необработанные исключения перед возвратом 500."""
    tb = traceback.format_exc()
    logging.error(f"500 Internal Server Error on {request.method} {request.url.path}\n{tb}")
    response = JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

# Set default response class to ensure proper charset handling
from fastapi.responses import JSONResponse as FastAPIJSONResponse

class UTF8JSONResponse(FastAPIJSONResponse):
    def __init__(self, *args, **kwargs):
        if "media_type" not in kwargs and "content" in kwargs:
            kwargs.setdefault("media_type", "application/json")
        super().__init__(*args, **kwargs)
        self.init_headers()
    
    def init_headers(self):
        # Ensure charset is always set to utf-8
        if hasattr(self, 'headers'):
            content_type = self.headers.get("content-type", "application/json")
            if "application/json" in content_type:
                if "charset=utf-8" not in content_type:
                    if "charset=" in content_type:
                        # Replace existing charset with utf-8
                        updated_content_type = re.sub(r'charset=[^;]*', 'charset=utf-8', content_type)
                        self.headers["content-type"] = updated_content_type
                    else:
                        self.headers["content-type"] = content_type + "; charset=utf-8"
                else:
                    self.headers["content-type"] = content_type

# Set the custom response class as default for the app
app.default_response_class = UTF8JSONResponse

@app.middleware("http")
async def add_charset_header(request: Request, call_next):
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        # Update content-type header to include charset if not already present
        if "charset" not in content_type:
            response.headers["content-type"] = "application/json; charset=utf-8"
        elif "utf-8" not in content_type:
            # Ensure utf-8 charset is specified
            response.headers["content-type"] = content_type.replace("charset=", "charset=utf-8")
    return response

app.include_router(users_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(cities_router, prefix="/api")
app.include_router(catalog_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(broadcast_router, prefix="/api")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        headers=[("server", "VapeShop")]
    )