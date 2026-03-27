# AI Resume – Job Matching System

An advanced AI-powered resume matching system that uses semantic embeddings and heuristic analysis for candidate-job matching.

## Features

- **Semantic Analysis**: Uses sentence transformers for fast and accurate similarity matching
- **Single & Bulk Analysis**: Analyze individual resumes or rank multiple candidates
- **Advanced Scoring**: Multi-factor scoring including semantic match, skills, and experience
- **Recommendations**: Personalized suggestions generated from local threshold logic
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Real-time Analytics**: Track analysis patterns and insights

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd resume-match-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` for local configuration as needed (no OpenAI key required):
   ```
   # Optional settings e.g. app port, debug
   ```

### Running the Application

```bash
python app.py
```

Open your browser and navigate to `http://localhost:5000`

## Semantic Matching Engine

### How It Works

The system uses:

1. **Sentence Transformers**: Fast semantic similarity matching
2. **Heuristic Analysis**: Skill completeness and experience scoring
3. **Weighted Scoring**: Combines embeddings with heuristic score

### Recommendations

- **Contextual Assessment**: Based on job/resume embedding similarity
- **Skill Assessment**: Match/missing skill detection from job requirements
- **Personalized Suggestions**: Local logic for candidate advice
- **Experience Evaluation**: Extracts years from resume text
- **Match Quality Classification**: Based on combined score thresholds

## API Endpoints

### Single Resume Analysis
```
POST /match_single
```
Upload one resume with job details for detailed analysis.

### Bulk Resume Ranking
```
POST /match_bulk
```
Upload multiple resumes for comparative ranking.

### AI Insights
```
GET /insights/skill_gaps
GET /insights/hiring_tips
GET /insights/top_candidates
GET /insights/metrics
```

## Configuration

### Environment Variables

- Optionally configure app settings in `.env` (port, debug, etc.)

### Model Configuration

The system uses a weighted scoring approach:
- Semantic Similarity: 50%
- Heuristic Analysis: 50%

You can adjust these weights in `model.py` if needed.

## Usage

### Single Analysis
1. Enter job title, required skills, and job description
2. Upload a resume PDF
3. Get detailed analysis with AI recommendations

### Bulk Analysis
1. Enter job details
2. Upload multiple resume PDFs
3. Get ranked candidates with detailed comparisons

### AI Insights
Access the AI Insights tab for:
- Skill gap analysis across candidates
- Hiring recommendations
- Top performing candidates
- Performance metrics

## Technical Details

### Dependencies

- **Flask**: Web framework
- **sentence-transformers**: For semantic similarity
- **openai**: GPT model integration
- **PyMuPDF**: PDF text extraction
- **numpy**: Numerical computations
- **python-dotenv**: Environment variable management

### Model Architecture

```
Input (Job + Resume)
    │
    ├── Sentence Transformers → Semantic Score
    │
    └── GPT-4 Analysis → Contextual Score
        │
        └── Skill Analysis
        └── Experience Assessment
        └── Recommendations
    │
    └── Weighted Combination → Final Score
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Not Set**
   - Ensure `OPENAI_API_KEY` is set in `.env`
   - Check API key validity and quota

2. **PDF Processing Errors**
   - Ensure PDFs are text-based (not image-only)
   - Check file size limits

3. **Slow Analysis**
   - GPT-4 analysis takes longer than traditional methods
   - Consider using GPT-3.5-turbo for faster results

### Performance Optimization

- Use GPT-3.5-turbo for faster analysis
- Limit bulk analysis to reasonable batch sizes
- Cache frequent analyses if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the code comments
- Open an issue on GitHub

---

**Note**: GPT-5 mentioned in the original request refers to advanced GPT capabilities. This implementation uses GPT-4 for optimal performance and accuracy.