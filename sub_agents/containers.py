import requests
from schema import WorkflowState, ToolInfo, ContainerInfo
from typing import Dict, Any

def request_biocontainers(executable: str, version: str) -> dict:
    """Make request to BioContainers given an executable (tool name) and version."""
    url = f"https://api.biocontainers.pro/ga4gh/trs/v2/tools/{executable}/versions/{executable}-{version}"
    # Example: https://api.biocontainers.pro/ga4gh/trs/v2/tools/samtools/versions/samtools-1.19
    print(f"Running request for {executable}-{version}")
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()

            bioconda = docker = singularity = None
            images = data.get("images", [])
            # Loop through images and assign image name based on type
            for x in images:
                if x.get("image_type", "").lower() == "conda":
                    bioconda = x.get("image_name")
                elif x.get("image_type", "").lower() == "docker":
                    docker = x.get("image_name")
                elif x.get("image_type", "").lower() == "singularity":
                    singularity = x.get("image_name")
            return {
                "bioconda": bioconda,
                "docker": docker,
                "singularity": singularity
            }
        else:
            # In the case of a non-success HTTP status code
            return {"error": r.status_code, "message": r.text}
    except requests.Timeout:
        # Handle timeout specifically
        return {"error": "timeout", "message": "Request timed out"}
    except Exception as e:
        # For any other exceptions
        return {"error": "exception", "message": str(e)}


def container_agent(state: WorkflowState) -> Dict[str, Any]:
    """
    Container agent: Captures container environment information for a given tool and version.
    Returns structured JSON output for the parsing agent to process. 
    """
    tool_info = state.get("tool_info")
    if not tool_info:
        raise Exception("Tool info missing from state")
    
    if tool_info.get("error"):
        # Pass through error state
        return {"tool_info": tool_info}
    
    executable = tool_info.get("tool")
    version = tool_info.get("version")
    if not executable:
        raise Exception("Executable name missing from state")
    if not version:
        raise Exception("Version missing from state")

    out = {}
    
    try:
        # Capture container info
        container_info = request_biocontainers(executable, version)
        print(container_info)

        # Create basic container info with raw text
        containers: ContainerInfo = {
            "bioconda": container_info.get("bioconda"),
            "docker": container_info.get("docker"),
            "singularity": container_info.get("singularity")
        }

        # Update tool_info with parsed results
        tool_info: ToolInfo = {
            **tool_info,
            "containers": containers,
        }

        print("Complete container request")

        out = {
            "tool_info": tool_info
        }

    except Exception as e:
        # Return error state
        containers: ContainerInfo = {
            "bioconda": None,
            "docker": None,
            "singularity": None
        }

        print(f"Error in container function: {e}")

        # Update tool_info with parsed results
        tool_info: ToolInfo = {
            **tool_info,
            "containers": containers,
        }

        out = {
            "tool_info": tool_info
        }

    return out

# Create invocation & parser graphs subgraph
graph_builder = StateGraph(WorkflowState)
graph_builder.add_node("invocation_agent", invocation_agent)
graph_builder.add_node("parsing_version_agent", parsing_version_agent)
graph_builder.add_node("container_agent", container_agent)
graph_builder.add_edge(START, "invocation_agent")
graph_builder.add_edge("invocation_agent", "parsing_version_agent")
graph_builder.add_edge("parsing_version_agent", "container_agent")
graph_builder.add_edge("container_agent", END)

# Compile the invocation graph for export
invocation_graph = graph_builder.compile()


# if __name__ == "__main__":
#     # Simple test
#     test_state = {"executable": "bedtools"}
#     result = invocation_graph.invoke(test_state)
#     print(json.dumps(result, indent=2))