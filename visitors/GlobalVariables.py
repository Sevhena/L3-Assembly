import ast

class GlobalVariableExtraction(ast.NodeVisitor):
    """ 
        We extract all the left hand side of the global (top-level) assignments
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.results = {}

    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")
        if(node.targets[0].id not in self.results):
            if('value' in node.value.__match_args__):
                self.results[node.targets[0].id] = [str(type(node.value)),node.value.value]
            else:
                self.results[node.targets[0].id] = str(type(node.value))



    def visit_FunctionDef(self, node):
        """We do not visit function definitions, they are not global by definition"""
        pass
   