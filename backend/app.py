from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

from api import pdf_api, manual_api

# from backend.utils.logging.middleware import RequestContextMiddleware
# from backend.utils.logging.error_handler import log_error_to_db


# origins = [
#     "http://localhost:5173",  # Vite React Frontend
#     "http://127.0.0.1:5173",
# ]

# ======================================================
# ENV
# ======================================================
# print("APP STARTED")

ENV = os.getenv("ENV", "local")

# ======================================================
# API AUTH (NOT Swagger)
# ======================================================
api_security = HTTPBearer(auto_error=False)

def api_auth(
    credentials: HTTPAuthorizationCredentials = Depends(api_security),
):
    # LOCAL → no auth
    if ENV == "local":
        return

    # PROD → token required
    token = os.getenv("SWAGGER_TOKEN")
    if not credentials or credentials.credentials != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
 



# ======================================================
# FastAPI App (Swagger ENABLED)
# ======================================================
app = FastAPI(
    title="GSK PO Masking API",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json"
)


# ✅ 1️⃣ Add Request Context Middleware (FIRST)
# app.add_middleware(RequestContextMiddleware) # This adds request_id

# ✅ 2️⃣ CORS Middleware (SECOND)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or "*"" for testing
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# "http://localhost:5173"]

# ✅ 3️⃣ Routers
# Removed auth dependency from pdf_api to allow Power Automate access
app.include_router(pdf_api.router)
app.include_router(manual_api.router)
# app.include_router(invoice_api.router)
# app.include_router(evaluation_api.router, dependencies=[Depends(api_auth)])



@app.get("/")
def root():
    return {"message": "GSK PO Masking API is running."}
# ======================================================

@app.get("/health", tags=["Health Check"])
async def health():
    return {"status": "ok"}


# ======================================================


# Global Error Handler
# @app.exception_handler(Exception)
# async def global_exception_handler(request: Request, exc: Exception):
#     """
#     This catches ANY unhandled exception anywhere in the system.
#     Logs it into ErrorDump table.
#     """

#     log_error_to_db(
#         stage="API_LAYER",
#         error_category="UnhandledException",
#         error_message=str(exc),
#         metadata={
#             "url": str(request.url),
#             "method": request.method
#         }
#     )

#     return JSONResponse(
#         status_code=500,
#         content={"detail": "Internal Server Error"},
#     )