import os
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates



app = FastAPI()
router_prefix = os.environ.get("ROUTER_PREFIX", "")
if router_prefix and (
    not router_prefix.startswith("/") or router_prefix.endswith("/")
):
    raise ValueError("ROUTER_PREFIX must be empty or start with '/' without a trailing '/'.")

router = APIRouter(prefix=router_prefix)
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")



@router.get("/", response_class=HTMLResponse)
async def hello(request: Request):
    return templates.TemplateResponse(
        name="hello.html", context={"request": request, "message": "Hello, world!"}
    )


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(
        name="about.html", context={"request": request}
    )


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)