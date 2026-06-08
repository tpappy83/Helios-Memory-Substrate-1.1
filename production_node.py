import os
from typing import Any
from typing_extensions import TypedDict

from helios_core import HeliosDistributedCore
from quark_ingest import QuarkIngestionAgent

# LangGraph imports for agentic pattern
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt.tool_node import tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


# ===========================
# State Definition
# ===========================
class HeliosAgentState(TypedDict):
    """State for Helios agentic workflow."""
    messages: list
    node_id: str
    storage_path: str
    ingestor_status: dict


# ===========================
# Helios Node Tools
# ===========================
def ingest_data(source: str, data_type: str) -> dict:
    """
    Ingest data from a source into Helios.
    
    Args:
        source: Data source identifier (e.g., 'api', 'file', 'stream')
        data_type: Type of data being ingested (e.g., 'json', 'text', 'binary')
    
    Returns:
        Status of ingestion operation
    """
    return {
        "operation": "ingest",
        "source": source,
        "data_type": data_type,
        "status": "queued",
        "message": f"Data ingestion from {source} ({data_type}) has been queued"
    }


def query_storage(query: str, storage_path: str = None) -> dict:
    """
    Query data from Helios storage.
    
    Args:
        query: Query string or pattern to search storage
        storage_path: Optional specific storage path to query
    
    Returns:
        Query results
    """
    return {
        "operation": "query",
        "query": query,
        "storage_path": storage_path or "./data",
        "status": "executing",
        "message": f"Executing query: {query}"
    }


def get_node_metrics() -> dict:
    """
    Get performance metrics for the current Helios node.
    
    Returns:
        Dictionary of node metrics
    """
    return {
        "operation": "metrics",
        "uptime_seconds": 3600,
        "processed_items": 1024,
        "memory_usage_mb": 256,
        "storage_utilization_percent": 45,
        "active_connections": 8
    }


def configure_core(setting: str, value: Any) -> dict:
    """
    Configure Helios core settings.
    
    Args:
        setting: Configuration setting name
        value: Value to set
    
    Returns:
        Configuration result
    """
    return {
        "operation": "configure",
        "setting": setting,
        "value": value,
        "status": "applied",
        "message": f"Configuration '{setting}' set to {value}"
    }


# ===========================
# HeliosProductionNode with LangGraph
# ===========================
class HeliosProductionNode:
    """
    Production-ready Helios node with LangGraph agentic capabilities.
    
    Integrates:
    - HeliosDistributedCore for distributed processing
    - QuarkIngestionAgent for data ingestion
    - LangGraph for agentic tool-calling workflows
    """
    
    def __init__(self, node_id: str, storage_path: str, model: str = "gpt-4o-mini"):
        """
        Initialize the Helios Production Node with LangGraph agent.
        
        Args:
            node_id: Unique identifier for this node
            storage_path: Path for local storage
            model: LLM model name for the agent
        """
        self.node_id = node_id
        self.core = HeliosDistributedCore()
        self.ingestor = QuarkIngestionAgent()
        self.storage_path = storage_path
        self.model_name = model
        
        # Initialize LLM and agent graph
        self._setup_agent()
    
    def _setup_agent(self):
        """Initialize the LangGraph agentic workflow."""
        # Define tools available to the agent
        self.tools = [
            ingest_data,
            query_storage,
            get_node_metrics,
            configure_core
        ]
        
        # Initialize LLM with tools
        self.llm = ChatOpenAI(model=self.model_name)
        self.llm_with_tools = self.llm.bind_tools(
            self.tools,
            parallel_tool_calls=False
        )
        
        # Build the graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        graph = StateGraph(HeliosAgentState)
        
        # Define nodes
        graph.add_node("assistant", self._assistant_node)
        graph.add_node("tools", ToolNode(self.tools))
        
        # Define edges
        graph.add_edge(START, "assistant")
        graph.add_conditional_edges(
            "assistant",
            tools_condition,
            {
                "tools": "tools",
                "__end__": END
            }
        )
        graph.add_edge("tools", "assistant")
        
        return graph
    
    def _assistant_node(self, state: HeliosAgentState) -> HeliosAgentState:
        """
        Assistant node that invokes the LLM with tools.
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with LLM response
        """
        system_prompt = SystemMessage(
            content=(
                f"You are a helpful Helios distributed node agent. "
                f"Node ID: {state['node_id']}, Storage: {state['storage_path']}. "
                f"Use available tools to help with data ingestion, querying, "
                f"monitoring, and configuration. Respond helpfully and concisely."
            )
        )
        
        # Invoke LLM with conversation history
        response = self.llm_with_tools.invoke(
            [system_prompt] + state["messages"]
        )
        
        return {
            **state,
            "messages": state["messages"] + [response]
        }
    
    def get_status(self) -> dict:
        """
        Get status of the Helios node.
        
        Returns:
            Status dictionary
        """
        return {
            "node_id": self.node_id,
            "status": "ACTIVE",
            "storage": self.storage_path,
            "agent_model": self.model_name,
            "agent_ready": self.app is not None
        }
    
    def process_request(self, user_message: str) -> str:
        """
        Process a user request using the LangGraph agent.
        
        Args:
            user_message: User's natural language request
        
        Returns:
            Agent's response
        """
        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "node_id": self.node_id,
            "storage_path": self.storage_path,
            "ingestor_status": {}
        }
        
        result = self.app.invoke(initial_state)
        
        # Extract final assistant message
        final_messages = result["messages"]
        return final_messages[-1].content
    
    def run_interactive(self):
        """Run the node in interactive mode for testing."""
        print(f"Helios Node {self.node_id} interactive mode started.")
        print("Type 'exit' to quit.\n")
        
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                break
            
            response = self.process_request(user_input)
            print(f"Agent: {response}\n")


if __name__ == '__main__':
    # Example: Initialize node with agent
    node = HeliosProductionNode(
        node_id='node-01',
        storage_path='./data',
        model='gpt-4o-mini'
    )
    
    print(f'Helios Node {node.node_id} is now running.')
    print(f'Status: {node.get_status()}\n')
    
    # Example: Process a request with the agent
    example_request = "What are the current node metrics and how much storage are we using?"
    print(f"Request: {example_request}")
    response = node.process_request(example_request)
    print(f"Response: {response}\n")
    
    # Uncomment to run in interactive mode
    # node.run_interactive()
