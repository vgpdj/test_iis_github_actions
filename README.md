# test_iis_github_actions
CI/CD step for siting server

## Hello app

A small FastAPI app that renders `templates/hello.html` at `/`.

With Python 3.10+ and [uv](https://docs.astral.sh/uv/) installed, run from
the repository root:

```sh
uv run uvicorn main:app --reload
```

Open http://127.0.0.1:8000/ to see “Hello, world!”.
