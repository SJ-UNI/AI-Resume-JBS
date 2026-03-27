import numpy as np
from collections import Counter
import re


class SemanticMatcher:

    def __init__(self):
        self.model = None

    def _load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer, util
            # Lightweight + high accuracy model
            self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def _extract_experience_years(self, text):
        """Extract years of experience from resume text"""
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience[:\s]+(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s+in\s+',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 0

    def _expand_synonyms(self, words_set):
        """Expand set of words with common technical synonyms"""
        synonyms = {
            'js': 'javascript',
            'ts': 'typescript',
            'aws': 'amazon web services',
            'k8s': 'kubernetes',
            'py': 'python',
            'reactjs': 'react',
            'nodejs': 'node',
            'postgres': 'postgresql',
            'sql server': 'mssql',
            'ai': 'artificial intelligence',
            'ml': 'machine learning',
            'nlp': 'natural language processing'
        }
        expanded = words_set.copy()
        for word in words_set:
            if word in synonyms:
                expanded.add(synonyms[word])
            # Reverse check
            for short, full in synonyms.items():
                if word == full:
                    expanded.add(short)
        return expanded

    def _calculate_skill_match_score(self, resume_text, job_skills):
        """Calculate detailed skill matching score with synonym support"""
        resume_words = set(resume_text.lower().split())
        # Expand resume words with synonyms for better matching
        expanded_resume_words = self._expand_synonyms(resume_words)
        
        job_skill_set = set(skill.lower() for skill in job_skills)

        matched_skills = []
        missing_skills = []

        # Calculate weighted score based on skill importance
        skill_weights = {
            'python': 1.2, 'javascript': 1.1, 'java': 1.1, 'react': 1.0, 'node': 1.0,
            'sql': 1.0, 'aws': 1.1, 'docker': 1.1, 'kubernetes': 1.2, 'machine learning': 1.3,
            'artificial intelligence': 1.3, 'data science': 1.2, 'devops': 1.1
        }

        weighted_matched = 0
        total_weight = 0

        for skill in job_skills:
            skill_lower = skill.lower()
            weight = skill_weights.get(skill_lower, 1.0)
            total_weight += weight
            
            # Check if skill or its synonyms exist in resume
            if skill_lower in expanded_resume_words:
                weighted_matched += weight
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        skill_score = weighted_matched / total_weight if total_weight > 0 else 0

        return {
            'matched': matched_skills,
            'missing': missing_skills,
            'skill_score': skill_score,
            'match_percentage': len(matched_skills) / len(job_skills) if job_skills else 0
        }

    def _generate_candidate_suggestions(self, score_pct, skill_analysis, job_title, exp_years):
        """Generate personalized suggestions for the candidate"""
        suggestions = []

        if score_pct < 50:
            suggestions.append("🔴 Critical: Your profile needs significant alignment with this role's core requirements.")
            if exp_years < 2:
                suggestions.append("Consider gaining 1-2 years of targeted project experience before applying for similar roles.")
        elif score_pct < 65:
            suggestions.append("🟡 Moderate match: Focus on bridging the identified skill gaps and highlighting relevant projects.")
        elif score_pct < 80:
            suggestions.append("🟢 Good match: Providing more specific examples of your work with key technologies could make you a top candidate.")
        else:
            suggestions.append("🟢 Excellent match: You are highly qualified! Ensure your cover letter highlights your most relevant achievements.")

        # Skill-specific suggestions
        missing = skill_analysis['missing']
        if missing:
            top_missing = missing[:3]
            suggestions.append(f"📚 Priority skills to learn: {', '.join(top_missing)}")

            learning_map = {
                'python': 'Official Python Docs or freeCodeCamp',
                'javascript': 'MDN Web Docs or JavaScript.info',
                'react': 'React.dev documentation',
                'aws': 'AWS Training and Certification',
                'docker': 'Docker University',
                'kubernetes': 'KubeAcademy by VMware'
            }

            for skill in top_missing:
                s_lower = skill.lower()
                if s_lower in learning_map:
                    suggestions.append(f"🎓 Resource for {skill}: {learning_map[s_lower]}")

        return suggestions

    def compute_scores(self, job_text, resumes, job_skills):
        """Enhanced scoring with detailed analysis and AI insights"""
        self._load_model()

        from sklearn.metrics.pairwise import cosine_similarity

        # Try mapping to numpy instead of tensors to avoid PyTorch prims::full_like error
        job_embedding = self.model.encode(job_text)
        resume_embeddings = self.model.encode(resumes)

        if len(resume_embeddings) == 0:
            semantic_scores = []
        else:
            semantic_scores = cosine_similarity([job_embedding], resume_embeddings)[0]

        final_scores = []
        detailed_results = []

        for i, semantic_score in enumerate(semantic_scores):
            base_score = float(semantic_score)

            # Enhanced skill analysis
            skill_analysis = self._calculate_skill_match_score(resumes[i], job_skills)

            # Experience factor
            exp_years = self._extract_experience_years(resumes[i])
            exp_bonus = min(exp_years * 0.02, 0.1)  # Max 10% bonus

            # Final weighted score
            final_score = (0.7 * base_score) + (0.25 * skill_analysis['skill_score']) + (0.05 * exp_bonus)
            final_score = max(0, min(final_score, 1))
            score_percentage = round(final_score * 100, 2)

            # Generate Insights
            suggestions = self._generate_candidate_suggestions(score_percentage, skill_analysis, "Job", exp_years)
            
            # Simple heuristic for strengths/improvements
            strengths = []
            improvements = []
            
            if base_score > 0.7: strengths.append("Strong semantic alignment with job description")
            if skill_analysis['skill_score'] > 0.8: strengths.append(f"Excellent match for technical stack ({len(skill_analysis['matched'])} skills)")
            if exp_years >= 3: strengths.append(f"Substantial professional experience ({exp_years} years)")
            
            if skill_analysis['skill_score'] < 0.5: improvements.append("Missing several core technical requirements")
            if exp_years < 1: improvements.append("Limited professional experience mentioned")
            if base_score < 0.5: improvements.append("Resume content doesn't strongly reflect job context")

            final_scores.append(final_score)
            detailed_results.append({
                'score': final_score,
                'semantic_score': base_score,
                'skill_score': skill_analysis['skill_score'],
                'experience_years': exp_years,
                'matched_skills': skill_analysis['matched'],
                'missing_skills': skill_analysis['missing'],
                'skill_match_percentage': skill_analysis['match_percentage'],
                'suggestions': suggestions,
                'key_strengths': strengths,
                'areas_for_improvement': improvements
            })

        return np.array(final_scores), detailed_results