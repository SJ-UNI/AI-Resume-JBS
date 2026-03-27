# Resume Match System - Comprehensive Project Analysis

## 1. Project Purpose & Main Functionality

### Overview
The **AI Resume – Job Matching System** is an intelligent candidate-job matching platform that uses semantic embeddings and heuristic analysis to automatically rank and analyze resumes against job requirements.

### Key Features
- **Single Resume Analysis**: Detailed analysis of a single resume against job requirements
- **Bulk Resume Ranking**: Comparative ranking of multiple candidates for a single job
- **Semantic Matching**: Advanced similarity matching between job descriptions and resumes
- **Skill Assessment**: Automatic skill matching with synonym expansion (e.g., "JS" → "JavaScript", "ML" → "Machine Learning")
- **Experience Extraction**: Automatic extraction of years of experience from resume text
- **AI Insights Dashboard**: Analytics including common skill gaps, top candidates, and hiring tips
- **CSV Export**: Export bulk ranking results for further processing
- **Real-time Analytics**: Track analysis patterns and metrics
- **Responsive UI**: Desktop, tablet, and mobile-friendly interface

### Use Cases
1. **Recruiters**: Quick screening of candidates for specific roles
2. **HR Teams**: Bulk processing of applications to save screening time (80% time reduction claimed)
3. **Hiring Managers**: Getting AI-powered insights about candidate suitability
4. **Analytics**: Understanding skill gaps and hiring trends

---

## 2. Architecture & Component Interaction

### High-Level Architecture
```
┌─────────────────────────────────────────┐
│        Flask Web Application            │
│           (app.py)                      │
├──────────────┬──────────────────────────┤
│              │                          │
│  Frontend    │   Backend Services       │
│  (HTML/CSS   │   • Matching Engine      │
│   /JavaScript)│   • File Processing     │
│              │   • Analytics            │
└──────────────┴──────────────────────────┘
        │              │
        ▼              ▼
┌─────────────────────────────────────────┐
│        Core Components                  │
│  ┌──────────────────────────────────┐   │
│  │ SemanticMatcher (model.py)       │   │
│  │ - Sentence Transformers          │   │
│  │ - Skill Analysis                 │   │
│  │ - Experience Extraction          │   │
│  │ - Score Computation              │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │ ResumeDatabase (database.py)     │   │
│  │ - Supabase Integration           │   │
│  │ - Data Persistence               │   │
│  │ - Analytics Storage              │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │ Utilities (utils.py)             │   │
│  │ - PDF/DOCX Extraction            │   │
│  │ - Text Preprocessing             │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│      External Services                  │
│  • Supabase (PostgreSQL)                │
│  • Sentence Transformers Model          │
│  • PyMuPDF & python-docx                │
└─────────────────────────────────────────┘
```

### Data Flow

#### Single Resume Analysis Flow
```
User Input (Job Details + Resume File)
        │
        ▼
extract_text_from_file() [utils.py]
        │
        ├─ PDF → fitz.open() → text extraction
        └─ DOCX → python-docx → text extraction
        │
        ▼
preprocess() [utils.py]
        │
        ├─ Lowercase
        ├─ Expand abbreviations (ML→Machine Learning)
        └─ Clean special characters
        │
        ▼
SemanticMatcher.compute_scores() [model.py]
        │
        ├─ Load sentence-transformers model (all-MiniLM-L6-v2)
        ├─ Generate embeddings for job & resume
        ├─ Calculate semantic similarity (cosine)
        ├─ Analyze skill matching (with synonyms)
        ├─ Extract experience years (regex patterns)
        └─ Compute weighted final score
                (70% semantic + 25% skills + 5% experience)
        │
        ▼
Generate Insights
        │
        ├─ Matched/missing skills
        ├─ Personalized suggestions
        ├─ Key strengths & areas for improvement
        └─ Match quality classification
        │
        ▼
Save to Supabase [database.py]
        │
        ├─ analyses table (session metadata)
        ├─ candidates table (candidate details)
        └─ skill_stats table (aggregate statistics)
        │
        ▼
JSON Response to Frontend
```

