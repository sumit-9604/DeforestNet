# Planner for the DeForestNet Agent

import json
import requests
from backend.config import LLM_PROVIDER, GEMINI_API_KEY, CLAUDE_API_KEY
from backend.agent.prompts import PLANNER_PROMPT_TEMPLATE, SYSTEM_PROMPT
from backend.services.llm_reasoning import LLMReasoningService
from backend.models.alert import Alert, RegionOfInterest
from backend.models.report import Report
from backend.utils.logger import setup_logger

logger = setup_logger("agent_planner")


class AgentPlanner:
    def __init__(self):
        self.provider = LLM_PROVIDER
        self.reasoning_service = LLMReasoningService()

    def decide_next_step(self, memory, db=None, human_oversight: bool = True) -> dict:
        """
        Determines the next tool to run based on memory context.
        Uses LLM (Gemini/Claude) or the rule-based state machine in mock mode.
        """
        logger.info(f"Planner decision requested. Provider: {self.provider}. Human oversight: {human_oversight}")
        
        if self.provider == "mock":
            decision = self._decide_mock_state_machine(memory, db)
        else:
<<<<<<< Updated upstream
            return self._decide_llm(memory, db)
=======
            decision = self._decide_llm(memory, db)
            
        # Intercept and block notification tool if human oversight is active
        if decision and decision.get("tool") == "NotificationTool" and human_oversight:
            logger.info("Human oversight is active. Intercepting NotificationTool execution.")
            return {
                "tool": None,
                "parameters": {},
                "reasoning": "Report compiled. Human oversight is active, pausing for manual authorization.",
                "finished": True
            }
            
        return decision
