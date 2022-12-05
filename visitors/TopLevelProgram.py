import ast

LabeledInstruction = tuple[str, str]

class TopLevelProgram(ast.NodeVisitor):
    """We supports assignments and input/print calls"""
    
    def __init__(self, entry_point,global_symbols,constants,func_sysmbols,numOfFuncVars,params,ret) -> None:
        super().__init__()
        self.__instructions = list()
        self.__instructionsFunc = list()
        self.params = params
        self.ret = ret
        self.__record_instruction('NOP1', label=entry_point)
        if(len(self.params)>0):
            #add the length of the ret to the string
            self.__record_instruction('SUBSP '+str((len(self.params)+len(self.ret))*2)+",i")
        self.__should_save = True
        self.__current_variable = None
        self.__loop_id = 0 # Counts loops in program
        self.__if_id = 0 # Counts ifs in program
        self.__if_tree_id = 0 # Counts if trees in program
        self.__in_if_tree = False
        self.occurance = {}
        self.global_symbols = global_symbols
        self.constants = constants
        self.inLoop = False
        self.func_symbols =func_sysmbols
        self.inFunctionDef = False
        self.numOfFuncVars = numOfFuncVars
        self.funcNames = []
        self.numReturned = 0


    def finalize(self):
        self.__instructions.append((None, '.END'))
        return self.__instructionsFunc + self.__instructions

    ####
    ## Handling Assignments (variable = ...)
    ####

    def visit_Assign(self, node):
        # remembering the name of the target
        self.__current_variable = node.targets[0].id
        returning = False
        try:
            if(self.__current_variable in self.ret and node.value.func.id in self.funcNames):
                temp = self.ret[self.__current_variable][1]
                returning = True
        except:
            if(self.__current_variable in self.global_symbols):
                temp = self.global_symbols[self.__current_variable]
            else:
                temp = self.__current_variable
            
            if(self.__current_variable not in self.occurance):
                self.occurance[self.__current_variable] = 1
            else:
                self.occurance[self.__current_variable] += 1
        
        # visiting the left part, now knowing where to store the result
        

        if(self.__current_variable[0] != "_"):
            if(str(type(node.value)) == "<class 'ast.Constant'>"):
                if(self.occurance[self.__current_variable] > 1 or (self.inLoop == True)): #--------------------
                    self.visit(node.value)
                    if self.__should_save:
                        if(self.inFunctionDef):
                            if(temp in self.params):
                                temp = self.params[temp]
                            self.__record_instructionFunction(f'STWA {temp},s')
                        else:
                            self.__record_instruction(f'STWA {temp},d')
                    else:
                        self.__should_save = True
                    self.__current_variable = None
            else:
                self.visit(node.value)
                if self.__should_save:
                    if(self.inFunctionDef):
                        if(temp in self.params):
                            temp = self.params[temp]
                        self.__record_instructionFunction(f'STWA {temp},s')
                    else:
                        if(returning):
                            self.__record_instruction(f'LDWA {self.numReturned},s')
                            self.numReturned +=2
                            returning = False
                        self.__record_instruction(f'STWA {temp},d')
                else:
                    self.__should_save = True
                self.__current_variable = None

    def visit_Constant(self, node):
        if(self.__current_variable[0] != "_"):
            if(self.occurance[self.__current_variable] > 1 or (self.inLoop == True)): #--------------------
                if(self.inFunctionDef):
                    self.__record_instructionFunction(f'LDWA {node.value},i')
                else:
                    self.__record_instruction(f'LDWA {node.value},i')
    
    def visit_Name(self, node):
        if(len(node.id) > 8):
            temp = self.global_symbols[node.id]
        else:
            temp = node.id
        if(self.inFunctionDef):
            if(temp in self.params):
                temp = self.params[temp]
            self.__record_instructionFunction(f'LDWA {temp},s')
        else:
            self.__record_instruction(f'LDWA {temp},d')

    def visit_BinOp(self, node): #Binary Operation
        self.__access_memory(node.left, 'LDWA')
        if isinstance(node.op, ast.Add):
            self.__access_memory(node.right, 'ADDA')
        elif isinstance(node.op, ast.Sub):
            self.__access_memory(node.right, 'SUBA')
        else:
            raise ValueError(f'Unsupported binary operator: {node.op}')

    def visit_Call(self, node):
        if(self.__current_variable in self.global_symbols):
            temp = self.global_symbols[self.__current_variable]
        else:
            temp = self.__current_variable
        match node.func.id:
            case 'int': 
                # Let's visit whatever is casted into an int
                self.visit(node.args[0])
            case 'input':
                # We are only supporting integers for now
                if(self.inFunctionDef):
                    self.__record_instructionFunction(f'DECI {temp},s')
                else:
                    self.__record_instruction(f'DECI {temp},d')
                self.__should_save = False # DECI already save the value in memory
            case 'print':
                # We are only supporting integers for now
                if(self.inFunctionDef):
                    self.__record_instructionFunction(f'DECO {node.args[0].id},s')
                else:
                    try:
                        if(node.args[0].id in self.ret):
                            temp = self.ret[node.args[0].id][1]
                            self.__record_instruction(f'ADDSP {2},i')
                    except:
                        temp = node.args[0].id
                    self.__record_instruction(f'DECO {temp},d')
            case _:
                if(str(node.func.id) in self.funcNames):
                    if(len(node.args)>0):
                        count = 0
                        for p in node.args:
                            self.__record_instruction(f'LDWA {p.id},d')
                            self.__record_instruction(f'STWA {count},s')
                            count+=2

                    self.__record_instruction(f'CALL {node.func.id}')
                    self.__record_instruction(f'ADDSP '+str(len(self.params)*2)+",i")
                else:
                    raise ValueError(f'Unsupported function call: { node.func.id}')

    ####
    ## Handling While loops (only variable OP variable)
    ####

    def visit_While(self, node):
        self.inLoop = True
        loop_id = self.__identify_while()
        inverted = {
            ast.Lt:     'BRGE', # '<'  in the code means we branch if '>=' 
            ast.LtE:    'BRGT', # '<=' in the code means we branch if '>' 
            ast.Gt:     'BRLE', # '>'  in the code means we branch if '<='
            ast.GtE:    'BRLT', # '>=' in the code means we branch if '<'
            ast.Eq:     'BRNE', # '==' in the code means we branch if '!='
            ast.NotEq:  'BREQ', # '!=' in the code means we branch if '=='
        }
        # left part can only be a variable
        self.__access_memory(node.test.left, 'LDWA', label = f'w_test_{loop_id}')
        # right part can only be a variable
        self.__access_memory(node.test.comparators[0], 'CPWA')
        # Branching is condition is not true (thus, inverted)
        self.__record_instruction(f'{inverted[type(node.test.ops[0])]} end_l_{loop_id}')
        # Visiting the body of the loop
        for contents in node.body:
            self.visit(contents)
        if(self.inFunctionDef):
            self.__record_instructionFunction(f'BR w_test_{loop_id}')
            self.__record_instructionFunction(f'NOP1', label = f'end_l_{loop_id}')
        else:
            self.__record_instruction(f'BR w_test_{loop_id}')
            # Sentinel marker for the end of the loop
            self.__record_instruction(f'NOP1', label = f'end_l_{loop_id}')

    ###
    ## Handling Conditional Branching (if, elif, else)
    ###

    def visit_If(self, node):
        branch_id = self.__identify_if()
        else_flag = False # flags next if as an else

        # flags first if in "if tree"
        is_root = False 
        if self.__in_if_tree == False:
            is_root = True
            self.__in_if_tree = True

        inverted = {
            ast.Lt:     'BRGE', # '<'  in the code means we branch if '>=' 
            ast.LtE:    'BRGT', # '<=' in the code means we branch if '>' 
            ast.Gt:     'BRLE', # '>'  in the code means we branch if '<='
            ast.GtE:    'BRLT', # '>=' in the code means we branch if '<'
            ast.Eq:     'BRNE', # '==' in the code means we branch if '!='
            ast.NotEq:  'BREQ', # '!=' in the code means we branch if '=='
        }
        # Sets up loop condition
        self.__access_memory(node.test.left, 'LDWA', label = f'test_if{branch_id}')
        self.__access_memory(node.test.comparators[0], 'CPWA')

        # If condition is false
        if len(node.orelse) > 0:
            # If next is an else
            if not isinstance(node.orelse[0], ast.If):
                else_flag = True
                if(self.inFunctionDef):
                    self.__record_instructionFunction(f'{inverted[type(node.test.ops[0])]} else{self.__if_tree_id}')
                else:
                    self.__record_instruction(f'{inverted[type(node.test.ops[0])]} else{self.__if_tree_id}')
            # If next is elif
            else:
                if(self.inFunctionDef):
                    self.__record_instructionFunction(f'{inverted[type(node.test.ops[0])]} test_if{branch_id+1}')
                else:
                    self.__record_instruction(f'{inverted[type(node.test.ops[0])]} test_if{branch_id+1}')
        # If lone if
        else:
            if(self.inFunctionDef):
                self.__record_instructionFunction(f'{inverted[type(node.test.ops[0])]} end_if{self.__if_tree_id}')
            else:
                self.__record_instruction(f'{inverted[type(node.test.ops[0])]} end_if{self.__if_tree_id}')
        
        # Visits body of if
        for contents in node.body:
            self.visit(contents)
        
        # Visits other ifs in if tree
        for contents in node.orelse:
            # print("contents: ", type(contents))
            if else_flag:
                if(self.inFunctionDef):
                    self.__record_instructionFunction('NOP1', label = f'else{self.__if_tree_id}')
                else:
                    self.__record_instruction('NOP1', label = f'else{self.__if_tree_id}')
                else_flag = False
            self.visit(contents)

        # Label for end of the if tree
        if is_root:
            if(self.inFunctionDef):
                self.__record_instruction(f'NOP1', label = f'end_if{self.__if_tree_id}')
            else:
                self.__record_instructionFunction(f'NOP1', label = f'end_if{self.__if_tree_id}')
            self.__if_tree_id += 1
            self.__in_if_tree = False


    ####
    ## Not handling function calls 
    ####

    def visit_FunctionDef(self, node):
        self.inFunctionDef = True
        func_name = node.name
        self.funcNames.append(func_name)
        self.__record_instructionFunction(f'SUBSP '+ str(self.numOfFuncVars*2)+",i", label = f'{func_name}')
        for content in node.body:

            self.visit(content)
        self.inFunctionDef = False
        
    def visit_Return(self, node):
        if(node.value.id in self.ret):
            self.__record_instructionFunction(f'LDWA '+ node.value.id+",s")
            self.__record_instructionFunction(f'STWA '+ self.ret[node.value.id][0]+",s")
        self.__record_instructionFunction(f'ADDSP '+ str(self.numOfFuncVars*2)+",i")
        self.__record_instructionFunction(f'RET ')



    ####
    ## Helper functions to 
    ####

    def __record_instruction(self, instruction, label = None):
        self.__instructions.append((label, instruction))
    
    def __record_instructionFunction(self, instruction, label = None):
        self.__instructionsFunc.append((label, instruction))


    def __access_memory(self, node, instruction, label = None):
        if isinstance(node, ast.Constant):
            if(self.inFunctionDef):
                self.__record_instructionFunction(f'{instruction} {node.value},i', label)
            else:
                self.__record_instruction(f'{instruction} {node.value},i', label)
        else:
            if(len(node.id) > 8):
                temp = self.global_symbols[node.id]
            else:
                temp = node.id
            if(node.id in self.constants):
                if(self.inFunctionDef):
                    if(temp in self.params):
                        temp = self.params[temp]
                    self.__record_instructionFunction(f'{instruction} {temp},i', label)
                else:
                    self.__record_instruction(f'{instruction} {temp},i', label)
            else:
                if(self.inFunctionDef):
                    if(temp in self.params):
                        temp = self.params[temp]
                    self.__record_instructionFunction(f'{instruction} {temp},s', label)
                else:
                    self.__record_instruction(f'{instruction} {temp},d', label)

    def __identify_if(self):
        result = self.__if_id
        self.__if_id = self.__if_id + 1
        return result
    
    def __identify_while(self):
        result = self.__loop_id
        self.__loop_id = self.__loop_id + 1
        return result