import google.generativeai as genai
import PIL.Image
import json
import os

# 1. Configure the API key
# Ensure you have set GEMINI_API_KEY in your terminal or .env file before running
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY environment variable not found. The API call will fail.")
genai.configure(api_key=api_key)

# 2. Define the System Prompt
# This forces Gemini to act as a plant pathologist and return strictly formatted JSON.
SYSTEM_PROMPT = """
You are an expert agricultural plant pathologist. Analyze the provided image of a crop. 
1. Identify the crop and the disease or pest present. 
2. Determine your confidence level (High, Medium, Low).
3. Provide a single, short, actionable remedy (under 15 words) using accessible treatments.
4. If the image shows a healthy plant, state 'Healthy Crop' for the disease name.
5. If the image is not a plant or is entirely blurry, set the disease name to 'Invalid Image' and the remedy to 'Please submit a clear photo of the crop leaf.'

You must respond strictly in valid JSON format with exactly these keys:
"crop_identified", "disease_name", "confidence", "short_remedy"
"""

# 3. Initialize the Model
# We use gemini-1.5-flash for speed (crucial for hackathon demos) and force a JSON MIME type.
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=SYSTEM_PROMPT,
    generation_config={"response_mime_type": "application/json"}
)

# 4. Define the core function
def diagnose_crop_image(image_input):
    """
    Accepts either a string (file path) or a PIL.Image object.
    Calls the Gemini API and returns a parsed Python dictionary.
    """
    try:
        # Check if the input is a file path (for local testing) or an image object (from Streamlit)
        if isinstance(image_input, str):
            img = PIL.Image.open(image_input)
        else:
            img = image_input

        # Call the Gemini API with the image
        response = model.generate_content([img])
        
        # Parse the JSON string returned by the model into a usable Python dictionary
        result_dict = json.loads(response.text)
        return result_dict

    except Exception as e:
        # Safe fallback so your Streamlit app does not crash during the live pitch
        print(f"Error during diagnosis: {e}")
        return {
            "crop_identified": "Unknown",
            "disease_name": "API Error",
            "confidence": "Low",
            "short_remedy": "System busy or API key missing. Please try again."
        }

# --- Quick Local Test (Runs only if you execute this file directly) ---
if __name__ == "__main__":
    print("Testing vision_engine.py locally...")
    
    # Replace with the name of an actual image in your demo_images folder to test
    test_image_path = "demo_images/tractor.jpg" 
    
    if os.path.exists(test_image_path):
        print(f"Found {test_image_path}, analyzing...")
        result = diagnose_crop_image(test_image_path)
        print("\nFinal Output Dictionary:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Could not find {test_image_path}. Add an image there to test this script directly.")