>>>>>>> Stashed changes

    def _decide_mock_state_machine(self, memory, db) -> dict:
        """Deterministic state machine implementing the exact workflow of the PRD"""
        region_name = memory.region_name
        logs = memory.logs

        # Step 1 & 2: Get Alerts
        gfw_logs = [l for l in logs if l["tool"] == "GetForestAlertsTool"]
        if not gfw_logs:
            return {
                "tool": "GetForestAlertsTool",
                "parameters": {"region_name": region_name},
                "reasoning": "Step 1: Retrieve latest deforestation alerts for the region.",
                "finished": False
            }

        # Save alerts to memory once retrieved
        if not memory.alerts:
            alerts = gfw_logs[0]["output"]
            if isinstance(alerts, list):
                memory.alerts = alerts
                memory.metrics["raw_alerts_received"] = len(alerts)
                logger.info(f"Loaded {len(alerts)} alerts into memory.")
            
        if not memory.alerts:
            logger.info("No alerts retrieved. Finishing workflow.")
            return {
                "tool": None,
                "parameters": {},
                "reasoning": "No alerts found to process. Workflow finished.",
                "finished": True
            }

        # If we haven't selected an alert yet, select the first one
        if memory.current_alert_idx == -1:
            memory.current_alert_idx = 0
            memory.current_alert = memory.alerts[0].copy()
            logger.info("Selected first alert to process.")

        # Process alerts one by one
        while memory.current_alert_idx < len(memory.alerts):
            idx = memory.current_alert_idx
            alert = memory.current_alert
            lat = alert.get("latitude")
            lon = alert.get("longitude")
            area_ha = alert.get("area_ha")
            details = alert.get("details", "")
            alert_id = alert.get("alert_id")

            # Filter logs relevant to this specific coordinate / alert
            alert_logs = []
            for l in logs:
                params = l["parameters"]
                output = l.get("output", {})
                if not isinstance(output, dict):
                    output = {}

                # Extract lat/lon from params or nested params
                log_lat = params.get("latitude")
                log_lon = params.get("longitude")
                if log_lat is None:
                    log_lat = params.get("parameters", {}).get("latitude")
                if log_lon is None:
                    log_lon = params.get("parameters", {}).get("longitude")

                # Extract alert_id from params, nested params, or tool output
                log_alert_id = params.get("alert_id")
                if log_alert_id is None:
                    log_alert_id = params.get("parameters", {}).get("alert_id")
                if log_alert_id is None:
                    log_alert_id = output.get("alert_id")

                matches_coord = False
                if log_lat is not None and log_lon is not None:
                    if abs(log_lat - lat) < 0.001 and abs(log_lon - lon) < 0.001:
                        matches_coord = True

                matches_id = False
                if alert_id is not None and log_alert_id is not None:
                    if int(log_alert_id) == int(alert_id):
                        matches_id = True

                if matches_coord or matches_id:
                    alert_logs.append(l)

            # Check if check_exists operation has run
            check_exists_logs = [l for l in alert_logs if l["tool"] == "DatabaseTool" and l["parameters"].get("operation") == "check_exists"]
            if not check_exists_logs:
                return {
                    "tool": "DatabaseTool",
                    "parameters": {
                        "operation": "check_exists",
                        "parameters": {"latitude": lat, "longitude": lon}
                    },
                    "reasoning": f"Check if alert at ({lat:.4f}, {lon:.4f}) already exists to avoid duplicate processing.",
                    "finished": False
                }

            # Handle exist verification
            exists_output = check_exists_logs[0]["output"]
            if exists_output.get("exists"):
                logger.info(f"Alert at ({lat:.4f}, {lon:.4f}) already exists (ID: {exists_output.get('alert_id')}). Skipping.")
                # Move to next alert
                memory.current_alert_idx += 1
                if memory.current_alert_idx < len(memory.alerts):
                    memory.current_alert = memory.alerts[memory.current_alert_idx].copy()
                    continue
                else:
                    return {
                        "tool": None,
                        "parameters": {},
                        "reasoning": "All alerts processed.",
                        "finished": True
                    }

            # Create Alert in DB if check_exists indicates new alert
            create_alert_logs = [l for l in alert_logs if l["tool"] == "DatabaseTool" and l["parameters"].get("operation") == "create_alert"]
            if not create_alert_logs:
                # Increment processed count metrics
                memory.metrics["new_alerts_processed"] += 1
                return {
                    "tool": "DatabaseTool",
                    "parameters": {
                        "operation": "create_alert",
                        "parameters": {
                            "latitude": lat,
                            "longitude": lon,
                            "area_ha": area_ha,
                            "details": details,
                            "region_name": region_name
                        }
                    },
                    "reasoning": f"Save new alert record to database for coordinate ({lat:.4f}, {lon:.4f}).",
                    "finished": False
                }

            # Get generated database alert ID
            alert_id = create_alert_logs[0]["output"].get("alert_id")
            alert["alert_id"] = alert_id

            # Fetch satellite imagery
            fetch_img_logs = [l for l in alert_logs if l["tool"] == "FetchSatelliteImageTool"]
            if not fetch_img_logs:
                return {
                    "tool": "FetchSatelliteImageTool",
                    "parameters": {"latitude": lat, "longitude": lon, "alert_id": alert_id},
                    "reasoning": f"Fetch pre- and post-clearing satellite bands for alert {alert_id}.",
                    "finished": False
                }

            # Run NDVI verification
            imagery_paths = fetch_img_logs[0]["output"]
            alert["imagery_paths"] = imagery_paths
            ndvi_logs = [l for l in alert_logs if l["tool"] == "ComputeNDVITool"]
            if not ndvi_logs:
                return {
                    "tool": "ComputeNDVITool",
                    "parameters": {"imagery_paths": imagery_paths, "area_ha": area_ha, "alert_id": alert_id},
                    "reasoning": f"Perform NDVI change calculation to verify vegetation loss.",
                    "finished": False
                }

            # Handle NDVI verification results
            ndvi_result = ndvi_logs[0]["output"]
            is_verified = ndvi_result.get("is_verified", False)
            
            if not is_verified:
                # Mark as False Positive in DB
                update_fp_logs = [l for l in alert_logs if l["tool"] == "DatabaseTool" and l["parameters"].get("operation") == "update_alert" and l["parameters"].get("parameters", {}).get("status") == "False Positive"]
                if not update_fp_logs:
                    return {
                        "tool": "DatabaseTool",
                        "parameters": {
                            "operation": "update_alert",
                            "parameters": {"alert_id": alert_id, "status": "False Positive", "risk_level": "Low"}
                        },
                        "reasoning": f"NDVI change detection did not verify vegetation loss. Marking alert {alert_id} as False Positive.",
                        "finished": False
                    }
                # Move to next alert
                logger.info(f"Alert {alert_id} is a False Positive. Done.")
                memory.current_alert_idx += 1
                if memory.current_alert_idx < len(memory.alerts):
                    memory.current_alert = memory.alerts[memory.current_alert_idx].copy()
                    continue
                else:
                    return {
                        "tool": None,
                        "parameters": {},
                        "reasoning": "All alerts processed.",
                        "finished": True
                    }

            # If verified, keep metrics
            # Look up protected area boundaries
            protected_logs = [l for l in alert_logs if l["tool"] == "ProtectedAreaLookupTool"]
            if not protected_logs:
                # Store metric
                memory.metrics["verified_deforestation_events"] += 1
                return {
                    "tool": "ProtectedAreaLookupTool",
                    "parameters": {"latitude": lat, "longitude": lon, "alert_id": alert_id},
                    "reasoning": f"Look up if coordinates intersect with protected area limits.",
                    "finished": False
                }

            # Proximity / active cluster check
            historical_logs = [l for l in alert_logs if l["tool"] == "HistoricalAlertTool"]
            if not historical_logs:
                return {
                    "tool": "HistoricalAlertTool",
                    "parameters": {"latitude": lat, "longitude": lon, "alert_id": alert_id},
                    "reasoning": f"Find neighboring alerts in the last 30 days.",
                    "finished": False
                }

            # Retrieve outputs
            protected_info = protected_logs[0]["output"]
            historical_info = historical_logs[0]["output"] # dict contains neighboring_alerts_30d, is_active_cluster
            
            # Save enrichment status to database
            enrich_db_logs = [l for l in alert_logs if l["tool"] == "DatabaseTool" and l["parameters"].get("operation") == "enrich_alert"]
            if not enrich_db_logs:
                return {
                    "tool": "DatabaseTool",
                    "parameters": {
                        "operation": "enrich_alert",
                        "parameters": {
                            "alert_id": alert_id,
                            "is_protected": protected_info.get("is_protected", False),
                            "protected_area_name": protected_info.get("name"),
                            "protected_area_category": protected_info.get("category"),
                            "neighboring_alerts_30d": historical_info.get("neighboring_alerts_30d", 0),
                            "is_active_cluster": historical_info.get("is_active_cluster", False)
                        }
                    },
                    "reasoning": "Store enriched geographical details in database.",
                    "finished": False
                }

            # Update DB details and run LLM reasoning
            update_verified_logs = [l for l in alert_logs if l["tool"] == "DatabaseTool" and l["parameters"].get("operation") == "update_alert" and l["parameters"].get("parameters", {}).get("status") == "Verified"]
            if not update_verified_logs:
                # Prepare LLM input payload
                llm_input = {
                    "latitude": lat,
                    "longitude": lon,
                    "area_ha": ndvi_result.get("verified_area_ha", area_ha),
                    "ndvi_before_mean": ndvi_result.get("ndvi_before_mean", 0.0),
                    "ndvi_after_mean": ndvi_result.get("ndvi_after_mean", 0.0),
                    "ndvi_diff_mean": ndvi_result.get("ndvi_diff_mean", 0.0),
                    "is_protected": protected_info.get("is_protected", False),
                    "protected_area_name": protected_info.get("name"),
                    "protected_area_category": protected_info.get("category"),
                    "is_active_cluster": historical_info.get("is_active_cluster", False),
                    "neighboring_alerts_30d": historical_info.get("neighboring_alerts_30d", 0)
                }
                
                # Perform LLM analysis (uses configured provider or fallback heuristics)
                llm_result = self.reasoning_service.analyze_alert(llm_input)
                alert["analysis_result"] = llm_result
                
                return {
                    "tool": "DatabaseTool",
                    "parameters": {
                        "operation": "update_alert",
                        "parameters": {
                            "alert_id": alert_id,
                            "status": "Verified",
                            "risk_level": llm_result.get("risk_level", "Medium"),
                            "ndvi_before": ndvi_result.get("ndvi_before_mean"),
                            "ndvi_after": ndvi_result.get("ndvi_after_mean"),
                            "ndvi_diff": ndvi_result.get("verified_area_ha"),
                            "imagery_before_path": imagery_paths.get("before", {}).get("rgb"),
                            "imagery_after_path": imagery_paths.get("after", {}).get("rgb"),
                            "details": {
                                "reasoning_chain": llm_result.get("reasoning_chain"),
                                "analysis_result": llm_result
                            }
                        }
                    },
                    "reasoning": "Update Alert status to Verified and save risk classification & reasoning.",
                    "finished": False
                }

            # Retrieve analysis result from the memory if not populated
            if "analysis_result" not in alert:
                update_log = update_verified_logs[0]
                details_param = update_log["parameters"].get("parameters", {}).get("details", {})
                alert["analysis_result"] = details_param.get("analysis_result", {})

            # Generate comparative image and PDF report
            report_gen_logs = [l for l in alert_logs if l["tool"] == "ReportGeneratorTool"]
            if not report_gen_logs:
                return {
                    "tool": "ReportGeneratorTool",
                    "parameters": {
                        "alert_id": alert_id,
                        "analysis_result": alert["analysis_result"]
                    },
                    "reasoning": f"Compile PDF evidence report with comparative satellite bands for alert {alert_id}.",
                    "finished": False
                }

            # Register PDF report record in database
            pdf_path = report_gen_logs[0]["output"]
            alert["pdf_path"] = pdf_path
            create_report_logs = [l for l in alert_logs if l["tool"] == "DatabaseTool" and l["parameters"].get("operation") == "create_report"]
            if not create_report_logs:
                # Find recipient email from region
                region = db.query(RegionOfInterest).filter(RegionOfInterest.name == region_name).first()
                contact_email = region.contact_email if region else "alerts@deforestnet.org"
                alert["recipient_email"] = contact_email
                
                return {
                    "tool": "DatabaseTool",
                    "parameters": {
                        "operation": "create_report",
                        "parameters": {
                            "alert_id": alert_id,
                            "file_path": pdf_path,
                            "narrative_summary": alert["analysis_result"].get("narrative_summary", ""),
                            "recommended_action": alert["analysis_result"].get("recommended_action", ""),
                            "recipient_email": contact_email,
                            "status": "Pending"
                        }
                    },
                    "reasoning": f"Create Report record in database for alert {alert_id}.",
                    "finished": False
                }

            # Get generated report ID
            report_id = create_report_logs[0]["output"].get("report_id")
            alert["report_id"] = report_id

            # Route dispatch of report notification
            notify_logs = [l for l in alert_logs if l["tool"] == "NotificationTool"]
            if not notify_logs:
                recipient_email = create_report_logs[0]["parameters"]["parameters"]["recipient_email"]
                return {
                    "tool": "NotificationTool",
                    "parameters": {
                        "recipient_email": recipient_email,
                        "alert_id": alert_id,
                        "pdf_path": pdf_path
                    },
                    "reasoning": f"Send the compiled PDF report via email notification to {recipient_email}.",
                    "finished": False
                }

            # Check notification status and update report record
            sent_status = notify_logs[0]["output"]
            report_status = "Sent" if sent_status else "Failed"
            update_report_logs = [l for l in alert_logs if l["tool"] == "DatabaseTool" and l["parameters"].get("operation") == "update_report"]
            if not update_report_logs:
                return {
                    "tool": "DatabaseTool",
                    "parameters": {
                        "operation": "update_report",
                        "parameters": {"report_id": report_id, "status": report_status, "alert_id": alert_id}
                    },
                    "reasoning": f"Update Report {report_id} status to '{report_status}' in the database.",
                    "finished": False
                }

            # Update Alert status to Reported (or keep Verified if notify failed)
            final_alert_status = "Reported" if sent_status else "Verified"
            update_alert_final_logs = [l for l in alert_logs if l["tool"] == "DatabaseTool" and l["parameters"].get("operation") == "update_alert" and l["parameters"].get("parameters", {}).get("status") in ("Reported", "Verified") and l["parameters"].get("parameters", {}).get("risk_level") is None]
            if not update_alert_final_logs:
                if sent_status:
                    memory.metrics["evidence_reports_dispatched"] += 1
                return {
                    "tool": "DatabaseTool",
                    "parameters": {
                        "operation": "update_alert",
                        "parameters": {"alert_id": alert_id, "status": final_alert_status}
                    },
                    "reasoning": f"Update Alert {alert_id} status to '{final_alert_status}' in database.",
                    "finished": False
                }

            # Update dashboard timeline
            dashboard_logs = [l for l in alert_logs if l["tool"] == "DashboardTool"]
            if not dashboard_logs:
                return {
                    "tool": "DashboardTool",
                    "parameters": {"alert_id": alert_id, "status": final_alert_status},
                    "reasoning": f"Trigger dashboard updates and timeline logging for alert {alert_id}.",
                    "finished": False
                }

            # Active alert processed! Move to next.
            logger.info(f"Finished processing alert {alert_id} successfully.")
            memory.current_alert_idx += 1
            if memory.current_alert_idx < len(memory.alerts):
                memory.current_alert = memory.alerts[memory.current_alert_idx].copy()
                logger.info(f"Moving to next alert index: {memory.current_alert_idx}")
            else:
                logger.info("All alerts in region processed.")

        return {
            "tool": None,
            "parameters": {},
            "reasoning": "All alerts processed.",
            "finished": True
        }

    def _decide_llm(self, memory, db=None) -> dict:
        """Call LLM provider for planning decisions"""
        # Format the planner prompt
        prompt = PLANNER_PROMPT_TEMPLATE.format(
            region_name=memory.region_name,
            num_alerts=len(memory.alerts),
            current_alert_index=memory.current_alert_idx + 1,
            current_alert_details=json.dumps(memory.current_alert),
            history_log=memory.get_history_summary()
        )

        logger.info(f"Constructed planner prompt. Calling provider {self.provider}...")

        # Invoke API calls
        if self.provider == "gemini":
            response_text = self._call_gemini_api(prompt)
        elif self.provider == "claude":
            response_text = self._call_claude_api(prompt)
        else:
            response_text = None

        if not response_text:
            logger.warning("LLM API failed. Falling back to rule-based state machine.")
