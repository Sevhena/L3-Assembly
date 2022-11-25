import ast

class StaticMemoryAllocation():

    def __init__(self, global_vars: dict()) -> None:
        self.__global_vars = global_vars
        self.symbols = {}
        self.constants = []

    def generate(self):
        print('; Allocating Global (static) memory')
        for n in self.__global_vars:
            if len(n) > 8:
                if n not in self.symbols:
                    self.symbols[n] = "var" + str(len(self.symbols))

            if n in self.symbols :
                temp = self.symbols[n]
            else:
                temp = n
                
            glob_var = self.__global_vars[n]
            if isinstance(glob_var, (ast.Call, ast.BinOp, ast.Name)):
                print(f'{str(temp + ":"):<9}\t.BLOCK 2')
            elif isinstance(glob_var[0], ast.Constant) and n[0] == '_':
                self.constants.append(n)
                print(f'{str(temp + ":"):<9}\t.EQUATE ' + str(glob_var[1]))
            elif isinstance(glob_var[0], ast.Constant):
                print(f'{str(temp + ":"):<9}\t.WORD ' + str(glob_var[1]))
        return (self.symbols, self.constants)

