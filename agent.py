from langgraph.graph import START, StateGraph, MessagesState, END
from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from sub_agents.schema import WorkflowState

from dotenv import load_dotenv
load_dotenv()

llm = ChatOllama(model="llama3.1:8b")

sys_msg = SystemMessage(content="You are a helpful assistant tasked with generating workflow files from CLI tools.")


def assistant(state: WorkflowState):
    """Basic assistant node for handling general messages."""
    with open("assistant_log.txt", "a") as f:
        f.write(str(state) + "\n")

    return {"messages": [state]}


def invocation_subgraph_node(state: WorkflowState):
    """Wrapper node that invokes the invocation subgraph."""
    # Import here to avoid circular dependencies
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'sub-agents'))
    
    with open("invocation_log.txt", "a") as f:
        f.write(str(state) + "\n")

    from sub_agents.invocation import invocation_graph
    return invocation_graph.invoke(state)


def parsing_subgraph_node(state: WorkflowState):
    """Wrapper node that invokes the parsing subgraph."""
    # Import here to avoid circular dependencies
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'sub-agents'))
    
    with open("parsing_log.txt", "a") as f:
        f.write(str(state) + "\n")

    from sub_agents.parsing import parsing_graph
    return parsing_graph.invoke(state)


def standardization_subgraph_node(state: WorkflowState):
    """Wrapper node that invokes the standardization subgraph."""
    # Import here to avoid circular dependencies
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'sub-agents'))
    
    with open("standardization_log.txt", "a") as f:
        f.write(str(state) + "\n")

    from sub_agents.standardization import standardization_graph
    return standardization_graph.invoke(state)



# Create the main workflow graph
builder = StateGraph(WorkflowState)

# Add subgraph nodes to the main workflow
builder.add_node("invocation_subgraph", invocation_subgraph_node)
builder.add_node("parsing_subgraph", parsing_subgraph_node)
builder.add_node("standardization_subgraph", standardization_subgraph_node)
builder.add_node("assistant", assistant)

# Add edges based on the workflow
builder.add_edge(START, "invocation_subgraph")
builder.add_edge("invocation_subgraph", "parsing_subgraph")
builder.add_edge("parsing_subgraph", "standardization_subgraph")
builder.add_edge("standardization_subgraph", "assistant")
builder.add_edge("assistant", END)

# Commented out the full workflow for future implementation
# builder.add_node("troubleshooting_agent", troubleshooting_agent)
# builder.add_node("wdl_generator_agent", wdl_generator_agent)
# builder.add_node("nextflow_generator_agent", nextflow_generator_agent)
# builder.add_edge("standardization_subgraph", "troubleshooting_agent")
# builder.add_edge("troubleshooting_agent", format_condition, ["wdl_generator_agent", "nextflow_generator_agent"])
# builder.add_edge("wdl_generator_agent", END)
# builder.add_edge("nextflow_generator_agent", END)

graph = builder.compile()


if __name__ == "__main__":
    # Simple test
    test_state = {"executable": "samtools"}
    result = graph.invoke(test_state)
    print(result)