
import json

def parse_items(extracted_data):
    grades = []
    print(f"Input data: {json.dumps(extracted_data, indent=2)}")
    
    for item in extracted_data:
        # Basic validation
        if isinstance(item, dict) and 'grade' in item:
            try:
                # Clean and Normalize
                raw_grade = item.get('grade')
                grade_val = float(raw_grade) if raw_grade is not None else 0.0
                
                # Fixed logic
                subj = str(item.get('subject') or '').strip()
                code = str(item.get('course_code') or '').strip()
                
                print(f"Raw subj: {repr(item.get('subject'))} -> Parsed: {repr(subj)}")
                print(f"Raw code: {repr(item.get('course_code'))} -> Parsed: {repr(code)}")

                # Fix empty fields
                if not subj and code: subj = code
                if not code and subj: code = subj.split(' ')[0]
                
                if not subj and not code: 
                    print("Skipped: No subject and no code")
                    continue

                raw_units = item.get('units')
                units_val = float(raw_units) if raw_units is not None else 3.0

                grades.append({
                    'courseCode': code,
                    'subject': subj,
                    'grade': grade_val,
                    'units': units_val,
                    'semester': str(item.get('semester', 'Detected Subjects'))
                })
            except (ValueError, TypeError) as e:
                print(f"Error parsing item: {e}")
                continue
    return grades

# Test cases
test_data = [
    { "course_code": "ICC 0101", "subject": "Intro to Computing", "units": 2.0, "grade": 1.5 },
    { "course_code": None, "subject": None, "units": 2.0, "grade": 1.5 }, # The 'None' bug case
    { "course_code": "", "subject": "", "units": 2.0, "grade": 1.5 }, # Empty string case
    { "course_code": "EIT 0123", "subject": None, "units": 3.0, "grade": 1.75 } # Partial None
]

results = parse_items(test_data)
print("\nFinal Results:")
print(json.dumps(results, indent=2))
