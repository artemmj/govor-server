# from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware


# @asynccontextmanager
# async def lifespan(_: FastAPI):
#     async with redis_dependency.get_client() as redis_client:
#         try:
#             await ws_manager.start(redis_client)
#             yield
#         finally:
#             await ws_manager.stop()


origins = [
    # "http://localhost:5173",
    # "http://127.0.0.1:5173",
    # "https://your-production-app.com"
]

app = FastAPI(
    title="FastMessenger API",
    # lifespan=lifespan,
    # root_path="/api/v1/crm",
    # docs_url="/docs",
    # redoc_url="/redoc",
    # openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_credentials=True,  # Разрешить передачу cookies / auth-заголовков
    allow_methods=[
        "*"
    ],  # Разрешить ВСЕ методы, включая POST, GET, и критически важный OPTIONS
    allow_headers=["*"],  # Разрешить любые HTTP-заголовки
)

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(router)
