#!/usr/bin/env python3
"""Test script for the flowgen CLI agent."""

import sys
import os

# Add the current directory and sub-agents directory to Python path for imports
sys.path.append('.')
sys.path.append('./sub-agents')

def test_subgraphs():
    """Test individual subgraphs first."""
    print("Testing individual subgraphs...")
    
    try:
        # Test invocation subgraph
        from invocation import invocation_graph
        
        print("✅ Invocation subgraph imported successfully")
        
        initial_state = {
            "executable": "ls",
            "messages": []
        }
        
        result = invocation_graph.invoke(initial_state)
        print("✅ Invocation subgraph executed successfully")
        print("Invocation result keys:", list(result.keys()))
        
        # Test parsing subgraph
        from parsing import parsing_graph
        
        print("✅ Parsing subgraph imported successfully")
        
        # Use result from invocation as input to parsing
        parsing_result = parsing_graph.invoke(result)
        print("✅ Parsing subgraph executed successfully")
        print("Parsing result keys:", list(parsing_result.keys()))
        
        return True
        
    except Exception as e:
        print(f"❌ Subgraph test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_workflow():
    """Test the main workflow."""
    print("\nTesting main workflow...")
    
    try:
        from agent import graph
        
        print("✅ Main agent graph imported successfully")
        
        # Test with a simple CLI tool
        initial_state = {
            "executable": "ls",
            "messages": []
        }
        
        result = graph.invoke(initial_state)
        print("✅ Main workflow completed successfully!")
        print("Result keys:", list(result.keys()))
        
        if "tool_info" in result:
            tool_info = result["tool_info"]
            print(f"Tool: {tool_info.get('tool')}")
            print(f"Version: {tool_info.get('version')}")
            print(f"Subcommands found: {len(tool_info.get('subcommands', []))}")
            if tool_info.get('error'):
                print(f"Error: {tool_info['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Main workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting integration tests...")
    
    subgraph_success = test_subgraphs()
    
    if subgraph_success:
        main_success = test_main_workflow()
        
        if main_success:
            print("\n🎉 All tests passed! The modular structure is working correctly.")
        else:
            print("\n❌ Main workflow test failed.")
    else:
        print("\n❌ Subgraph tests failed.")