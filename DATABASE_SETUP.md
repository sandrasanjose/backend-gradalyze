# Database Setup Guide

## New Tables Overview

Two new tables have been added to support academic records and analysis results:

### 1. academic_records
Stores individual course grades and academic information for each student.

### 2. analysis_results
Stores career analysis results including RIASEC personality archetypes and job recommendations.

## Quick Setup

### Step 1: Run the Migration
Execute the SQL script in your Supabase SQL Editor:
```bash
# File location: migrations/create_new_tables.sql
```

### Step 2: Verify Tables
Check that both tables were created with:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('academic_records', 'analysis_results');
```

## Usage Examples

### Python (Backend)

#### Academic Records
```python
from app.models.academic_records import AcademicRecord

# Create a single record
record = AcademicRecord.create({
    'user_id': 1,
    'sub_code': 'CS101',
    'sub_name': 'Introduction to Computer Science',
    'units': 3.0,
    'grades': 1.5,
    'year': 2024,
    'semester': '1st Semester'
})

# Create multiple records
records = AcademicRecord.create_bulk([
    {'user_id': 1, 'sub_name': 'Math 101', 'units': 3, 'grades': 1.75, ...},
    {'user_id': 1, 'sub_name': 'Physics 101', 'units': 4, 'grades': 2.0, ...}
])

# Get all records for a user
user_records = AcademicRecord.get_by_user_id(user_id=1)

# Get records for a specific semester
semester_records = AcademicRecord.get_by_semester(
    user_id=1, 
    year=2024, 
    semester='1st Semester'
)

# Update a record
updated = AcademicRecord.update(record_id=1, {'grades': 1.25})

# Delete a record
AcademicRecord.delete(record_id=1)
```

#### Analysis Results
```python
from app.models.analysis_results import AnalysisResult

# Create analysis result
analysis = AnalysisResult.create({
    'user_id': 1,
    'primary_archetype': 'Investigative',
    'archetype_realistic_perc': 15.5,
    'archetype_investigative_perc': 35.2,
    'archetype_artistic_perc': 12.8,
    'archetype_social_perc': 18.3,
    'archetype_enterprising_perc': 10.1,
    'archetype_conventional_perc': 8.1,
    'career_top_jobs': ['Software Engineer', 'Data Scientist', 'Research Analyst'],
    'career_top_job_scores': [0.92, 0.88, 0.85],
    'job_recommendations': {
        'top_match': 'Software Engineer',
        'match_score': 0.92,
        'description': '...'
    }
})

# Get latest analysis for user
latest = AnalysisResult.get_by_user_id(user_id=1)

# Get all historical analyses
history = AnalysisResult.get_all_by_user_id(user_id=1)

# Create or update (upsert)
result = AnalysisResult.upsert_by_user_id(user_id=1, {
    'primary_archetype': 'Social',
    'archetype_social_perc': 40.0,
    ...
})
```

### API Calls (Frontend)

#### Academic Records
```javascript
// Get all records for a user
const response = await fetch('/api/academic-records/?user_id=1', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const { records } = await response.json();

// Create a new record
await fetch('/api/academic-records/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        user_id: 1,
        sub_code: 'CS101',
        sub_name: 'Intro to CS',
        units: 3.0,
        grades: 1.5,
        year: 2024,
        semester: '1st Semester'
    })
});

// Create multiple records at once
await fetch('/api/academic-records/bulk', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        records: [
            { user_id: 1, sub_name: 'Math', units: 3, grades: 1.75, ... },
            { user_id: 1, sub_name: 'Physics', units: 4, grades: 2.0, ... }
        ]
    })
});
```

#### Analysis Results
```javascript
// Get latest analysis
const response = await fetch('/api/analysis-results/?user_id=1', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const analysis = await response.json();

// Create or update analysis
await fetch('/api/analysis-results/upsert', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        user_id: 1,
        primary_archetype: 'Investigative',
        archetype_realistic_perc: 15.5,
        archetype_investigative_perc: 35.2,
        archetype_artistic_perc: 12.8,
        archetype_social_perc: 18.3,
        archetype_enterprising_perc: 10.1,
        archetype_conventional_perc: 8.1,
        career_top_jobs: ['Software Engineer', 'Data Scientist'],
        career_top_job_scores: [0.92, 0.88],
        job_recommendations: { /* ... */ }
    })
});
```

## Data Relationships

```
users (existing table)
  └─ user_id (PK)
      ├─ academic_records.user_id (FK) - One-to-Many
      └─ analysis_results.user_id (FK) - One-to-Many
```

## Security

- Row Level Security (RLS) is enabled on both tables
- Users can only access their own records
- Foreign key constraints ensure data integrity
- CASCADE delete removes related records when user is deleted

## Notes

- All endpoints require JWT authentication (token_required decorator)
- JSONB fields (career_top_jobs, career_top_job_scores, job_recommendations) support complex data structures
- Timestamps (created_at, updated_at) are automatically managed
- Use the `/upsert` endpoint for analysis_results to avoid duplicate entries per user
