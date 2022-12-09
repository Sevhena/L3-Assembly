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
        self.retVal = 0
        self.funcNames = []
        self.funcAns = 0
        self.current_function = None
        

    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")
        if(node.targets[0].id not in self.results):
            if('value' in node.value.__match_args__):
                self.results[node.targets[0].id] = [node.value, node.value.value]
            else:
                try:
                    if(node.value.func.id in self.funcNames):
                        self.ret[node.value.func.id] = ["ans"+str(self.funcAns+1),True,node.targets[0].id]
                        self.funcAns+=1
                except:
                    None
                self.results[node.targets[0].id] = node.value


    def vis_Asg_func(self, node):
        # print("@@@@@@@@@@@@@@@@@@@@@@@")
        # print(node.targets[0].id)
        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")
        if(node.targets[0].id not in self.func_results):
            if('value' in node.value.__match_args__):
                self.func_results[node.targets[0].id] = [str(type(node.value)),node.value.value,self.current_function]
            else:
                self.func_results[node.targets[0].id] = [str(type(node.value)),self.current_function]

    def vis_Asg_While(self,node):
        for nobe in node:
            if len(nobe.targets) != 1:
                raise ValueError("Only unary assignments are supported")
            if(nobe.targets[0].id not in self.func_results):
                if('value' in nobe.value.__match_args__):
                    if(nobe.targets[0].id not in self.params):
                        self.func_results[nobe.targets[0].id] = [str(type(nobe.value)),nobe.value.value,self.current_function]
                else:
                    if(nobe.targets[0].id not in self.params):
                        self.func_results[nobe.targets[0].id] = [str(type(nobe.value)),self.current_function]

    def vis_Asg_If(self,node):
        for i in node:
            if(str(type(i)) == "<class 'ast.Return'>"):
                if(str(type(i.value)) != "<class 'ast.Constant'>"):
                    self.ret[i.value.id] = ["retVal"+str(self.retVal+1),False,self.current_function]
                    self.retVal+=1
            else:
                for nobe in node:
                    if len(nobe.targets) != 1:
                        raise ValueError("Only unary assignments are supported")
                    if(nobe.targets[0].id not in self.func_results):
                        if('value' in nobe.value.__match_args__):
                            if(nobe.targets[0].id not in self.params):
                                self.func_results[nobe.targets[0].id] = [str(type(nobe.value)),nobe.value.value,self.current_function]
                        else:
                            if(nobe.targets[0].id not in self.params):
                                self.func_results[nobe.targets[0].id] = [str(type(nobe.value)),self.current_function]


    def visit_FunctionDef(self, node):
        """We do not visit function definitions, they are not global by definition"""
        self.funcNames.append(node.name)
        self.current_function = node.name
        for i in node.args.args:
            self.params[str(i.arg)] = ["para"+ str(self.parameters+1),self.current_function]
            self.parameters+=1
        for nobe in node.body:
            if(str(type(nobe)) == "<class 'ast.Assign'>"):
                self.vis_Asg_func(nobe)
            elif(str(type(nobe)) == "<class 'ast.Return'>"):
                self.ret[nobe.value.id] = ["retVal"+str(self.retVal+1),False,self.current_function]
                self.retVal+=1
            elif(str(type(nobe)) == "<class 'ast.While'>"):
                self.vis_Asg_While(nobe.body)
            elif(str(type(nobe)) =="<class 'ast.If'>"):    
                for i in nobe.__match_args__:
                    if(i == 'body'):
                        self.vis_Asg_If(nobe.body)
                    elif(i == 'orelse'):
                        self.vis_Asg_If(nobe.orelse)

                

