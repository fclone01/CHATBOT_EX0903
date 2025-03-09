# from ai.handle_all import create_routes
from be.routes import create_routes_be
from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware


app  = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",               # Các domain được phép
    allow_credentials=True,
    allow_methods=["*"],                 # GET, POST, PUT, DELETE...
    allow_headers=["*"],                 # Authorization, Content-Type...
)
# app.include_router(create_routes())
app.include_router(create_routes_be(), prefix="/api")

if __name__ == "__main__":
    uvicorn.run(app)