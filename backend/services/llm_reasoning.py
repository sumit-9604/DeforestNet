import json
import requests
from backend.config import LLM_PROVIDER, GEMINI_API_KEY, CLAUDE_API_KEY
from backend.utils.logger import setup_logger

logger = setup_logger("llm_reasoning")

class LLMReasoningService:
    def __init__(self):
        self.provider = LLM_PROVIDER
        
    def analyze_alert(self, alert_data: dict) -> dict:
        """
        Runs LLM reasoning on the enriched alert data to classify risk level,
        generate a narrative summary of the event, and advise recommended actions.
        """
        prompt = self._construct_prompt(alert_data)
        
        # Determine provider and key presence
        provider = self.provider
        if provider == "gemini" and not GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured. Falling back to rule-based analysis.")
            provider = "mock"
        elif provider == "claude" and not CLAUDE_API_KEY:
            logger.warning("CLAUDE_API_KEY not configured. Falling back to rule-based analysis.")
            provider = "mock"
            
        if provider == "gemini":
            return self._call_gemini_api(prompt, alert_data)
        elif provider == "claude":
            return self._call_claude_api(prompt, alert_data)
        else:
            return self._run_rule_based_fallback(alert_data)

    def _construct_prompt(self, data: dict) -> str:
        return f"""
You are the reasoning core of DeForestNet, an AI agent monitoring illegal logging and deforestation.
Analyze this deforestation alert and output your assessment strictly as a JSON object.

Alert Data:
- Latitude: {data['latitude']}
- Longitude: {data['longitude']}
- Total Detected Forest Cover Loss Area: {data['area_ha']} hectares
- NDVI Mean Value Before: {data['ndvi_before_mean']:.3f}
- NDVI Mean Value After: {data['ndvi_after_mean']:.3f}
- NDVI Drop: {data['ndvi_diff_mean']:.3f}
- Location is inside Legally Protected Area: {data['is_protected']}
- Protected Area Name: {data['protected_area_name']}
- Protected Area Category: {data['protected_area_category']}
- Active Deforestation Cluster in the past 30 days: {data['is_active_cluster']}
- Number of nearby alerts (1km radius, 30 days): {data['neighboring_alerts_30d']}

Your response must be a JSON object with the following fields:
1. "risk_level": Must be one of "Low", "Medium", "High", "Critical".
2. "narrative_summary": A 2-3 sentence human-readable description summarizing what occurred, the severity, and why it is flagged.
3. "recommended_action": A clear, actionable directive for forest department personnel or NGOs.
4. "reasoning_chain": A brief explanation of your decision (e.g. why the risk is graded critical or low).

Output JSON only, no markdown wrappers, no backticks, no other text.
"""

    def _call_gemini_api(self, prompt: str, data: dict) -> dict:
        """Calls Gemini API using direct REST POST request"""
        logger.info("Calling Google Gemini API for alert analysis...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                result_json = response.json()
                text_content = result_json["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content.strip())
            else:
                logger.error(f"Gemini API error (Status {response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"Failed to query Gemini API: {e}")
            
        # Fallback to rule-based if API call fails
        return self._run_rule_based_fallback(data)

    def _call_claude_api(self, prompt: str, data: dict) -> dict:
        """Calls Anthropic Claude API using direct REST POST request"""
        logger.info("Calling Anthropic Claude API for alert analysis...")
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                result_json = response.json()
                text_content = result_json["content"][0]["text"]
                return json.loads(text_content.strip())
            else:
                logger.error(f"Claude API error (Status {response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"Failed to query Claude API: {e}")
            
        # Fallback to rule-based if API call fails
        return self._run_rule_based_fallback(data)

    def _run_rule_based_fallback(self, data: dict) -> dict:
        """Determines risk level and narrative summary using robust heuristics"""
        logger.info("Executing rule-based fallback analysis...")
        
        is_protected = data.get("is_protected", False)
        is_active_cluster = data.get("is_active_cluster", False)
        area_ha = data.get("area_ha", 0.0)
        pa_name = data.get("protected_area_name", "a protected reserve")
        neighbors = data.get("neighboring_alerts_30d", 0)
        ndvi_drop = data.get("ndvi_diff_mean", 0.0)
        
        # Risk evaluation heuristics
        if is_protected and is_active_cluster:
            risk_level = "Critical"
            narrative = (
                f"CRITICAL ALERT: Deforestation of {area_ha} hectares detected inside {pa_name}. "
                f"This location is part of an active deforestation cluster with {neighbors} other alerts "
                f"detected within 1km over the last 30 days, suggesting organized, expanding logging roads."
            )
            action = (
                "Dispatch an enforcement patrol immediately. Secure coordinates, initiate ground checks, "
                "and deploy aerial drones to locate active logging crews or machinery."
            )
            reasoning = "Overlaps with legally protected area and shows active expanding logging pattern (multiple nearby alerts)."
            
        elif is_protected:
            risk_level = "High"
            narrative = (
                f"HIGH ALERT: Forest loss of {area_ha} hectares confirmed inside {pa_name} (NDVI drop of {ndvi_drop:.2f}). "
                f"No other alerts have been logged in the immediate vicinity recently, indicating a potentially isolated clearing."
            )
            action = (
                f"Notify the local range officers for {pa_name}. Schedule a field inspection to verify "
                "if this is an unpermitted clearing or natural tree fall (windthrow/landslide)."
            )
            reasoning = "Located inside protected boundary, but lacks active cluster pattern."
            
        elif is_active_cluster:
            risk_level = "Medium"
            narrative = (
                f"MEDIUM ALERT: Deforestation of {area_ha} hectares confirmed outside protected boundaries. "
                f"However, this is part of an active cluster with {neighbors} nearby alerts in the past month, "
                f"indicating potential unpermitted agricultural or logging encroachment."
            )
            action = (
                "Query local land registry and logging permit databases to verify if this clearance "
                "is legally authorized. If unauthorized, issue a stop-work notice."
            )
            reasoning = "Lacks protected status but has active expanding spatial cluster pattern."
            
        else:
            # Low risk
            risk_level = "Low"
            narrative = (
                f"LOW ALERT: Minor vegetation drop ({area_ha} hectares, NDVI drop {ndvi_drop:.2f}) detected in "
                f"unprotected forest. No active clusters or neighboring alerts detected."
            )
            action = (
                "Flag for passive monitoring. Verify against next satellite pass (Sentinel-2) to ensure "
                "vegetation is not recovering (which would indicate cloud shadow or seasonal leaf shedding)."
            )
            reasoning = "Small scale clearance in unprotected forest, with no surrounding active alerts."
            
        return {
            "risk_level": risk_level,
            "narrative_summary": narrative,
            "recommended_action": action,
            "reasoning_chain": reasoning
        }
