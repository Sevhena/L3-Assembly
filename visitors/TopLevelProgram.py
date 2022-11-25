import ast

LabeledInstruction = tuple[str, str]

class TopLevelProgram(ast.NodeVisitor):
    """We supports assignments and input/print calls"""
    
    def __init__(self, entry_point,symbols,constants) -> None:
        super().__init__()
        self.__instructions = list()
        self.__record_instruction('NOP1', label=entry_point)
        self.__should_save = True
        self.__current_variable = None
        self.__elem_id = 0
        self.occurance = {}
        self.symbols = symbols
        self.constants = constants
        self.inLoop = []

    def finalize(self):
        self.__instructions.append((None, '.END'))
        return self.__instructions

    ####
    ## Handling Assignments (variable = ...)
    ####

    def visit_Assign(self, node):
        # remembering the name of the target
        self.__current_variable = node.targets[0].id
        if(self.__current_variable in self.symbols):
            temp = self.symbols[self.__current_variable]
        else:
            temp = self.__current_variable
        
        if(self.__current_variable not in self.occurance):
            self.occurance[self.__current_variable] = 1
        else:
            self.occurance[self.__current_variable] += 1
        # visiting the left part, now knowing where to store the result
        if(self.__current_variable[0] != "_"):
            if(str(type(node.value)) == "<class 'ast.Constant'>"):
                if(self.occurance[self.__current_variable] > 1 or (self.__current_variable not in self.inLoop)): #--------------------
                    self.visit(node.value)
                    if self.__should_save:
                        self.__record_instruction(f'STWA {temp},d')
                    else:
                        self.__should_save = True
                    self.__current_variable = None
            else:
                self.visit(node.value)
                if self.__should_save:
                    self.__record_instruction(f'STWA {temp},d')
                else:
                    self.__should_save = True
                self.__current_variable = None

    def visit_Constant(self, node):
        if(self.__current_variable in self.inLoop):
            print("=== ",self.__current_variable, str(type(node.value)))
        if(self.__current_variable[0] != "_"):
            if(self.occurance[self.__current_variable] > 1 or (self.__current_variable not in self.inLoop)): #--------------------
                self.__record_instruction(f'LDWA {node.value},i')
    
    def visit_Name(self, node):
        if(len(node.id) > 8):
            temp = self.symbols[node.id]
        else:
            temp = node.id
        self.__record_instruction(f'LDWA {temp},d')

    def visit_BinOp(self, node):
        self.__access_memory(node.left, 'LDWA')
        if isinstance(node.op, ast.Add):
            self.__access_memory(node.right, 'ADDA')
        elif isinstance(node.op, ast.Sub):
            self.__access_memory(node.right, 'SUBA')
        else:
            raise ValueError(f'Unsupported binary operator: {node.op}')

    def visit_Call(self, node):
        if(self.__current_variable in self.symbols):
            temp = self.symbols[self.__current_variable]
        else:
            temp = self.__current_variable
        match node.func.id:
            case 'int': 
                # Let's visit whatever is casted into an int
                self.visit(node.args[0])
            case 'input':
                # We are only supporting integers for now
                self.__record_instruction(f'DECI {temp},d')
                self.__should_save = False # DECI already save the value in memory
            case 'print':
                # We are only supporting integers for now
                self.__record_instruction(f'DECO {node.args[0].id},d')
            case _:
                raise ValueError(f'Unsupported function call: { node.func.id}')

    ####
    ## Handling While loops (only variable OP variable)
    ####

    def visit_While(self, node):
        self.inLoop.append(node.body[0].targets[0].id)
        loop_id = self.__identify()
        inverted = {
            ast.Lt:  'BRGE', # '<'  in the code means we branch if '>=' 
            ast.LtE: 'BRGT', # '<=' in the code means we branch if '>' 
            ast.Gt:  'BRLE', # '>'  in the code means we branch if '<='
            ast.GtE: 'BRLT', # '>=' in the code means we branch if '<'
        }
        # left part can only be a variable
        self.__access_memory(node.test.left, 'LDWA', label = f'test_{loop_id}')
        # right part can only be a variable
        self.__access_memory(node.test.comparators[0], 'CPWA')
        # Branching is condition is not true (thus, inverted)
        self.__record_instruction(f'{inverted[type(node.test.ops[0])]} end_l_{loop_id}')
        # Visiting the body of the loop
        for contents in node.body:
            self.visit(contents)
        self.__record_instruction(f'BR test_{loop_id}')
        # Sentinel marker for the end of the loop
        self.__record_instruction(f'NOP1', label = f'end_l_{loop_id}')

    ####
    ## Not handling function calls 
    ####

    def visit_FunctionDef(self, node):
        """We do not visit function definitions, they are not top level"""
        pass

    ####
    ## Helper functions to 
    ####

    def __record_instruction(self, instruction, label = None):
        self.__instructions.append((label, instruction))

    def __access_memory(self, node, instruction, label = None):
        if isinstance(node, ast.Constant):
            self.__record_instruction(f'{instruction} {node.value},i', label)
        else:
            if(len(node.id) > 8):
                temp = self.symbols[node.id]
            else:
                temp = node.id
            if(node.id in self.constants):
                self.__record_instruction(f'{instruction} {temp},i', label)
            else:
                self.__record_instruction(f'{instruction} {temp},d', label)


    def __identify(self):
        result = self.__elem_id
        self.__elem_id = self.__elem_id + 1
        return result