#### Bulk Resume Ranking Flow
```
User Input (Job Details + Multiple Resume Files)
        │
        ▼
Process All Files
        │
        ├─ For each file:
        │  ├─ Extract & preprocess text
        │  └─ Add to batch
        │
        ▼
Batch Scoring
        │
        ├─ Generate embeddings for all resumes
        ├─ Calculate scores in parallel
        ├─ Extract candidate names from files/text
        │
        ▼
Rank & Sort
        │
        ├─ Sort by score (descending)
        ├─ Assign rank positions
        └─ Calculate summary statistics
        │
        ▼
Save Batch Results
        │
        ├─ Store in Supabase
        └─ Keep in-memory for CSV export
        │
        ▼
Return Ranked List + Summary
```

---

## 3. Key Files and Their Responsibilities

### Core Application Files

#### [app.py](app.py) - Main Flask Application
**Responsibility**: HTTP request handling, routing, and orchestration

**Key Classes/Functions**:
- `get_matcher()`: Lazy-loads SemanticMatcher instance
- `extract_candidate_name()`: Extracts name from resume or filename using regex
- `get_match_quality()`: Maps numeric score to quality labels (Excellent/Good/Moderate/Poor)
- **Routes**:
  - `GET /`: Homepage (renders index.html)
  - `POST /match_single`: Single resume analysis
  - `POST /match_bulk`: Bulk ranking of multiple resumes
  - `GET /export_csv`: Export last bulk results as CSV
  - `GET /insights/skill_gaps`: Top missing skills across all analyses
  - `GET /insights/metrics`: High-level analytics (total resumes, avg score, total analyses)
  - `GET /insights/top_candidates`: Historical top performers
  - `GET /insights/hiring_tips`: Dynamic hiring recommendations
- **Global State**: 
  - `matcher`: Singleton SemanticMatcher instance
  - `db`: ResumeDatabase instance
  - `last_bulk_results`: In-memory cache of latest bulk analysis

**Processing Logic**:
- Input validation and file type checking (PDF, DOCX only)
- Text extraction and preprocessing
- Score computation and quality classification
- Database persistence
- Response serialization

#### [model.py](model.py) - Semantic Matching Engine
**Responsibility**: AI-powered resume-job matching and scoring

**Key Class**: `SemanticMatcher`

**Methods**:
- `_load_model()`: Lazy-loads "all-MiniLM-L6-v2" SentenceTransformer
- `_extract_experience_years()`: Regex-based extraction of years from resume text
  - Patterns: "3 years experience", "experience: 5 years", "5 years in..."
- `_expand_synonyms()`: Expands technical abbreviations
  - Bidirectional mapping: JS↔JavaScript, ML↔Machine Learning, etc.
  - 13 major abbreviations supported
- `_calculate_skill_match_score()`: Multi-factor skill analysis
  - Weighted matching (important skills weighted higher: Python 1.2x, Kubernetes 1.2x, etc.)
  - Matched skills, missing skills, and percentages
  - Total 13 skills with custom weights
- `_generate_candidate_suggestions()`: Creates personalized recommendations based on score
  - Score thresholds: Excellent (≥85%), Good (≥70%), Moderate (≥55%), Poor (≥40%)
  - Learning resource suggestions for missing skills
- `compute_scores()`: Main scoring orchestrator
  - Encodes job description and all resumes using sentence-transformers
  - Calculates cosine similarity for semantic matching
  - Combines scores: 70% semantic + 25% skills + 5% experience experience bonus
  - Generates detailed analysis including strengths and improvements
  - **Output**: Array of scores + detailed results per resume

**Scoring Formula**:
```
final_score = (0.7 × semantic_score) + (0.25 × skill_score) + (0.05 × exp_bonus)
where exp_bonus = min(exp_years × 0.02, 0.1)  # Max 10% bonus
```

#### [database.py](database.py) - Supabase Integration
**Responsibility**: Data persistence and analytics

**Class**: `ResumeDatabase`

