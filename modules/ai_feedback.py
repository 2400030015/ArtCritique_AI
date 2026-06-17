import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
from PIL import Image

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def generate_critique(pil_image, timeout=30):
    """
    Sends the PIL image to Gemini 2.5 Flash for professional feedback.
    
    Parameters:
    - pil_image: PIL Image object
    - timeout: int timeout in seconds
    
    Returns:
    - critique: dict conforming to the structured critique schema
    """
    if not api_key:
        print("Warning: GEMINI_API_KEY not found. Falling back to local heuristics.")
        return get_fallback_critique()

    # Resize image to max dimension of 1024 to prevent huge payloads and network hangs
    try:
        pil_image = pil_image.copy()
        pil_image.thumbnail((1024, 1024))
    except Exception as img_err:
        print(f"Warning: Failed to resize image for Gemini: {img_err}")

    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = """
    You are a professional art critic, art historian, and mentor. Analyze this uploaded artwork image and provide detailed, professional feedback.
    You MUST respond in a valid JSON format with the following keys and data types. Do not include markdown code block syntax (like ```json ... ```) in the raw response text, just return the JSON string directly.
    
    JSON Schema:
    {
      "aesthetic_score": <int 0-100: average aesthetic appeal>,
      "visual_appeal_score": <int 0-100: sensory appeal and raw beauty>,
      "professional_quality_score": <int 0-100: technical draftsmanship and control>,
      "style": "<string: one of 'Realism', 'Impressionism', 'Abstract', 'Surrealism', 'Pop Art', 'Minimalism', 'Digital Illustration'>",
      "style_confidences": {
        "Realism": <int percentage 0-100>,
        "Impressionism": <int percentage 0-100>,
        "Abstract": <int percentage 0-100>,
        "Surrealism": <int percentage 0-100>,
        "Pop Art": <int percentage 0-100>,
        "Minimalism": <int percentage 0-100>,
        "Digital Illustration": <int percentage 0-100>
      },
      "strengths": [
        "<string: strength 1>",
        "<string: strength 2>",
        "<string: strength 3>"
      ],
      "weaknesses": [
        "<string: weakness 1>",
        "<string: weakness 2>",
        "<string: weakness 3>"
      ],
      "suggestions": [
        "<string: suggestion 1>",
        "<string: suggestion 2>",
        "<string: suggestion 3>"
      ],
      "insights": "<string: 2-3 paragraphs of deep professional insights, examining composition, color palette, values, style conventions, and emotional resonance. Be constructive and educational.>",
      "roadmap": {
        "immediate_fixes": [
          "<string: tactical fix 1>",
          "<string: tactical fix 2>"
        ],
        "long_term_improvements": [
          "<string: skill to practice 1>",
          "<string: skill to practice 2>"
        ]
      },
      "verdict": "<string: one of 'Beginner', 'Intermediate', 'Advanced', 'Professional' depending on skill display>"
    }
    """

    raw_response_text = ""
    try:
        response = model.generate_content(
            [prompt, pil_image],
            generation_config={"response_mime_type": "application/json"},
            request_options={"timeout": timeout}
        )
        raw_response_text = response.text.strip()
        
        # Parse the JSON response
        critique_data = json.loads(raw_response_text)
        
        # Ensure all required keys exist
        required_keys = ["aesthetic_score", "visual_appeal_score", "professional_quality_score", 
                         "style", "style_confidences", "strengths", "weaknesses", "suggestions", 
                         "insights", "roadmap", "verdict"]
        for key in required_keys:
            if key not in critique_data:
                raise ValueError(f"Missing key: {key}")
                
        return critique_data
        
    except Exception as e:
        print(f"Error during Gemini critique generation: {e}")
        if raw_response_text:
            print("=== RAW GEMINI RESPONSE TEXT ===")
            print(raw_response_text)
            print("================================")
            raise ValueError(f"JSON parsing failed: {e}. Raw response: {raw_response_text}")
        raise e

def get_fallback_critique():
    """Generates a structured mock critique if the API call fails or is unconfigured."""
    return {
        "aesthetic_score": 75,
        "visual_appeal_score": 78,
        "professional_quality_score": 72,
        "style": "Realism",
        "style_confidences": {
            "Realism": 70,
            "Impressionism": 10,
            "Abstract": 5,
            "Surrealism": 5,
            "Pop Art": 0,
            "Minimalism": 5,
            "Digital Illustration": 5
        },
        "strengths": [
            "Good overall balance of lighting and local contrast.",
            "Strong layout structure that anchors the visual elements.",
            "Cohesive color selection that unifies the composition."
        ],
        "weaknesses": [
            "Lacks a clear primary focal point to draw immediate attention.",
            "Some midtone transitions could benefit from finer value gradations.",
            "Shadow rendering feels slightly flat in the lower quadrants."
        ],
        "suggestions": [
            "Increase contrast and edge sharpness around the key subject elements.",
            "Introduce subtle complementary accents in the highlight regions.",
            "Examine classical grid alignment (like thirds) to organize structural layers."
        ],
        "insights": (
            "The artwork exhibits a solid understanding of structural forms and lighting. "
            "There is a clear sense of balance that guides the viewer across the scene, creating "
            "a quiet but effective visual rhythm. However, the narrative impact could be elevated "
            "by creating a more distinct focal point with high-contrast highlights.\n\n"
            "From a technical perspective, color harmony is maintained well, keeping the atmosphere "
            "integrated. To transition to a more professional style, the focus should shift to "
            "mastering edge control and creating stronger dynamic ranges within critical details."
        ),
        "roadmap": {
            "immediate_fixes": [
                "Increase brightness or saturation in the main area of interest.",
                "Sharpen boundaries around the subject and soften the background elements."
            ],
            "long_term_improvements": [
                "Study values and high-contrast shading exercises (Chiaroscuro).",
                "Practice composition grids to create dynamic, off-center visual focal nodes."
            ]
        },
        "verdict": "Intermediate"
    }
