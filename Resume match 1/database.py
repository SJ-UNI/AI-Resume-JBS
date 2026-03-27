import os
from supabase import create_client, Client
from dotenv import load_dotenv
from collections import Counter
import uuid

# Load environment variables
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")  # Use SECRET key, not publishable!

class ResumeDatabase:
    """Supabase interface for Resume Match data storage."""
    
    def __init__(self):
        self._client = None
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("⚠️  WARNING: Supabase credentials not found in .env file!")
            print("   Database operations are DISABLED.")
            print("   To enable: set SUPABASE_URL and SUPABASE_KEY in .env")
            return
        
        try:
            self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print(f"✓ Supabase connected to {SUPABASE_URL}")
        except Exception as e:
            print(f"❌ Supabase connection FAILED: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if Supabase client is valid."""
        return self._client is not None

    def save_analysis(self, job_title: str, analysis_type: str, job_desc: str, job_skills: list, results: list) -> str:
        """Save a complete analysis session + its candidates to Supabase."""
        if not self.is_connected:
            print("⚠️  Database DISABLED - Analysis NOT saved to database")
            return ""

        try:
            # 1. Insert analysis record
            avg_score = sum(r['score'] for r in results) / len(results) if results else 0
            
            # Using Supabase's Python wrapper
            analysis_data = {
                "job_title": job_title,
                "analysis_type": analysis_type,
                "total_resumes": len(results),
                "avg_score": avg_score,
                "job_description": job_desc,
                "job_skills": job_skills
            }
            
            resp = self._client.table("analyses").insert(analysis_data).execute()
            analysis_id = resp.data[0]['id']
            print(f"✓ Analysis saved: {analysis_id}")

            # 2. Insert candidates
            candidate_records = []
            for r in results:
                candidate_records.append({
                    "analysis_id": analysis_id,
                    "name": r.get('candidate_name', 'Candidate'),
                    "score": r['score'],
                    "semantic_score": r.get('semantic_score'),
                    "skill_score": r.get('skill_score'),
                    "experience_years": r.get('experience_years', 0),
                    "matched_skills": r.get('matched_skills', []),
                    "missing_skills": r.get('missing_skills', []),
                    "skill_match_percentage": r.get('skill_match_percentage', 0),
                    "suggestions": r.get('suggestions', []),
                    "key_strengths": r.get('key_strengths', []),
                    "areas_for_improvement": r.get('areas_for_improvement', [])
                })

            if candidate_records:
                self._client.table("candidates").insert(candidate_records).execute()
                print(f"✓ Saved {len(candidate_records)} candidate(s)")
            
            # 3. Aggregated skills (async updates often best, here we just do simple upserts)
            # This is a bit heavy for transactional code, but good for demo
            self._update_skill_stats(results)

            return analysis_id
        except Exception as e:
            print(f"❌ Database save FAILED: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def _update_skill_stats(self, results: list):
        """Update the aggregate statistics of matched/missed skills."""
        if not self.is_connected: return
        
        matches = Counter()
        misses = Counter()
        
        for r in results:
            for s in r.get('matched_skills', []): matches[s.lower()] += 1
            for s in r.get('missing_skills', []): misses[s.lower()] += 1

        # Combine all unique skills found
        all_skills = set(matches.keys()) | set(misses.keys())
        
        # Batching upserts might be needed for scale, keep it simple for now
        for skill in all_skills:
            try:
                # Skill names are unique keys in table definition
                # We'll use upsert which handles 'on conflict'
                data = {
                    "skill_name": skill,
                    "match_count": matches[skill],
                    "miss_count": misses[skill]
                }
                # supabase-py doesn't have a direct 'increment' built-in that's easy to use via upsert
                # Normally you'd use a RPC or specialized query. 
                # For this demo, let's fetch then update.
                current = self._client.table("skill_stats").select("*").eq("skill_name", skill).execute()
                if current.data:
                    old = current.data[0]
                    self._client.table("skill_stats").update({
                        "match_count": old['match_count'] + matches[skill],
                        "miss_count": old['miss_count'] + misses[skill],
                        "last_updated": "now()"
                    }).eq("skill_name", skill).execute()
                else:
                    self._client.table("skill_stats").insert(data).execute()
            except:
                pass

    def get_skill_gaps(self, limit=5):
        """Fetch top commonly missing skills from database."""
        if not self.is_connected: return []
        try:
            # Most common missing skills across ALL analyses
            resp = self._client.table("skill_stats").select("*").order("miss_count", desc=True).limit(limit).execute()
            return resp.data
        except:
            return []

    def get_metrics_summary(self):
        """Fetch high level metrics for dashboard."""
        if not self.is_connected: return None
        try:
            # Aggregate stats from analyses table
            analyses = self._client.table("analyses").select("total_resumes", "avg_score").execute()
            if not analyses.data: return None
            
            total_resumes = sum(a['total_resumes'] for a in analyses.data)
            avg_score = sum(a['avg_score'] for a in analyses.data) / len(analyses.data)
            
            return {
                "total_resumes": total_resumes,
                "average_score": avg_score,
                "total_analyses": len(analyses.data)
            }
        except:
            return None

    def get_top_candidates(self, limit=5):
        """Fetch overall top candidates from historical data."""
        if not self.is_connected: return []
        try:
            resp = self._client.table("candidates").select("name, score, analysis_id").order("score", desc=True).limit(limit).execute()
            # Fetch the associated job titles for roles
            results = []
            for c in resp.data:
                # Simple secondary query for title
                analysis = self._client.table("analyses").select("job_title").eq("id", c['analysis_id']).single().execute()
                role = analysis.data['job_title'] if analysis.data else "Developer"
                results.append({"name": c['name'], "score": c['score'], "role": role})
            return results
        except:
            return []
