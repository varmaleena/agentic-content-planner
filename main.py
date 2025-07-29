import os
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, constr
from sqlalchemy.orm import Session

from app.agents.content_generator import (generate_alternate_idea,
                                          generate_content_ideas,
                                          summarize_single_idea)
from app.database.models import ScheduledPost, SessionLocal

app = FastAPI()

NonEmptyStr = constr(min_length=1)

class PostInput(BaseModel):
    idea: NonEmptyStr
    date: date

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Agentic Content Planner backend is running with OpenAI + Perplexity fallback."}

@app.get("/plan-content")
def plan_content(
    topic: str = Query("branding", description="Topic for content ideas"),
    audience: str = Query("Adults", description="Intended audience"),
    model: str = Query("auto", description="LLM provider: openai, perplexity, or auto (fallback)")
):
    """
    Generate content ideas with automatic fallback.
    The content_generator.py already handles OpenAI -> Perplexity fallback automatically.
    """
    try:
        # The content_generator.py handles fallback automatically
        result = generate_content_ideas(topic, audience)
        
    except Exception as e:
        print(f"ERROR in /plan-content: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {e}")
    
    return {
        "topic": topic,
        "ideas": result["ideas"],
        "summary": result["summary"],
        "model_used": "auto_fallback"
    }

@app.get("/summarize-idea")
def summarize_idea(
    topic: str,
    audience: str,
    idea: str,
    day: str,
    model: str = Query("auto", description="LLM provider")
):
    """
    Summarize idea with automatic fallback.
    """
    try:
        # The content_generator.py handles fallback automatically
        summary = summarize_single_idea(topic, audience, idea, day)
                
    except Exception as e:
        print(f"ERROR in /summarize-idea: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")
    
    return {"summary": summary or "No summary available."}

@app.get("/alternate-idea")
def alternate_idea(
    topic: str,
    audience: str,
    day: str,
    exclude: str = "",
    model: str = Query("auto", description="LLM provider")
):
    """
    Generate alternate idea with automatic fallback.
    """
    try:
        # The content_generator.py handles fallback automatically
        idea = generate_alternate_idea(topic, audience, day, exclude)
                
    except Exception as e:
        print(f"ERROR in /alternate-idea: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Alternate idea generation failed: {e}")
    
    return {"idea": idea}

# Database endpoints remain unchanged
@app.post("/schedule-post")
def schedule_post(post: PostInput, db: Session = Depends(get_db)):
    existing = db.query(ScheduledPost).filter(
        ScheduledPost.idea == post.idea,
        ScheduledPost.date == str(post.date)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this idea and date already exists.")
    
    new_post = ScheduledPost(idea=post.idea, date=str(post.date))
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {
        "message": "Post scheduled!",
        "post": {"id": new_post.id, "idea": new_post.idea, "date": new_post.date}
    }

@app.get("/scheduled-posts")
def get_scheduled_posts(db: Session = Depends(get_db)):
    posts = db.query(ScheduledPost).all()
    return {"scheduled_posts": [{"id": post.id, "idea": post.idea, "date": post.date} for post in posts]}

@app.put("/scheduled-posts/{post_id}")
def update_scheduled_post(post_id: int, post: PostInput, db: Session = Depends(get_db)):
    existing_post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    duplicate = db.query(ScheduledPost).filter(
        ScheduledPost.idea == post.idea,
        ScheduledPost.date == str(post.date),
        ScheduledPost.id != post_id
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="A post with this idea and date already exists.")
    
    existing_post.idea = post.idea
    existing_post.date = str(post.date)
    db.commit()
    db.refresh(existing_post)
    return {
        "message": f"Post with id {post_id} updated.",
        "post": {"id": existing_post.id, "idea": existing_post.idea, "date": existing_post.date}
    }

@app.delete("/scheduled-posts/{post_id}")
def delete_scheduled_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return {"message": f"Post with id {post_id} deleted."}

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "openai_available": bool(os.getenv("OPENAI_API_KEY")),
        "perplexity_available": bool(os.getenv("PERPLEXITY_API_KEY")),
        "fallback_enabled": True
    }

# Debug endpoint to check API status
@app.get("/api-status")
def api_status():
    """Debug endpoint to check which APIs are working."""
    from app.agents.content_generator import get_api_status
    return get_api_status()
