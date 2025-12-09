
import sys
import os
import io
import json
from unittest.mock import MagicMock

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

# Mock environment variables to avoid import errors
os.environ['GEMINI_API_KEY'] = 'fake_key'
os.environ['SUPABASE_URL'] = 'https://fake.supabase.co'
os.environ['SUPABASE_KEY'] = 'fake_key'

# Mock genai before importing the module
import google.generativeai as genai
genai.configure = MagicMock()
genai.GenerativeModel = MagicMock()

# Now import the module
try:
    from app.routes import ocr_tor
except ImportError as e:
    print(f"Import Error: {e}")
    # Try importing assuming we are in backend-gradalyze root
    # Adjust path if needed
    pass

def test_batch_logic():
    print("Testing analyze_tor_with_gemini...")
    
    # Mock the model
    mock_model = MagicMock()
    ocr_tor.gemini_model = mock_model
    
    # Mock response
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "grading_scale": {"97": 1.0, "75": 3.0},
        "grades": [
            {"course_code": "CS101", "subject": "Intro", "grade": 1.5, "units": 3.0}
        ]
    })
    mock_model.generate_content.return_value = mock_response
    
    # Create dummy data (2 pages)
    dummy_data = [
        {
            'page': 1,
            'text_fragments': [([[10, 10], [20, 20]], "Subject 1", 0.9)]
        },
        {
            'page': 2,
            'text_fragments': [([[10, 50], [20, 60]], "Subject 2", 0.9)]
        }
    ]
    
    # Run the function
    result = ocr_tor.analyze_tor_with_gemini(dummy_data)
    
    # Verify calls
    mock_model.generate_content.assert_called_once()
    
    # Verify args
    call_args = mock_model.generate_content.call_args
    prompt_sent = call_args[0][0]
    
    print("Success! generate_content was called exactly once.")
    
    if "--- PAGE 1 ---" in prompt_sent and "--- PAGE 2 ---" in prompt_sent:
        print("Success! Prompt contains data from both pages.")
    else:
        print("Failure! Prompt missing page markers.")
        
    if result['grades'][0]['courseCode'] == "CS101":
        print("Success! Parsed grades correctly.")
    else:
        print("Failure! Grade parsing mismatch.")

    if result['grading_scale']['97'] == 1.0:
        print("Success! Parsed grading scale correctly.")
    else:
        print("Failure! Grading scale parsing mismatch.")

if __name__ == "__main__":
    try:
        test_batch_logic()
        print("\nALL TESTS PASSED.")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