**Key Methods**:
- `__init__()`: Initializes Supabase client with credentials from .env
- `is_connected` (property): Validates Supabase connection status
- `save_analysis()`: Persists complete analysis session
  - Creates record in `analyses` table (job title, description, skills, metadata)
  - Creates records in `candidates` table (one per candidate with detailed scores)
  - Updates aggregate statistics in `skill_stats` table
  - **Returns**: Analysis ID
- `_update_skill_stats()`: Aggregates matched/missed skills across candidates
  - Counters for skill presence/absence
  - Fetches existing records and increments counts (upsert pattern)
- `get_skill_gaps()`: Returns top N most commonly missing skills
  - Ordered by miss_count descending
- `get_metrics_summary()`: Dashboard-level statistics
  - Total resumes analyzed
  - Average score across all analyses
  - Total number of analyses
- `get_top_candidates()`: Returns top N candidates from historical data
  - Includes candidate name, score, and associated job title

**Credentials** (in environment):
- `SUPABASE_URL`: Database endpoint
- `SUPABASE_KEY`: Public API key
- Defaults provided (demo/public instance)

#### [utils.py](utils.py) - Text Processing Utilities
**Responsibility**: File parsing and text preprocessing

**Functions**:
- `extract_text_from_pdf()`: Uses PyMuPDF to extract all text from PDF files
  - Handles page-by-page extraction
- `extract_text_from_docx()`: Uses python-docx to extract paragraph text
  - Joins all paragraphs with newlines
- `extract_text_from_file()`: Unified dispatcher based on file extension
  - Supports `.pdf` and `.docx` formats
- `preprocess()`: Normalizes text for AI processing
  - Converts to lowercase
  - Expands abbreviations (ML, AI, NLP) using regex word boundaries
  - Removes special characters (keeps alphanumeric and spaces)
  - Normalizes whitespace
  - **Stop words**: 100+ common English words in memory (not actively used)

#### [requirements.txt](requirements.txt) - Dependencies
```
Flask>=3.0.0              # Web framework
numpy>=1.26.0             # Numerical computing
PyMuPDF>=1.23.5           # PDF text extraction
python-dotenv>=1.0.0      # Environment variable management
sentence-transformers>=3.0.0  # Semantic embeddings
supabase>=2.0.0           # Database client
python-docx>=1.1.0        # DOCX text extraction
pandas>=2.1.1             # Data manipulation & CSV export
```

#### [test_bulk.py](test_bulk.py) - Test Script
**Purpose**: Manual testing of bulk matching endpoint

**Functionality**:
- Loads job description for "Senior Python Backend Engineer"
- Reads all `.docx` files from `sample_resumes/` directory
- Sends multipart form request to `/match_bulk` endpoint
- Prints ranked candidates with scores
- Closes file handles properly

### Configuration & Schema Files

#### [supabase_schema.sql](supabase_schema.sql) - Database Schema
Three main tables:

1. **analyses** (Analysis sessions)
   - `id`: UUID primary key
   - `created_at`: Timestamp
   - `job_title`: Text (required)
   - `analysis_type`: 'single' or 'bulk'
   - `total_resumes`: Count of resumes in batch
   - `avg_score`: Average of candidate scores
   - `job_description`: Full job description text
   - `job_skills`: Array of skill strings

2. **candidates** (Individual candidate results)
   - `id`: UUID primary key
   - `analysis_id`: FK to analyses (cascading delete)
   - `created_at`: Timestamp
   - `name`: Candidate name (required)
   - `score`: Final composite score (0-1)
   - `semantic_score`: Embedding similarity score
   - `skill_score`: Skill matching percentage
   - `experience_years`: Extracted experience duration
   - `matched_skills`: Array of matched skill strings
   - `missing_skills`: Array of missing skill strings
   - `skill_match_percentage`: (matched / total) × 100
   - `suggestions`: Array of personalized suggestions
   - `key_strengths`: Array of identified strengths
   - `areas_for_improvement`: Array of improvement areas

3. **skill_stats** (Aggregate statistics)
   - `skill_name`: Text primary key (unique)
   - `match_count`: Times skill was matched
   - `miss_count`: Times skill was missing
   - `last_updated`: When record was last updated

**Security**: Row Level Security (RLS) enabled with public read-write policies (demo configuration)

