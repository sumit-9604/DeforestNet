# Coordinator for the DeForestNet Agentic Layer

from backend.agent.memory import AgentMemory
from backend.agent.planner import AgentPlanner
from backend.agent.executor import AgentExecutor
from backend.utils.logger import setup_logger

logger = setup_logger("agent_coordinator")


class DeForestNetAgent:
    def __init__(self):
        self.planner = AgentPlanner()
        self.executor = AgentExecutor()

    def run(self, region_name: str, db, human_oversight: bool = True) -> dict:
        """
        Runs the autonomous agentic loop to monitor, analyze, and report 
        deforestation events in the specified region.
        """
        logger.info(f"Starting DeForestNetAgent execution for region: {region_name} (Human oversight: {human_oversight})")
        
        # Initialize memory context
        memory = AgentMemory(region_name)
        
        step_limit = 150  # Upper bound safety threshold to prevent infinite loops
        step_count = 0
        
        while not memory.finished and step_count < step_limit:
            # 1. Decide next step
            decision = self.planner.decide_next_step(memory, db, human_oversight=human_oversight)
            
            if "error" in decision:
                logger.error(f"Agent execution interrupted due to Planner error: {decision['error']}")
                memory.add_log("ErrorState", {}, {"error": decision["error"]})
                break
                
            if decision.get("finished") or decision.get("tool") is None:
                logger.info("Planner signaled workflow completion.")
                memory.finished = True
                break
                
            tool_name = decision["tool"]
            parameters = decision["parameters"]
            
            logger.info(f"Agent Loop Step {step_count + 1}: Selected Tool '{tool_name}' with parameters: {parameters}")
            
            # 2. Execute selected tool
            output = self.executor.execute(tool_name, parameters, db)
            
            # 3. Add to memory logs
            memory.add_log(tool_name, parameters, output)
            
            step_count += 1
            
        if step_count >= step_limit:
            logger.warning(f"Agent loop reached safety step limit ({step_limit}) and was terminated.")
            
        logger.info(f"DeForestNetAgent run complete. Enacted {step_count} tool invocations.")
        logger.info(f"Final metrics gathered: {memory.metrics}")
        
        return memory.metrics
