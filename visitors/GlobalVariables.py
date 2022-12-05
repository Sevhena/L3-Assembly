import ast

class GlobalVariableExtraction(ast.NodeVisitor):
    """ 
        We extract all the left hand side of the global (top-level) assignments
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.results = {}
        self.func_results = {}
        self.params = {}
        self.ret = {}
        self.parameters = 0
        self.returns = 0
        

    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")
        if(node.targets[0].id not in self.results):
            if('value' in node.value.__match_args__):
                self.results[node.targets[0].id] = [str(type(node.value)),node.value.value]
            else:
                self.results[node.targets[0].id] = str(type(node.value))


    def vis_Asg_func(self, node):
        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")
        if(node.targets[0].id not in self.func_results):
            if('value' in node.value.__match_args__):
                self.func_results[node.targets[0].id] = [str(type(node.value)),node.value.value]
            else:
                self.func_results[node.targets[0].id] = str(type(node.value))


    def visit_FunctionDef(self, node):
        """We do not visit function definitions, they are not global by definition"""
        for i in node.args.args:
            self.params[str(i.arg)] = "para"+ str(self.parameters+1)
            self.parameters+=1

        for nobe in node.body:
            if(str(type(nobe)) == "<class 'ast.Assign'>"):
                self.vis_Asg_func(nobe)
            if(str(type(nobe)) == "<class 'ast.Return'>"):
                self.ret[nobe.value.id] = ["retVal"+str(self.returns+1),"ans"+str(self.returns+1)]
                self.returns+=1
                