#### [.env] - Environment Configuration
Variables:
- `SUPABASE_URL`: Database connection endpoint
- `SUPABASE_KEY`: Public API authentication key

### Frontend Files

#### [templates/index.html](templates/index.html)
**Purpose**: Single-page application shell

**Sections**:
- Navigation bar with mobile toggle
- Home section: Hero content, statistics, CTA buttons
- Single analysis section: Form for job details + resume upload
- Bulk ranking section: Multi-file upload interface
- AI Insights section: Analytics dashboard
- About section: Project information

**Features**:
- Responsive navigation
- Drag-and-drop file upload
- Real-time form validation
- Mobile-friendly UI
- Integration with Font Awesome icons

#### [static/script.js](static/script.js)
**Functionality**:
- Navigation between sections
- File upload handling (drag-drop + input)
- Form submission to Flask endpoints
- Response processing and result display
- CSV export triggering
- Mobile menu toggle

**Key Functions**:
- `navigateTo()`: Section switching
- `setupFileUpload()`: Drag-drop setup
- `handleFiles()`: File processing and listing
- `submitSingleAnalysis()`: POST to `/match_single`
- `submitBulkAnalysis()`: POST to `/match_bulk`
- `displayResults()`: Render analysis results

#### [static/styles.css](static/styles.css)
**Styling**:
- Responsive grid layout (mobile-first)
- Hero section with floating cards
- Form styling with validation states
- Results cards with score visualization
- Analytics dashboard layout
- Mobile navigation drawer
- Dark/light mode ready

---

## 4. Technology Stack and Dependencies

### Backend Framework
- **Flask 3.0+**: Lightweight Python web framework for HTTP routing and request handling

### AI/ML Components
- **Sentence Transformers 3.0+**: Pre-trained "all-MiniLM-L6-v2" model for semantic embeddings
- **scikit-learn**: Cosine similarity computation for embedding comparison
- **NumPy 1.26+**: Numerical arrays and operations

### Data Processing
- **PyMuPDF 1.23.5+**: PDF text extraction
- **python-docx 1.1+**: DOCX file parsing
- **Pandas 2.1.1+**: CSV export and data manipulation

### Database
- **Supabase 2.0+**: PostgreSQL-based backend-as-a-service (BaaS)
  - Tables: analyses, candidates, skill_stats
  - Row-Level Security (RLS) for access control
  - Python client library for connectivity

### Configuration
- **python-dotenv 1.0+**: Environment variable management from `.env` files

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Responsive styling with Flexbox/Grid
- **Vanilla JavaScript**: DOM manipulation, event handling, fetch API calls
- **Font Awesome 6.0**: Icon library (CDN-based)

### Deployment/Development
- **Python 3.8+**: Language runtime
- **pip**: Package manager

---

## 5. Database Schema (Supabase/PostgreSQL)

### Schema Design Pattern
The schema follows a **normalized relational structure** with:
- Parent-child relationship (analyses → candidates)
- Aggregate table for statistics (skill_stats)
- Array columns for flexible skill storage
- Cascading deletes for data integrity

### Detailed Schema

```sql
-- Parent table for analysis sessions
CREATE TABLE public.analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    job_title TEXT NOT NULL,
    analysis_type TEXT NOT NULL,  -- 'single' or 'bulk'
    total_resumes INTEGER DEFAULT 1,
    avg_score FLOAT DEFAULT 0,
    job_description TEXT,
    job_skills TEXT[]  -- Array of skills
);

-- Child table for individual candidate results
CREATE TABLE public.candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES public.analyses(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    name TEXT NOT NULL,
    score FLOAT NOT NULL,  -- Final composite (0-1)
    semantic_score FLOAT,  -- Raw embedding similarity
    skill_score FLOAT,  -- Skill match percentage (0-1)
    experience_years INTEGER,
    matched_skills TEXT[],  -- Array of matched skills
    missing_skills TEXT[],  -- Array of missing skills
    skill_match_percentage FLOAT,  -- (matched/total) * 100
    suggestions TEXT[],  -- Array of recommendation strings
    key_strengths TEXT[],  -- Array of strength descriptions
    areas_for_improvement TEXT[]  -- Array of improvement areas
);

-- Aggregate statistics table
CREATE TABLE public.skill_stats (
    skill_name TEXT PRIMARY KEY,
    match_count INTEGER DEFAULT 0,  -- Global match occurrences
    miss_count INTEGER DEFAULT 0,  -- Global miss occurrences
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Data Flow Through Schema

**Single Resume Analysis**:
```
analyses: 1 record
├─ job_title: "Senior Python Developer"
├─ analysis_type: "single"
├─ total_resumes: 1
└─ avg_score: 0.78

