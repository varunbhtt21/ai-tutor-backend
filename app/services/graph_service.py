"""
Graph validation and traversal service for bubble graphs
"""

from typing import List, Dict, Set, Optional, Tuple, Any
import logging
from collections import defaultdict, deque

from app.schemas.session import BubbleGraphSchema, GraphValidationResponse

logger = logging.getLogger(__name__)


class GraphService:
    """Service for bubble graph operations"""
    
    def __init__(self):
        pass
    
    def validate_graph(self, graph: BubbleGraphSchema) -> GraphValidationResponse:
        """Comprehensive graph validation"""
        errors = []
        warnings = []
        
        try:
            # Basic structure validation
            node_count = len(graph.nodes)
            edge_count = len(graph.edges)
            
            if node_count == 0:
                errors.append("Graph must have at least one node")
                return GraphValidationResponse(
                    is_valid=False, errors=errors, warnings=warnings,
                    node_count=0, edge_count=0, has_cycles=False
                )
            
            # Check for start node
            node_ids = {node.id for node in graph.nodes}
            if graph.start_node not in node_ids:
                errors.append(f"Start node '{graph.start_node}' not found in graph nodes")
            
            # Check edge connectivity
            edge_errors = self._validate_edges(graph.edges, node_ids)
            errors.extend(edge_errors)
            
            # Check for cycles
            has_cycles = self._has_cycles(graph)
            if has_cycles:
                warnings.append("Graph contains cycles - students may get stuck in loops")
            
            # Check for unreachable nodes
            unreachable = self._find_unreachable_nodes(graph)
            if unreachable:
                warnings.append(f"Unreachable nodes found: {', '.join(unreachable)}")
            
            # Check for dead ends (nodes with no outgoing edges except last nodes)
            dead_ends = self._find_dead_ends(graph)
            if len(dead_ends) > 1:
                warnings.append(f"Multiple dead ends found: {', '.join(dead_ends)}")
            
            # Validate node types and content
            content_warnings = self._validate_node_content(graph.nodes)
            warnings.extend(content_warnings)
            
            is_valid = len(errors) == 0
            
            return GraphValidationResponse(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                node_count=node_count,
                edge_count=edge_count,
                has_cycles=has_cycles,
                unreachable_nodes=unreachable
            )
            
        except Exception as e:
            logger.error(f"Graph validation error: {e}")
            return GraphValidationResponse(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=warnings,
                node_count=len(graph.nodes) if graph.nodes else 0,
                edge_count=len(graph.edges) if graph.edges else 0,
                has_cycles=False
            )
    
    def _validate_edges(self, edges: List[Any], node_ids: Set[str]) -> List[str]:
        """Validate edge connectivity"""
        errors = []
        
        for edge in edges:
            if edge.from_node not in node_ids:
                errors.append(f"Edge references unknown from_node: {edge.from_node}")
            if edge.to_node not in node_ids:
                errors.append(f"Edge references unknown to_node: {edge.to_node}")
            if edge.from_node == edge.to_node:
                errors.append(f"Self-loop detected: {edge.from_node} -> {edge.to_node}")
        
        return errors
    
    def _has_cycles(self, graph: BubbleGraphSchema) -> bool:
        """Check for cycles using DFS"""
        # Build adjacency list
        adj_list = defaultdict(list)
        for edge in graph.edges:
            adj_list[edge.from_node].append(edge.to_node)
        
        # Track visited nodes and recursion stack
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            if node in rec_stack:
                return True  # Cycle found
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in adj_list[node]:
                if dfs(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check each node
        for node in [n.id for n in graph.nodes]:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def _find_unreachable_nodes(self, graph: BubbleGraphSchema) -> List[str]:
        """Find nodes unreachable from start node"""
        # Build adjacency list
        adj_list = defaultdict(list)
        for edge in graph.edges:
            adj_list[edge.from_node].append(edge.to_node)
        
        # BFS from start node
        visited = set()
        queue = deque([graph.start_node])
        visited.add(graph.start_node)
        
        while queue:
            current = queue.popleft()
            for neighbor in adj_list[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # Find unreachable nodes
        all_nodes = {node.id for node in graph.nodes}
        unreachable = list(all_nodes - visited)
        return unreachable
    
    def _find_dead_ends(self, graph: BubbleGraphSchema) -> List[str]:
        """Find nodes with no outgoing edges"""
        nodes_with_outgoing = set()
        for edge in graph.edges:
            nodes_with_outgoing.add(edge.from_node)
        
        all_nodes = {node.id for node in graph.nodes}
        dead_ends = list(all_nodes - nodes_with_outgoing)
        return dead_ends
    
    def _validate_node_content(self, nodes: List[Any]) -> List[str]:
        """Validate node content and types"""
        warnings = []
        
        type_counts = defaultdict(int)
        for node in nodes:
            type_counts[node.type] += 1
            
            # Check for missing titles
            if not node.title or len(node.title.strip()) == 0:
                warnings.append(f"Node '{node.id}' has empty title")
        
        # Check for balanced content types
        if type_counts.get("concept", 0) == 0:
            warnings.append("No concept bubbles found - consider adding explanatory content")
        
        if type_counts.get("task", 0) == 0 and type_counts.get("quiz", 0) == 0:
            warnings.append("No interactive bubbles found - consider adding tasks or quizzes")
        
        return warnings
    
    def get_next_nodes(self, graph: BubbleGraphSchema, current_node: str) -> List[str]:
        """Get possible next nodes from current node"""
        next_nodes = []
        for edge in graph.edges:
            if edge.from_node == current_node:
                next_nodes.append(edge.to_node)
        return next_nodes
    
    def get_valid_paths(self, graph: BubbleGraphSchema) -> List[List[str]]:
        """Get all valid paths through the graph"""
        paths = []
        
        def dfs_paths(current: str, path: List[str], visited: Set[str]):
            # Avoid infinite loops
            if current in visited:
                return
            
            new_path = path + [current]
            new_visited = visited.copy()
            new_visited.add(current)
            
            # Get next nodes
            next_nodes = self.get_next_nodes(graph, current)
            
            if not next_nodes:
                # End of path
                paths.append(new_path)
            else:
                for next_node in next_nodes:
                    dfs_paths(next_node, new_path, new_visited)
        
        dfs_paths(graph.start_node, [], set())
        return paths
    
    def calculate_graph_metrics(self, graph: BubbleGraphSchema) -> Dict[str, Any]:
        """Calculate graph complexity metrics"""
        metrics = {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "start_node": graph.start_node,
            "has_cycles": self._has_cycles(graph),
            "unreachable_nodes": len(self._find_unreachable_nodes(graph)),
            "dead_ends": len(self._find_dead_ends(graph)),
        }
        
        # Calculate node type distribution
        type_counts = defaultdict(int)
        for node in graph.nodes:
            type_counts[node.type] += 1
        metrics["node_types"] = dict(type_counts)
        
        # Calculate average branching factor
        outgoing_counts = defaultdict(int)
        for edge in graph.edges:
            outgoing_counts[edge.from_node] += 1
        
        if outgoing_counts:
            avg_branching = sum(outgoing_counts.values()) / len(outgoing_counts)
            metrics["avg_branching_factor"] = round(avg_branching, 2)
        else:
            metrics["avg_branching_factor"] = 0
        
        # Calculate estimated completion time
        estimated_minutes = len(graph.nodes) * 5  # 5 minutes per node average
        metrics["estimated_completion_minutes"] = estimated_minutes
        
        return metrics
    
    def suggest_graph_improvements(self, graph: BubbleGraphSchema) -> List[str]:
        """Suggest improvements for the graph"""
        suggestions = []
        
        validation = self.validate_graph(graph)
        
        # Based on validation results
        if validation.unreachable_nodes:
            suggestions.append("Connect unreachable nodes to the main learning path")
        
        if validation.has_cycles:
            suggestions.append("Review cycles to ensure they don't create infinite loops")
        
        # Based on content analysis
        type_counts = defaultdict(int)
        for node in graph.nodes:
            type_counts[node.type] += 1
        
        if type_counts.get("concept", 0) < type_counts.get("task", 0):
            suggestions.append("Add more concept bubbles to explain before practice")
        
        if len(graph.nodes) > 10:
            suggestions.append("Consider breaking this into multiple sessions")
        
        if len(graph.edges) < len(graph.nodes) - 1:
            suggestions.append("Graph seems linear - consider adding alternative paths")
        
        return suggestions 