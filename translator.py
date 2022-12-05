import argparse
import ast
from visitors.GlobalVariables import GlobalVariableExtraction
from visitors.TopLevelProgram import TopLevelProgram
from generators.StaticMemoryAllocation import StaticMemoryAllocation
from generators.EntryPoint import EntryPoint

def main():
    input_file, print_ast = process_cli()
    with open(input_file) as f:
        source = f.read()
    node = ast.parse(source)
    print("========================================")
    print("=======================================")
    print(ast.dump(node, indent=2))
    print("========================================")
    print("========================================")
    if print_ast:
        print(ast.dump(node, indent=2))
    else:
        process(input_file, node)

    
    
    
def process_cli():
    """"Process Command Line Interface options"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', help='filename to compile (.py)')
    parser.add_argument('--ast-only', default=False, action='store_true')
    args = vars(parser.parse_args())
    return args['f'], args['ast_only']

def process(input_file, root_node):
    print(f'; Translating {input_file}')
    # print("root node: ", root_node)
    extractor = GlobalVariableExtraction()
    extractor.visit(root_node)
    #allocate memory for global vars
    memory_alloc = StaticMemoryAllocation(extractor.results,False,extractor.params,extractor.ret)
    #allocate memory for function vars and paramters and return value
    memory_alloc2 = StaticMemoryAllocation(extractor.func_results,True,extractor.params,extractor.ret)
    print('; Branching to top level (tl) instructions')
    print('\t\tBR tl')
    global_symbols,global_constants = memory_alloc.generate()
    func_symbols,numOfFuncVars = memory_alloc2.generate()

    top_level = TopLevelProgram('tl',global_symbols,global_constants,func_symbols,numOfFuncVars,extractor.params,extractor.ret)
    top_level.visit(root_node)
    ep = EntryPoint(top_level.finalize())
    ep.generate() 

if __name__ == '__main__':
    main()