candidates: 1 record
├─ analysis_id: (FK)
├─ name: "John Doe"
├─ score: 0.78
├─ matched_skills: ["Python", "Flask", "PostgreSQL"]
├─ missing_skills: ["Docker", "Kubernetes"]
└─ suggestions: [...]

skill_stats: Updated incrementally
├─ "python": match_count +1
├─ "docker": miss_count +1
└─ "kubernetes": miss_count +1
```

**Bulk Analysis (3 candidates)**:
```
analyses: 1 record (represents entire batch)
├─ job_title: "Senior Python Developer"
├─ analysis_type: "bulk"
├─ total_resumes: 3
└─ avg_score: 0.71  (average of 3 candidates)

candidates: 3 records (one per candidate)
├─ Record 1: John Doe (score: 0.78)
├─ Record 2: Jane Smith (score: 0.72)
└─ Record 3: Bob Johnson (score: 0.63)

skill_stats: Aggregated across all 3
├─ "python": match_count +3
├─ "docker": miss_count +3
└─ ...
```

### Query Patterns Used

**Analytics Queries** (from [database.py](database.py)):
1. Get top missing skills: `SELECT * FROM skill_stats ORDER BY miss_count DESC LIMIT 5`
2. Get metrics summary: `SELECT SUM(total_resumes), AVG(avg_score) FROM analyses`
3. Get top candidates: `SELECT * FROM candidates ORDER BY score DESC LIMIT 5`
4. Get job title for candidate: `SELECT job_title FROM analyses WHERE id = ?`

---

## 6. Data Flow and Key Processes

### Process 1: Single Resume Analysis Endpoint

**Request**:
```json
POST /match_single
Content-Type: multipart/form-data

{
  "job_title": "Senior Python Developer",
  "job_skills": "Python, Flask, PostgreSQL, Docker, Kubernetes",
  "job_description": "We seek an experienced Python backend developer...",
  "resume": <PDF/DOCX file>
}
```

**Processing Steps**:
1. **Validation** (app.py):
   - Check all required fields present
   - Verify file extension is `.pdf` or `.docx`
   - Check file size ≤ 16MB

2. **Text Extraction** (app.py → utils.py):
   - Route based on file type to `extract_text_from_pdf()` or `extract_text_from_docx()`
   - Return raw resume text

3. **Text Preprocessing** (app.py → utils.py):
   - Convert job details to lowercase
   - Preprocess: expand abbreviations, remove special chars, normalize spaces
   - Parse skill list by comma splitting

4. **Semantic Matching** (app.py → model.py):
   - `get_matcher()` returns singleton SemanticMatcher
   - `_load_model()` loads "all-MiniLM-L6-v2" (if not already loaded)
   - `compute_scores()` orchestrates:
     - Encode job + resume via `model.encode()`
     - Calculate cosine similarity
     - Extract experience years via regex
     - Analyze skills with synonyms
     - Compute weighted final score
     - Generate personalized suggestions and strengths

5. **Name Extraction** (app.py):
   - Try regex patterns on resume text for full names
   - Fallback to filename cleaning

6. **Quality Classification** (app.py):
   - Map score to percentage (0-100)
   - Classify: "Excellent Match" (≥85), "Good Match" (≥70), etc.

7. **Database Persistence** (app.py → database.py):
   - Call `db.save_analysis()` with results
   - Create analyses record
   - Create candidates record
   - Update skill_stats

8. **Response Generation** (app.py):
   - Bundle all metrics into JSON response
   - Include candidate name, scores, skills, suggestions, strengths

**Response**:
```json
{
  "candidate_name": "John Doe",
  "score": 78.5,
  "match_quality": "Good Match",
  "semantic_score": 76.3,
  "skill_score": 82.1,
  "experience_years": 5,
  "matched_skills": ["Python", "Flask", "PostgreSQL"],
  "missing_skills": ["Docker", "Kubernetes"],
  "skill_match_percentage": 60.0,
  "suggestions": [
    "🟢 Good match: Providing more specific examples...",
    "📚 Priority skills to learn: Docker, Kubernetes",
    "🎓 Resource for Docker: Docker University"
  ],
  "analysis_time": 3.2,
  "key_strengths": ["Strong semantic alignment", "Excellent match for technical stack"],
  "areas_for_improvement": ["Missing several core technical requirements"]
}
```

---

### Process 2: Bulk Resume Ranking Endpoint

**Request**:
```json
POST /match_bulk
Content-Type: multipart/form-data

