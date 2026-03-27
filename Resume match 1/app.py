import os
import time
import re
from flask import Flask, request, jsonify, render_template, Response
from utils import extract_text_from_file, preprocess
from model import SemanticMatcher
from database import ResumeDatabase
from dotenv import load_dotenv
import pandas as pd
import io

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Limit upload size to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

matcher = None
db = ResumeDatabase()

# Global for simple CSV export of last bulk run (temp storage)
last_bulk_results = []

def get_matcher():
    global matcher
    if matcher is None:
        matcher = SemanticMatcher()
    return matcher

def extract_candidate_name(resume_text, filename):
    """Extract candidate name from resume text or filename"""
    # Try to extract name from common patterns in resume text
    name_patterns = [
        r'(?:name|full name)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
    ]

    for pattern in name_patterns:
        match = re.search(pattern, resume_text, re.MULTILINE)
        if match:
            name = match.group(1).strip()
            if len(name.split()) >= 2:  # Ensure it's a full name
                return name.title()

    # Fallback to filename (remove extension and clean up)
    name_from_file = re.sub(r'\.(pdf|docx)$', '', filename, flags=re.I)
    name_from_file = name_from_file.replace('_', ' ').replace('-', ' ').strip()
    
    if name_from_file:
        return name_from_file.title()

    return "Candidate"

def get_match_quality(score):
    """Determine match quality based on score"""
    if score >= 85: return "Excellent Match"
    elif score >= 70: return "Good Match"
    elif score >= 55: return "Moderate Match"
    elif score >= 40: return "Poor Match"
    else: return "Very Poor Match"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/match_single", methods=["POST"])
def match_single():
    try:
        start_time = time.time()

        # Input validation
        job_title = request.form.get("job_title", "").strip()
        job_skills = request.form.get("job_skills", "").strip()
        job_desc = request.form.get("job_description", "").strip()
        resume_file = request.files.get("resume")

        if not all([job_title, job_skills, job_desc, resume_file]):
            return jsonify({"error": "Missing required fields or file", "status": "error"}), 400

        if not resume_file.filename.lower().endswith(('.pdf', '.docx')):
            return jsonify({"error": "Unsupported file format. Use PDF or DOCX.", "status": "error"}), 400

        # Process job requirements
        job_text = preprocess(job_title + " " + job_desc)
        job_skill_list = [s.strip() for s in job_skills.split(",") if s.strip()]

        # Process resume
        resume_raw_text = extract_text_from_file(resume_file)
        if not resume_raw_text.strip():
            return jsonify({"error": "Could not extract text from the file.", "status": "error"}), 400
            
        clean_resume = preprocess(resume_raw_text)

        # Get matching results
        _, detailed_results = get_matcher().compute_scores(job_text, [clean_resume], job_skill_list)
        result = detailed_results[0]

        score_percentage = round(float(result['score']) * 100, 2)
        candidate_name = extract_candidate_name(resume_raw_text, resume_file.filename)
        match_quality = get_match_quality(score_percentage)
        analysis_time = round(time.time() - start_time, 2)

        # Prepare final response object
        response_data = {
            "candidate_name": candidate_name,
            "score": score_percentage,
            "match_quality": match_quality,
            "semantic_score": round(result['semantic_score'] * 100, 2),
            "skill_score": round(result['skill_score'] * 100, 2),
            "experience_years": result['experience_years'],
            "matched_skills": result['matched_skills'],
            "missing_skills": result['missing_skills'],
            "skill_match_percentage": round(result['skill_match_percentage'] * 100, 2),
            "suggestions": result.get('suggestions', []),
            "analysis_time": analysis_time,
            "key_strengths": result.get('key_strengths', []),
            "areas_for_improvement": result.get('areas_for_improvement', [])
        }

        # Save to DB
        db.save_analysis(job_title, 'single', job_desc, job_skill_list, [response_data])

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in match_single: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/match_bulk", methods=["POST"])
def match_bulk():
    global last_bulk_results
    try:
        start_time = time.time()

        job_title = request.form.get("job_title", "").strip()
        job_skills = request.form.get("job_skills", "").strip()
        job_desc = request.form.get("job_description", "").strip()
        files = request.files.getlist("resumes")

        if not all([job_title, job_skills, job_desc, files]):
             return jsonify({"error": "Missing required fields", "status": "error"}), 400

        job_text = preprocess(job_title + " " + job_desc)
        job_skill_list = [s.strip() for s in job_skills.split(",") if s.strip()]

        raw_texts = []
        clean_texts = []
        filenames = []

        for file in files:
            if not file.filename.lower().endswith(('.pdf', '.docx')):
                continue
            
            try:
                raw_txt = extract_text_from_file(file)
                if raw_txt.strip():
                    raw_texts.append(raw_txt)
                    clean_texts.append(preprocess(raw_txt))
                    filenames.append(file.filename)
            except Exception as e:
                print(f"Skiping {file.filename}: {e}")

        if not clean_texts:
            return jsonify({"error": "No valid resumes found in upload.", "status": "error"}), 400

        # Compute
        scores, detailed_results = get_matcher().compute_scores(job_text, clean_texts, job_skill_list)

        ranked_candidates = []
        for i, (name, score, details) in enumerate(zip(filenames, scores, detailed_results)):
            score_pct = round(float(score) * 100, 2)
            c_name = extract_candidate_name(raw_texts[i], name)
            
            ranked_candidates.append({
                "candidate_name": c_name,
                "filename": name,
                "score": score_pct,
                "match_quality": get_match_quality(score_pct),
                "semantic_score": round(details['semantic_score'] * 100, 2),
                "skill_score": round(details['skill_score'] * 100, 2),
                "experience_years": details['experience_years'],
                "matched_skills": details['matched_skills'],
                "missing_skills": details['missing_skills'],
                "skill_match_percentage": round(details['skill_match_percentage'] * 100, 2)
            })

        ranked_candidates.sort(key=lambda x: x['score'], reverse=True)
        for i, c in enumerate(ranked_candidates, 1): c['rank'] = i

        analysis_time = round(time.time() - start_time, 2)
        summary = {
            "total_candidates": len(ranked_candidates),
            "average_score": round(sum(c['score'] for c in ranked_candidates) / len(ranked_candidates), 2),
            "highest_score": ranked_candidates[0]['score'],
            "analysis_time": analysis_time,
            "top_performer": ranked_candidates[0]['candidate_name']
        }

        # Save to DB
        db.save_analysis(job_title, 'bulk', job_desc, job_skill_list, ranked_candidates)
        
        # Save to global for export
        last_bulk_results = ranked_candidates

        return jsonify({"summary": summary, "ranked_candidates": ranked_candidates})

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in match_bulk: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/export_csv", methods=["GET"])
def export_csv():
    if not last_bulk_results:
        return jsonify({"error": "No bulk results found to export."}), 404
        
    df = pd.DataFrame(last_bulk_results)
    # Reorder columns
    cols = ['rank', 'candidate_name', 'score', 'match_quality', 'experience_years', 'skill_match_percentage', 'matched_skills', 'missing_skills']
    df = df[cols]
    
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=resume_ranking.csv"}
    )

