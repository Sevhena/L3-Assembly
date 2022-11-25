
class StaticMemoryAllocation():

    def __init__(self, global_vars: dict()) -> None:
        self.__global_vars = global_vars
        self.symbols = {}
        self.constants = []

    def generate(self):
        print('; Allocating Global (static) memory')
        for n in self.__global_vars:
            if(len(n) >8):
                if(n not in self.symbols):
                    self.symbols[n] = "var"+ str(len(self.symbols))

            if(n in self.symbols):
                temp = self.symbols[n]
            else:
                temp = n
                
            if(self.__global_vars[n] == "<class 'ast.Call'>" or self.__global_vars[n] == "<class 'ast.BinOp'>" or self.__global_vars[n] == "<class 'ast.Name'>" ):
                print(f'{str(temp+":"):<9}\t.BLOCK 2')
            elif(self.__global_vars[n][0] == "<class 'ast.Constant'>" and n[0] == '_'):
                self.constants.append(n)
                print(f'{str(temp+":"):<9}\t.EQUATE ' + str(self.__global_vars[n][1]))
            elif(self.__global_vars[n][0] == "<class 'ast.Constant'>"):
                print(f'{str(temp+":"):<9}\t.WORD '+ str(self.__global_vars[n][1]))
        return (self.symbols,self.constants)