{
  "job_title": "Senior Python Developer",
  "job_skills": "Python, Flask, PostgreSQL",
  "job_description": "...",
  "resumes": [<file1.pdf>, <file2.docx>, <file3.pdf>]
}
```

**Processing Steps**:

1. **Initialize** (app.py):
   - Record start time for performance tracking
   - Validate all fields present
   - Preprocess job details

2. **Batch File Processing** (app.py):
   - Iterate through uploaded files
   - Skip files without `.pdf`/`.docx` extension
   - For each valid file:
     - Extract text via utils
     - Preprocess text
     - Keep raw text for name extraction
     - Accumulate in lists: raw_texts, clean_texts, filenames

3. **Batch Scoring** (app.py → model.py):
   - Call `get_matcher().compute_scores(job_text, clean_texts, job_skill_list)`
   - Scores and detailed_results computed in parallel via NumPy
   - Returns: scores array, detailed_results list

4. **Results Aggregation** (app.py):
   - Create ranked_candidates list
   - For each candidate:
     - Extract name from raw text + filename
     - Convert score to percentage
     - Determine match quality
     - Assemble candidate object
   - Sort descending by score
   - Assign rank numbers (1, 2, 3, ...)

5. **Summary Calculation** (app.py):
   - Total candidates count
   - Average score
   - Highest score
   - Top performer name
   - Total analysis time

6. **Database Persistence** (app.py → database.py):
   - Save to Supabase with analysis_type='bulk'
   - Creates 1 analyses record + N candidates records
   - Updates skill_stats with all matched/missing skills

7. **In-Memory Caching** (app.py):
   - Store ranked_candidates in global `last_bulk_results` for CSV export

8. **Response Generation** (app.py):
   - Return summary object
   - Return ranked_candidates array (sorted by rank)

**Response**:
```json
{
  "summary": {
    "total_candidates": 3,
    "average_score": 71.2,
    "highest_score": 78.5,
    "analysis_time": 5.1,
    "top_performer": "John Doe"
  },
  "ranked_candidates": [
    {
      "rank": 1,
      "candidate_name": "John Doe",
      "filename": "john_doe.pdf",
      "score": 78.5,
      "match_quality": "Good Match",
      "semantic_score": 76.3,
      "skill_score": 82.1,
      "experience_years": 5,
      "matched_skills": ["Python", "Flask", "PostgreSQL"],
      "missing_skills": ["Docker", "Kubernetes"],
      "skill_match_percentage": 60.0
    },
    {
      "rank": 2,
      "candidate_name": "Jane Smith",
      "filename": "jane_smith.docx",
      "score": 72.3,
      ...
    },
    {
      "rank": 3,
      "candidate_name": "Bob Johnson",
      "filename": "bob_johnson.pdf",
      "score": 63.1,
      ...
    }
  ]
}
```

---

### Process 3: Analytics & Insights

**Endpoint**: `GET /insights/skill_gaps`

**Flow**:
1. Call `db.get_skill_gaps(5)` → queries skill_stats ordered by miss_count DESC
2. Calculate percentage distribution
3. Return formatted list with recommendations

**Example Response**:
```json
{
  "skill_gaps": [
    {"skill": "Docker", "percentage": 35, "count": 21},
    {"skill": "Kubernetes", "percentage": 28, "count": 17},
    {"skill": "Aws", "percentage": 22, "count": 13},
    {"skill": "Node", "percentage": 10, "count": 6},
    {"skill": "React", "percentage": 5, "count": 3}
  ],
  "recommendation": "Candidates are most commonly missing these skills. Consider training programs or relaxed requirements for these areas."
}
```

**Endpoint**: `GET /insights/metrics`

Aggregates:
- Total resumes analyzed (sum across all analyses)
- Average score (average of avg_score from all analyses)
- Total analyses count
- Estimated successful hires (analyses × 0.1)

---

### Process 4: CSV Export

**Endpoint**: `GET /export_csv`

**Flow**:
1. Check if `last_bulk_results` is populated (from recent bulk analysis)
2. Convert to Pandas DataFrame
3. Select columns: rank, candidate_name, score, match_quality, experience_years, skill_match_percentage, matched_skills, missing_skills
4. Export to CSV in-memory
5. Return with Content-Disposition header for file download

---

## 7. Key Algorithms & Scoring Logic

### 7.1 Semantic Similarity (70% weight)
- **Model**: SentenceTransformer("all-MiniLM-L6-v2") - 384-dimensional embeddings
- **Method**: Cosine similarity between job encoding and resume encoding
- **Range**: 0.0 to 1.0 (1.0 = perfect match)
- Uses pre-trained model on large corpus of sentence pairs
- Fast inference (~1-2ms per embedding)

### 7.2 Skill Matching (25% weight)
**Algorithm**:
```python
expanded_resume_words = expand_synonyms(resume.split())
weighted_matched = 0
total_weight = 0