@app.route("/insights/skill_gaps", methods=["GET"])
def get_skill_gaps():
    gaps = db.get_skill_gaps(5)
    if not gaps:
        return jsonify({"skill_gaps": [], "recommendation": "No data available yet. Run some analyses to see insights."})

    total_misses = sum(g['miss_count'] for g in gaps)
    formatted = []
    for g in gaps:
        percentage = int((g['miss_count'] / total_misses) * 100) if total_misses > 0 else 0
        formatted.append({
            "skill": g['skill_name'].title(),
            "percentage": percentage,
            "count": g['miss_count']
        })

    return jsonify({
        "skill_gaps": formatted,
        "recommendation": "Candidates are most commonly missing these skills. Consider training programs or relaxed requirements for these areas."
    })

@app.route("/insights/metrics", methods=["GET"])
def get_metrics():
    metrics = db.get_metrics_summary()
    if not metrics:
        return jsonify({"total_resumes": 0, "average_score": 0, "avg_analysis_time": 0, "total_analyses": 0, "successful_hires": 0})
    
    # Simple estimation for demo
    metrics['successful_hires'] = int(metrics['total_analyses'] * 0.1)
    metrics['avg_analysis_time'] = 5.2 # Mock average
    
    return jsonify(metrics)

@app.route("/insights/top_candidates", methods=["GET"])
def get_top_candidates():
    top = db.get_top_candidates(5)
    return jsonify(top)

@app.route("/insights/hiring_tips", methods=["GET"])
def get_hiring_tips():
    # Dynamic tips can be added here
    tips = [
        {"icon": "search", "title": "Precision Keywords", "content": "Use industry-standard tech terms to improve AI matching accuracy."},
        {"icon": "clock", "title": "Batch Processing", "content": "Use bulk ranking to save up to 80% of screening time."},
        {"icon": "lightbulb", "title": "Skill Synonyms", "content": "Our AI understands that 'JS' is 'JavaScript' and 'K8s' is 'Kubernetes'."}
    ]
    return jsonify(tips)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)