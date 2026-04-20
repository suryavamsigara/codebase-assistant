from fastapi import Request

def get_orchestrator(request: Request):
    return request.app.state.orchestrator