for skill in job_skills:
    weight = skill_weights.get(skill.lower(), 1.0)
    total_weight += weight
    if skill.lower() in expanded_resume_words:
        weighted_matched += weight

skill_score = weighted_matched / total_weight
```

**Skill Weights** (13 recognized skills):
- High (1.2-1.3): Python, Kubernetes, Machine Learning, Artificial Intelligence, Data Science
- Medium (1.1): JavaScript, Java, AWS, Docker, DevOps
- Base (1.0): React, Node, SQL

**Synonym Expansion** (Bidirectional):
- JS ↔ JavaScript, TS ↔ TypeScript, PY ↔ Python
- K8s ↔ Kubernetes, ML ↔ Machine Learning, AI ↔ Artificial Intelligence
- NLP ↔ Natural Language Processing, etc.

### 7.3 Experience Bonus (5% weight)
**Extraction Patterns** (regex):
1. "3+ years of experience"
2. "experience: 5 years"
3. "5 years in..."

**Calculation**:
```python
exp_years = extracted from resume
exp_bonus = min(exp_years × 0.02, 0.1)  # Max 10% bonus at 5+ years
```

### 7.4 Final Score Calculation
```
final_score = (0.7 × semantic_score) + (0.25 × skill_score) + (0.05 × exp_bonus)
final_score = clamp(final_score, 0, 1)
percentage = final_score × 100  # 0-100 scale
```

### 7.5 Match Quality Classification
- **Excellent Match**: ≥ 85%
- **Good Match**: 70-84%
- **Moderate Match**: 55-69%
- **Poor Match**: 40-54%
- **Very Poor Match**: < 40%

---

## 8. Integration Points

### External Service: Supabase
- **Authentication**: Public key via environment variables
- **Tables**: Direct SQL operations via Python client
- **Queries**: SELECT, INSERT, UPDATE operations
- **Error Handling**: Try-catch blocks with fallback behavior (graceful degradation)
- **Status Check**: `is_connected` property validates client availability

### Text Processing Pipeline
- **PDF**: PyMuPDF streams → page extraction → text concatenation
- **DOCX**: python-docx → paragraph iteration → newline joining
- **Error Handling**: Skips corrupted files in bulk operations

### ML Model Integration
- **Lazy Loading**: Model only loaded on first request (singleton pattern)
- **Framework**: sentence-transformers (wrapper around HuggingFace Transformers)
- **Model**: all-MiniLM-L6-v2 (lightweight, 384-dim embeddings)
- **Hardware**: CPU-based (no GPU required)
- **Memory**: ~150MB model size

---

## 9. Error Handling & Resilience

### Frontend Validation
- File type checking (PDF/DOCX only)
- File size limit (16MB)
- Required field validation

### Backend Graceful Degradation
1. **Supabase Connection Failure**: Analytics fail silently, matching still works
2. **Corrupted PDF/DOCX**: Skipped in bulk operations, error reported for single
3. **Empty Uploads**: Returns "No valid resumes found" error
4. **Model Loading Failure**: Caught and reported
5. **Regex Extraction**: Defaults to "Candidate" if name extraction fails

### Status Indicators
- `db.is_connected` property checks Supabase availability
- Analytics endpoints return empty data if database unavailable
- Single/bulk endpoints continue functioning without database

---

## 10. Performance Characteristics

### Single Analysis
- **Time**: ~3-5 seconds (observed in responses)
- **Bottleneck**: Model inference + text extraction
- **Scaling**: Linear per resume

### Bulk Analysis (N resumes)
- **Time**: ~5-10 seconds for 3-5 candidates
- **Parallelization**: NumPy cosine_similarity processes all embeddings in parallel
- **Bottleneck**: Model inference for all candidates (~1-2ms each)

### Database Operations
- **Insert**: <100ms per analysis (network latency)
- **Query**: <50ms per query (aggregations)
- **Scaling**: Linear with result size

### Model Memory
- **Sentence Transformer**: ~150MB
- **Loaded Once**: Lazy-loaded on first request
- **Singleton Pattern**: Reused across requests

---

## 11. Deployment & Configuration

### Environment Setup
```bash
# .env file requirements
SUPABASE_URL=https://phvlfdbpwgjjdvjnqtkf.supabase.co
SUPABASE_KEY=sb_publishable_...
```

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask app
python app.py

# Access at http://localhost:5000
```

