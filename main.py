from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from archimede import Api
api = Api("<username>", "<password>")

limiter = Limiter(key_func=get_remote_address, default_limits=["2/5seconds", "10/minute"])
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = ["http://127.0.0.1/", "http://localhost", "http://192.168.1.75"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)

@app.get("/getHomework/{corsoId}")
def getHomework(request: Request, corsoId: str):
    return api.getHomework(corsoId)