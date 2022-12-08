import ast

class StaticMemoryAllocation():

    def __init__(self, vars: dict(),function,params,ret) -> None:
        self.function = function
        self.params = params
        self.ret = ret
        if(function):
            self.func_vars = vars
        else:
            self.__global_vars = vars
        self.symbols_global = {}
        self.symbols_func = {}
        self.memory = 0
        self.constants = []


    def generate(self):
        if(self.function):
            print('; Allocating Function memory')
            for n in self.func_vars:
                if len(n) > 8:
                    if n not in self.symbols_func:
                        self.symbols_func[n] = "var" + str(len(self.symbols_func))

                if n in self.symbols_func :
                    temp = self.symbols_func[n]
                else:
                    temp = n
                print(f'{str(temp+":"):<9}\t.EQUATE ' + str(self.memory))
                self.memory+=2

            self.memory+=2
            if(len(self.params) >0):
                for para in self.params:
                    print(f'{str(self.params[para][0]+":"):<9}\t.EQUATE ' + str(self.memory))
                    self.memory+=2
            if(len(self.ret)>0):
                for ret in self.ret:
                    if(self.ret[ret][1] == False):
                        print(f'{str(self.ret[ret][0]+":"):<9}\t.EQUATE ' + str(self.memory))
                        self.memory+=2
            numOfFunVars = self.calculateVars(self.func_vars)
            return (self.symbols_func,numOfFunVars)
        else:
            print('; Allocating Global (static) memory')
            accepted = False
            for n in self.__global_vars:
                if(len(n) >8):
                    if(n not in self.symbols_global):
                        self.symbols_global[n] = "var"+ str(len(self.symbols_global))

                if(n in self.symbols_global):
                    temp = self.symbols_global[n]
                else:
                    temp = n
                glob_var = self.__global_vars[n]
                if isinstance(glob_var, (ast.Call, ast.BinOp, ast.Name)):
                    for i in self.ret:
                        if(temp in self.ret[i]):
                            print(f'{str(self.ret[i][0]+":"):<9}\t.BLOCK 2')
                            accepted = True
                    if(not accepted):
                        print(f'{str(temp + ":"):<9}\t.BLOCK 2')
                elif isinstance(glob_var[0], ast.Constant) and n[0] == '_':
                    self.constants.append(n)
                    print(f'{str(temp + ":"):<9}\t.EQUATE ' + str(glob_var[1]))
                elif isinstance(glob_var[0], ast.Constant):
                    print(f'{str(temp + ":"):<9}\t.WORD ' + str(glob_var[1]))
            return (self.symbols_global, self.constants)

    def calculateVars(self,func_vars):
        counts = {}
        for var in func_vars:
            if(len(func_vars[var]) == 2):
                if(func_vars[var][1] in counts):
                    counts[func_vars[var][1]] +=1
                else:
                    counts[func_vars[var][1]] = 1
            else:
                if(func_vars[var][2] in counts):
                    counts[func_vars[var][2]] +=1
                else:
                    counts[func_vars[var][2]] = 1
        return counts