### Docker Deployment (Not Included, but possible)
Would need: Dockerfile + requirements.txt + .env management

### Development Features
- Debug mode enabled in app.py
- Use_reloader disabled (to prevent model reloading)
- Verbose error traceback in responses

---

## 12. Security Considerations

### Current State (Demo)
- ⚠️ Supabase credentials in code + environment
- ⚠️ Public RLS policies (anyone can read/write)
- ⚠️ No authentication on endpoints
- ⚠️ No CORS configuration
- ✅ File size limit (16MB)
- ✅ File type validation

### Production Recommendations
1. Move credentials to secrets management (AWS Secrets Manager, etc.)
2. Implement authentication/authorization layer
3. Restrict RLS policies (authenticated users only)
4. Add CORS configuration
5. Rate limiting on API endpoints
6. Input sanitization for SQL injection prevention
7. Support for HTTPS/TLS
8. Logging and monitoring

---

## 13. Future Enhancements

### Possible Additions
1. **Authentication**: User accounts and session management
2. **Saved Analyses**: History and rerun capabilities
3. **Custom Models**: Upload organization-specific models
4. **API Integration**: LinkedIn, Indeed integration for resume imports
5. **Customizable Weights**: Allow organizations to adjust scoring weights
6. **Real-time Notifications**: Email alerts for new candidates
7. **Team Collaboration**: Share analyses with team members
8. **Advanced Filtering**: Filter by experience level, location, etc.
9. **Recommendation System**: Suggest improvements to job postings
10. **Mobile App**: Native mobile application

---

## Summary

The **Resume Match System** is a well-architected AI-powered recruiter tool that:
- Uses state-of-the-art semantic embeddings for intelligent matching
- Combines multiple scoring factors (semantic, skills, experience)
- Provides detailed insights and personalized recommendations
- Scales from single analysis to bulk ranking
- Persists data for analytics and trend analysis
- Delivers results in 3-10 seconds
- Maintains simple, maintainable architecture with clear separation of concerns

The system is suitable for MVP/demonstration purposes and can be extended with authentication, multi-tenancy, and advanced analytics for production deployment.
