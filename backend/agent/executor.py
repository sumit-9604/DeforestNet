# Executor for the DeForestNet Agent

from backend.agent.tools import (
    GetForestAlertsTool,
    FetchSatelliteImageTool,
    ComputeNDVITool,
    ProtectedAreaLookupTool,
    HistoricalAlertTool,
    ReportGeneratorTool,
    NotificationTool,
    DashboardTool,
    DatabaseTool
)
from backend.utils.logger import setup_logger

logger = setup_logger("agent_executor")


class AgentExecutor:
    def __init__(self):
        # Register tools
        self.tools = {
            "GetForestAlertsTool": GetForestAlertsTool(),
            "FetchSatelliteImageTool": FetchSatelliteImageTool(),
            "ComputeNDVITool": ComputeNDVITool(),
            "ProtectedAreaLookupTool": ProtectedAreaLookupTool(),
            "HistoricalAlertTool": HistoricalAlertTool(),
            "ReportGeneratorTool": ReportGeneratorTool(),
            "NotificationTool": NotificationTool(),
            "DashboardTool": DashboardTool(),
            "DatabaseTool": DatabaseTool()
        }

    def execute(self, tool_name: str, parameters: dict, db=None) -> any:
        """Executes the specified tool with parameters and returns the output"""
        logger.info(f"Executor received tool request: {tool_name} with params {parameters}")
        
        tool = self.tools.get(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' is not registered."
            logger.error(error_msg)
            return {"error": error_msg}

        try:
            output = tool.run(parameters, db)
            logger.info(f"Tool {tool_name} executed successfully. Output: {output}")
            return output
        except Exception as e:
            error_msg = f"Exception executing tool {tool_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}
