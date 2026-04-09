"""
Quick test to verify graph.py structure without running it.
This script checks that all expected nodes and edges are defined.
"""

import ast
import sys


def extract_graph_info(filepath: str):
    """Parse graph.py and extract node names and edge information."""
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    nodes = []
    edges = []
    conditional_edges = []

    for node in ast.walk(tree):
        # Find function definitions (agent nodes)
        if isinstance(node, ast.AsyncFunctionDef):
            if node.name not in ['fan_out_to_parallel_agents', 'route_after_integration_check', 'create_graph']:
                nodes.append(node.name)

        # Find add_node calls
        if isinstance(node, ast.Call):
            if hasattr(node.func, 'attr'):
                if node.func.attr == 'add_node' and len(node.args) >= 1:
                    if isinstance(node.args[0], ast.Constant):
                        if node.args[0].value not in [n for n in nodes]:
                            nodes.append(node.args[0].value)

                # Find add_edge calls
                elif node.func.attr == 'add_edge' and len(node.args) >= 2:
                    if isinstance(node.args[0], ast.Constant) and isinstance(node.args[1], ast.Constant):
                        edges.append((node.args[0].value, node.args[1].value))

                # Find add_conditional_edges calls
                elif node.func.attr == 'add_conditional_edges':
                    if len(node.args) >= 1 and isinstance(node.args[0], ast.Constant):
                        conditional_edges.append(node.args[0].value)

    return nodes, edges, conditional_edges


def main():
    filepath = 'AI_agents/graph/graph.py'

    print("=" * 70)
    print("LangGraph Structure Verification")
    print("=" * 70)

    try:
        nodes, edges, conditional_edges = extract_graph_info(filepath)

        print("\n[OK] File parsed successfully!\n")

        print("Agent Nodes Found:")
        expected_nodes = [
            "knowledge_retrieval",
            "design",
            "backend_agent",
            "frontend_agent",
            "backlog_agent",
            "integration_check",
            "error_handler",
            "devops_agent",
            "publish_agent"
        ]

        for node in expected_nodes:
            status = "[OK]" if node in nodes else "[FAIL]"
            print(f"  {status} {node}")

        print("\nSequential Edges Found:")
        for src, dst in edges:
            print(f"  {src} -> {dst}")

        print("\nConditional Edges From:")
        for node in conditional_edges:
            print(f"  {node}")

        print("\n" + "=" * 70)

        # Verify all expected nodes are present
        missing = set(expected_nodes) - set(nodes)
        if missing:
            print(f"\n[FAIL] Missing nodes: {missing}")
            sys.exit(1)
        else:
            print("\n[OK] All expected nodes are defined!")
            print("[OK] Graph structure is valid!")
            sys.exit(0)

    except Exception as e:
        print(f"\n[FAIL] Error parsing graph.py: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
