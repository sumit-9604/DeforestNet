# Memory representation for the DeForestNet Agent

class AgentMemory:
    def __init__(self, region_name: str):
        self.region_name = region_name
        self.alerts = []  # List of raw alert dicts retrieved
        self.current_alert_idx = -1  # Index of active alert being processed
        self.current_alert = {}  # Details of current active alert
        self.logs = []  # Chronological log of steps: {"step": int, "tool": str, "parameters": dict, "output": any}
        self.finished = False
        
        # Backward compatibility metrics for api response
        self.metrics = {
            "raw_alerts_received": 0,
            "new_alerts_processed": 0,
            "verified_deforestation_events": 0,
            "evidence_reports_dispatched": 0
        }

    def add_log(self, tool_name: str, parameters: dict, output: any):
        """Record a tool execution step"""
        step_num = len(self.logs) + 1
        self.logs.append({
            "step": step_num,
            "tool": tool_name,
            "parameters": parameters,
            "output": output
        })

    def get_history_summary(self) -> str:
        """Returns a string representation of tool history for prompting"""
        if not self.logs:
            return "No tools executed yet."
            
        summary_lines = []
        for entry in self.logs:
            summary_lines.append(
                f"Step {entry['step']}: Called {entry['tool']} "
                f"with {entry['parameters']} -> Output: {entry['output']}"
            )
        return "\n".join(summary_lines)

    def to_dict(self) -> dict:
        """Return dict representation of memory state for planner"""
        return {
            "region_name": self.region_name,
            "num_alerts": len(self.alerts),
            "current_alert_index": self.current_alert_idx,
            "current_alert_details": self.current_alert,
            "history_log": self.get_history_summary()
        }
