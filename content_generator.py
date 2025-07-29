import ast
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

class RateLimitError(Exception):
    """Custom exception for rate limiting"""
    pass

def call_llm_openai(prompt: str, max_tokens: int = 512, temperature: float = 0.95) -> str:
    """Call OpenAI Chat Completion API with enhanced error handling."""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY not set or loaded.")

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    url = "https://api.openai.com/v1/chat/completions"
    
    try:
        resp = httpx.post(url, headers=headers, json=data, timeout=90)
        
        # Handle rate limiting - DON'T WAIT, just raise the error immediately
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("retry-after", 60))
            print(f"OpenAI rate limited. Retry after {retry_after}s - switching to fallback immediately...")
            # DON'T sleep here - let the fallback handle it
            raise RateLimitError("OpenAI rate limit exceeded")
        
        # Handle other HTTP errors
        if resp.status_code == 401:
            raise Exception("Invalid OpenAI API key. Check your key and billing status.")
        elif resp.status_code == 403:
            raise Exception("OpenAI API access forbidden. Check your account permissions.")
        elif resp.status_code >= 500:
            raise Exception(f"OpenAI server error ({resp.status_code}). Try again later.")
        
        resp.raise_for_status()
        response_data = resp.json()
        
        # Enhanced response validation
        if "choices" not in response_data or not response_data["choices"]:
            raise Exception("Invalid response format from OpenAI API")
        
        return response_data["choices"][0]["message"]["content"].strip()
        
    except httpx.TimeoutException:
        raise Exception("OpenAI API request timed out. Check your connection.")
    except httpx.RequestError as e:
        raise Exception(f"OpenAI API connection error: {e}")
    except Exception as e:
        if "429" in str(e) or "rate limit" in str(e).lower():
            raise RateLimitError(str(e))
        raise Exception(f"OpenAI API error: {e}")

def call_llm_perplexity(prompt: str, max_tokens: int = 512, temperature: float = 0.95) -> str:
    """Call Perplexity API as fallback when OpenAI is rate limited."""
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    
    if not PERPLEXITY_API_KEY:
        raise Exception("PERPLEXITY_API_KEY not found in environment variables")
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Using sonar-pro as requested
    data = {
        "model": "sonar-pro",  # ✅ Using sonar-pro
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        print(f"🔄 Calling Perplexity with sonar-pro model...")
        resp = httpx.post("https://api.perplexity.ai/chat/completions", 
                         headers=headers, json=data, timeout=90)
        
        print(f"📡 Perplexity response status: {resp.status_code}")
        
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("retry-after", 30))
            print(f"⏳ Perplexity rate limited. Waiting {retry_after} seconds...")
            time.sleep(min(retry_after, 30))
            raise RateLimitError("Perplexity rate limit exceeded")
        
        if resp.status_code == 400:
            print(f"❌ Perplexity 400 error: {resp.text}")
            raise Exception(f"Perplexity API 400 error: {resp.text}")
        
        resp.raise_for_status()
        response_data = resp.json()
        
        # Enhanced response validation
        if "choices" not in response_data or not response_data["choices"]:
            print(f"❌ Invalid response format: {response_data}")
            raise Exception("Invalid response format from Perplexity API")
            
        content = response_data["choices"][0]["message"]["content"].strip()
        print(f"✅ Perplexity sonar-pro response received: {len(content)} characters")
        
        return content
        
    except httpx.TimeoutException:
        raise Exception("Perplexity API request timed out. Check your connection.")
    except httpx.RequestError as e:
        raise Exception(f"Perplexity API connection error: {e}")
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
        raise Exception(f"Perplexity API HTTP error {e.response.status_code}: {error_detail}")
    except Exception as e:
        if "429" in str(e) or "rate limit" in str(e).lower():
            raise RateLimitError(str(e))
        raise Exception(f"Perplexity API error: {e}")

