from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


@app.get("/", response_class=HTMLResponse)
async def hello(request: Request):
    return templates.TemplateResponse(
        request=request, name="hello.html", context={"message": "Hello, world!"}
    )