<<<<<<< Updated upstream
            # For runtime robustness, fallback to mock state machine
            if db is not None:
                return self._decide_mock_state_machine(memory, db)
            return {"error": "LLM planning call failed and no database context provided for fallback."}
=======
            if db is not None:
                return self._decide_mock_state_machine(memory, db)
            else:
                return {"error": "LLM planning call failed and no database context provided for fallback."}
>>>>>>> Stashed changes

        try:
            return self._parse_llm_json(response_text)
        except Exception as e:
            logger.error(f"Failed to parse LLM planning response: {e}. Raw response: {response_text}")
            if db is not None:
                logger.warning("Parsing failed. Falling back to rule-based state machine.")
                return self._decide_mock_state_machine(memory, db)
            return {"error": f"LLM returned invalid JSON: {str(e)}"}

    def _parse_llm_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)

    def _call_gemini_api(self, prompt: str) -> str:
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
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                result_json = response.json()
                return result_json["candidates"][0]["content"]["parts"][0]["text"]
            else:
                logger.error(f"Gemini API error (Planner): {response.text}")
        except Exception as e:
            logger.error(f"Gemini API Exception (Planner): {e}")
        return ""

    def _call_claude_api(self, prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                result_json = response.json()
                return result_json["content"][0]["text"]
            else:
                logger.error(f"Claude API error (Planner): {response.text}")
        except Exception as e:
            logger.error(f"Claude API Exception (Planner): {e}")
        return ""
