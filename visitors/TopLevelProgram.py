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
        self.__loop_id = 0 # Counts loops in program
        self.__if_id = 0 # Counts ifs in program
        self.__if_tree_id = 0 # Counts if trees in program
        self.__in_if_tree = False
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

    def visit_BinOp(self, node): #Binary Operation
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
            # print(type(node.orelse[0]))
            if not isinstance(node.orelse[0], ast.If):
                else_flag = True
                self.__record_instruction(f'{inverted[type(node.test.ops[0])]} else{self.__if_tree_id}')
            # If next is elif
            else:
                self.__record_instruction(f'{inverted[type(node.test.ops[0])]} test_if{branch_id+1}')
        # If lone if
        else:
            self.__record_instruction(f'{inverted[type(node.test.ops[0])]} end_if{self.__if_tree_id}')
        
        # Visits body of if
        for contents in node.body:
            self.visit(contents)

        # Branch to continuation of main program
        self.__record_instruction(f'BR end_if{self.__if_tree_id}')
        
        # Visits other ifs in if tree
        for contents in node.orelse:
            # print("contents: ", type(contents))
            if else_flag:
                self.__record_instruction('NOP1', label = f'else{self.__if_tree_id}')
                else_flag = False
            self.visit(contents)

        # Label for end of the if tree
        if is_root:
            self.__record_instruction(f'NOP1', label = f'end_if{self.__if_tree_id}')
            self.__if_tree_id += 1
            self.__in_if_tree = False


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

    def __identify_if(self):
        result = self.__if_id
        self.__if_id = self.__if_id + 1
        return result
    
    def __identify_while(self):
        result = self.__loop_id
        self.__loop_id = self.__loop_id + 1
        return result