def call_llm(prompt: str, max_tokens: int = 512, temperature: float = 0.95) -> str:
    """
    Smart LLM caller with automatic fallback from OpenAI to Perplexity on rate limits.
    """
    try:
        # Try OpenAI first
        print("🤖 Attempting OpenAI...")
        return call_llm_openai(prompt, max_tokens, temperature)
    except RateLimitError:
        print("⚠️ OpenAI rate limited, switching to Perplexity sonar-pro...")
        return call_llm_perplexity(prompt, max_tokens, temperature)
    except Exception as openai_error:
        # If OpenAI fails for other reasons, try Perplexity as fallback
        if "rate limit" in str(openai_error).lower() or "429" in str(openai_error):
            print("⚠️ OpenAI rate limited, switching to Perplexity sonar-pro...")
            return call_llm_perplexity(prompt, max_tokens, temperature)
        else:
            # For non-rate-limit errors, try Perplexity once
            try:
                print(f"❌ OpenAI failed ({openai_error}), trying Perplexity sonar-pro as fallback...")
                return call_llm_perplexity(prompt, max_tokens, temperature)
            except Exception as fallback_error:
                raise Exception(f"Both APIs failed. OpenAI: {openai_error} | Perplexity: {fallback_error}")

def generate_content_ideas(topic: str, audience: str = "marketers") -> dict:
    """
    Generate 7 unique content ideas (Mon-Sun) and a brief weekly summary for the given topic and audience.
    
    Args:
        topic: The content topic to generate ideas for
        audience: Target audience (defaults to "marketers")
    
    Returns:
        dict: {"ideas": [...], "summary": "..."}
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Enhanced prompt for better consistency
    prompt = (
        f"You are an expert content strategist creating content for {audience}.\n"
        f"Create 7 unique, engaging content ideas about '{topic}' for a weekly content calendar.\n\n"
        f"Requirements for each idea:\n"
        f"- Tailored specifically for {audience}\n"
        f"- Relevant, actionable, and valuable\n"
        f"- Different approach/angle for each day\n"
        f"- Concise but descriptive (10-15 words max)\n\n"
        f"IMPORTANT: Format your response EXACTLY as a Python list:\n"
        f"['Monday: [specific idea]', 'Tuesday: [specific idea]', 'Wednesday: [specific idea]', 'Thursday: [specific idea]', 'Friday: [specific idea]', 'Saturday: [specific idea]', 'Sunday: [specific idea]']\n\n"
        f"After the list, provide a 2-3 sentence summary of the week's content strategy.\n\n"
        f"Example format:\n"
        f"['Monday: Introduction to {topic} fundamentals for beginners', 'Tuesday: Common {topic} mistakes to avoid', 'Wednesday: Advanced {topic} techniques', 'Thursday: {topic} case studies and examples', 'Friday: Tools and resources for {topic}', 'Saturday: {topic} trends and future outlook', 'Sunday: {topic} community and networking tips']\n\n"
        f"This comprehensive weekly plan educates {audience} about {topic}, progressing from basics to advanced applications while building community engagement."
    )
    
    try:
        print(f"🎯 Generating content ideas for '{topic}' targeting {audience}...")
        response = call_llm(prompt, max_tokens=900, temperature=0.8)
        result = _parse_content_ideas(response, days, topic, audience)
        print(f"✅ Successfully generated {len(result['ideas'])} content ideas")
        return result
    except Exception as e:
        print(f"❌ Error in generate_content_ideas: {e}")
        # Enhanced fallback with more creative ideas
        fallback_ideas = [
            f"Introduction to {topic} basics for {audience}",
            f"Common {topic} challenges and solutions",
            f"Advanced {topic} strategies and techniques", 
            f"Real-world {topic} case studies",
            f"Essential {topic} tools and resources",
            f"Latest {topic} trends and insights",
            f"{topic} community tips and networking"
        ]
        return {
            "ideas": fallback_ideas,
            "summary": f"Comprehensive weekly content plan for {topic} designed to educate and engage {audience}. This fallback plan covers fundamental to advanced concepts with practical applications."
        }

def _parse_content_ideas(raw_response: str, days: list, topic: str, audience: str) -> dict:
    """
    Parse LLM response to extract ideas and summary with enhanced error handling.
    """
    summary = ""
    ideas_final = []
    
    # Enhanced parsing with multiple attempts
    if "[" in raw_response and "]" in raw_response:
        try:
            # Find the list portion with better detection
            start_indices = [i for i, char in enumerate(raw_response) if char == "["]
            end_indices = [i for i, char in enumerate(raw_response) if char == "]"]
            
            # Try each potential list match
            for start_idx in start_indices:
                for end_idx in end_indices:
                    if end_idx > start_idx:
                        try:
                            ideas_raw = raw_response[start_idx:end_idx + 1]
                            ideas_data = ast.literal_eval(ideas_raw)
                            
                            if isinstance(ideas_data, list) and len(ideas_data) >= 5:  # At least 5 ideas
                                # Extract ideas for each day
                                for day in days:
                                    found = next((s for s in ideas_data if isinstance(s, str) and s.strip().lower().startswith(day.lower())), None)
                                    if found and ":" in found:
                                        idea_text = found.split(":", 1)[1].strip()
                                        # Clean up the idea text
                                        idea_text = idea_text.strip('"').strip("'").strip()
                                        ideas_final.append(idea_text)
                                    else:
                                        ideas_final.append(f"Creative {topic} content for {day.lower()}")
                                
                                # Extract summary (text after the list)
                                summary_text = raw_response[end_idx + 1:].strip()
                                summary = summary_text.lstrip(".,;:-\n").strip() if summary_text else ""
                                
                                break
                        except (ValueError, SyntaxError, TypeError):
                            continue
                if ideas_final:
                    break
            
            # If parsing failed, try fallback
            if not ideas_final:
                raise ValueError("Could not parse list format")
                
        except Exception as e:
            print(f"⚠️ Failed to parse list format: {e}")
            ideas_final = _fallback_parse_ideas(raw_response, days, topic)
            summary = f"Strategic weekly content plan for {topic} targeting {audience}."
    else:
        # Fallback parsing for non-list format
        ideas_final = _fallback_parse_ideas(raw_response, days, topic)
        summary = f"Comprehensive weekly content strategy for {topic}, designed to engage {audience} across all seven days."
    
    # Ensure exactly 7 ideas
    ideas_final = ideas_final[:7]
    while len(ideas_final) < 7:
        day_name = days[len(ideas_final)]
        ideas_final.append(f"{day_name.lower()} content idea about {topic}")
    
    return {
        "ideas": ideas_final,
        "summary": summary or f"Comprehensive weekly content strategy for {topic}, designed to engage {audience} across all seven days."
    }

def _fallback_parse_ideas(raw_response: str, days: list, topic: str) -> list:
    """
    Fallback method to extract ideas from unstructured text.
    """
    ideas_final = []
    lines = [line.strip() for line in raw_response.split('\n') if line.strip()]
    
    # Look for day-prefixed lines
    for day in days:
        found_line = None
        for line in lines:
            if line.lower().startswith(day.lower()):
                found_line = line
                break
        
        if found_line and ":" in found_line:
            idea = found_line.split(":", 1)[1].strip()
            ideas_final.append(idea)
        else:
            ideas_final.append(f"Content idea for {day.lower()} about {topic}")
    
    return ideas_final

def summarize_single_idea(topic: str, audience: str, idea: str, day: str) -> str:
    """
    Generate a 2-3 sentence relevance and context summary for a specific day's content idea.
    
    Args:
        topic: Main content topic
        audience: Target audience
        idea: Specific content idea to analyze
        day: Day of the week
    
    Returns:
        str: Analysis summary
    """
    prompt = (
        f"As a content strategist, analyze why this content idea is effective for {day}:\n\n"
        f"Topic: {topic}\n"
        f"Audience: {audience}\n"
        f"Content Idea: {idea}\n\n"
        f"Write 2-3 sentences explaining:\n"
        f"1. Why this idea works well for {day}\n"
        f"2. How it appeals to {audience}\n"
        f"3. What specific value it provides\n\n"
        f"Keep it concise, actionable, and professional."
    )
    
    try:
        return call_llm(prompt, max_tokens=150, temperature=0.7)
    except Exception as e:
        return f"This {day} content idea about {topic} is designed to engage {audience} with relevant, timely information. The content provides valuable insights tailored to their specific needs and interests."

def generate_alternate_idea(topic: str, audience: str, day: str, exclude: str = "") -> str:
    """
    Generate an alternative content idea for the given day, avoiding the excluded idea.
    
    Args:
        topic: Main content topic
        audience: Target audience
        day: Day of the week
        exclude: Content to avoid (optional)
    
    Returns:
        str: Alternative content idea
    """
    exclude_text = f"\n\nDO NOT suggest anything similar to: '{exclude}'" if exclude else ""
    
    prompt = (
        f"Generate a fresh, creative content idea for {day} about '{topic}' targeting {audience}.\n"
        f"Make it engaging, specific, and different from typical content in this space.\n"
        f"Focus on actionable value for {audience}.\n"
        f"Provide ONLY the content idea title/description, no extra text.{exclude_text}"
    )
    
    try:
        result = call_llm(prompt, max_tokens=100, temperature=1.0)
        # Clean up the response
        return result.strip().strip('"').strip("'").strip()
    except Exception as e:
        return f"Alternative {day} content about {topic} for {audience}"

def test_api_connection() -> dict:
    """
    Test both OpenAI and Perplexity API connections.
    Returns status for both APIs.
    """
    results = {
        "openai": {"available": False, "error": None},
        "perplexity": {"available": False, "error": None}
    }
    
    # Test OpenAI
    try:
        test_response = call_llm_openai("Say 'OpenAI test successful'", max_tokens=10, temperature=0.1)
        results["openai"]["available"] = "successful" in test_response.lower()
        if not results["openai"]["available"]:
            results["openai"]["error"] = "Unexpected response format"
    except Exception as e:
        results["openai"]["error"] = str(e)
    
    # Test Perplexity
    try:
        test_response = call_llm_perplexity("Say 'Perplexity test successful'", max_tokens=10, temperature=0.1)
        results["perplexity"]["available"] = "successful" in test_response.lower()
        if not results["perplexity"]["available"]:
            results["perplexity"]["error"] = "Unexpected response format"
    except Exception as e:
        results["perplexity"]["error"] = str(e)
    
    return results

def get_api_status() -> dict:
    """
    Get current API key status and basic info for both services.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    
    status = test_api_connection()
    
    return {
        "openai": {
            "api_key_present": bool(openai_key),
            "api_key_format": openai_key[:10] + "..." + openai_key[-5:] if openai_key else None,
            "api_working": status["openai"]["available"],
            "error": status["openai"]["error"]
        },
        "perplexity": {
            "api_key_present": bool(perplexity_key),
            "api_working": status["perplexity"]["available"],
            "error": status["perplexity"]["error"]
        },
        "fallback_enabled": True
    }

if __name__ == "__main__":
    # Quick test when running directly
    print("Testing Content Generator with Fallback...")
    status = get_api_status()
    print(f"API Status: {status}")
    
    if status["openai"]["api_working"] or status["perplexity"]["api_working"]:
        print("\nGenerating test content...")
        result = generate_content_ideas("artificial intelligence", "marketers")
        print(f"Generated {len(result['ideas'])} ideas")
        print(f"Ideas: {result['ideas']}")
        print(f"Summary: {result['summary']}")
    else:
        print("Both APIs not working. Check your keys and network connection.")
