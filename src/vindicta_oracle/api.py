"""Meta-Oracle API - REST interface for list grading and council debates."""
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from meta_oracle.grader import ListGrader
from meta_oracle.models import GradeRequest, GradeResponse
from meta_oracle.ollama_client import OllamaConfig

app = FastAPI(
    title="Meta-Oracle API",
    description="AI council debate engine for competitive wargaming.",
    version="0.3.0"
)

router = APIRouter(prefix="/api/v1")


def get_grader() -> ListGrader:
    """Dependency provider for ListGrader."""
    # Custom config could be injected here
    return ListGrader()


@router.post("/grade", response_model=GradeResponse)
async def grade_list(
    request: GradeRequest,
    grader: ListGrader = Depends(get_grader)
) -> GradeResponse:
    """Submit an army list for AI council grading.
    
    Grading involves a 3-round adversarial debate between 5 specialized agents.
    """
    try:
        # Check units validity (extra safety beyond Pydantic)
        if not request.army_list.units:
            raise HTTPException(status_code=400, detail="List must have at least 1 unit")
            
        return await grader.grade(request)
        
    except ConnectionError:
        raise HTTPException(status_code=503, detail="AI service (Ollama) unavailable")
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Debate timed out")
    except Exception as e:
        # In a real system, we'd log this with a correlation ID
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "operational", "version": "0.3.0"}


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
