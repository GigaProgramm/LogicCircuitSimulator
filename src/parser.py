import json

class LogicCircuitParser:
    def __init__(self, circuit_data):
        self.circuit = circuit_data
        self.elements = {}
        self.connections = {}
        self.inputs = []
        self.outputs = []
        self.sorted_elements = []
        
    def parse(self):
        elements_sorted = sorted(self.circuit['elements'], key=lambda e: e['x'])
        
        for elem in elements_sorted:
            elem_id = f"{elem['type']}_{elem['x']}_{elem['y']}"
            self.elements[elem_id] = {
                'id': elem_id,
                'type': elem['type'],
                'x': elem['x'],
                'y': elem['y'],
                'inputs': [],
                'outputs': []
            }
            
            if elem['type'] == 'INPUT':
                self.inputs.append(elem_id)
            elif elem['type'] == 'OUTPUT':
                self.outputs.append(elem_id)
        
        for conn in self.circuit['connections']:
            start_elem = self._find_element_at_point(
                (conn['start'][0] + conn['start'][2]) / 2,
                (conn['start'][1] + conn['start'][3]) / 2
            )
            end_elem = self._find_element_at_point(
                (conn['end'][0] + conn['end'][2]) / 2,
                (conn['end'][1] + conn['end'][3]) / 2
            )
            
            if start_elem and end_elem:
                if end_elem not in self.connections:
                    self.connections[end_elem] = []
                self.connections[end_elem].append(start_elem)
                self.elements[start_elem]['outputs'].append(end_elem)
                self.elements[end_elem]['inputs'].append(start_elem)
        
        self._topological_sort()
        
        return self
    
    def _find_element_at_point(self, x, y, threshold=30):
        closest = None
        min_dist = float('inf')
        
        for elem_id, elem in self.elements.items():
            dist = ((elem['x'] - x) ** 2 + (elem['y'] - y) ** 2) ** 0.5
            if dist < min_dist and dist < threshold:
                min_dist = dist
                closest = elem_id
                
        return closest
    
    def _topological_sort(self):
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(elem_id):
            if elem_id in temp_visited:
                return
            if elem_id in visited:
                return
            
            temp_visited.add(elem_id)
            
            for input_elem in self.elements[elem_id]['inputs']:
                visit(input_elem)
            
            temp_visited.remove(elem_id)
            visited.add(elem_id)
            result.append(elem_id)
        
        for output_id in self.outputs:
            visit(output_id)
        
        for elem_id in self.elements:
            if elem_id not in visited:
                result.append(elem_id)
        
        self.sorted_elements = result
    
    def build_expression(self):
        if not self.sorted_elements:
            self.parse()
        
        expr_dict = {}
        input_names = {}
        for i, input_id in enumerate(sorted(self.inputs, key=lambda x: self.elements[x]['y'])):
            input_names[input_id] = chr(65 + i)
        
        for elem_id in reversed(self.sorted_elements):
            elem = self.elements[elem_id]
            
            if elem['type'] == 'INPUT':
                expr_dict[elem_id] = input_names[elem_id]
                
            elif elem['type'] == 'AND':
                inputs_expr = []
                for inp_id in elem['inputs']:
                    if inp_id in expr_dict:
                        inputs_expr.append(expr_dict[inp_id])
                    else:
                        inputs_expr.append(f"({inp_id})")
                
                if len(inputs_expr) == 1:
                    expr_dict[elem_id] = inputs_expr[0]
                elif len(inputs_expr) > 1:
                    if len(inputs_expr) == 2:
                        expr_dict[elem_id] = f"({inputs_expr[0]} ∧ {inputs_expr[1]})"
                    else:
                        inner = " ∧ ".join(inputs_expr)
                        expr_dict[elem_id] = f"({inner})"
                else:
                    expr_dict[elem_id] = "AND()"
                    
            elif elem['type'] == 'OR':
                inputs_expr = []
                for inp_id in elem['inputs']:
                    if inp_id in expr_dict:
                        inputs_expr.append(expr_dict[inp_id])
                    else:
                        inputs_expr.append(f"({inp_id})")
                
                if len(inputs_expr) == 1:
                    expr_dict[elem_id] = inputs_expr[0]
                elif len(inputs_expr) > 1:
                    if len(inputs_expr) == 2:
                        expr_dict[elem_id] = f"({inputs_expr[0]} ∨ {inputs_expr[1]})"
                    else:
                        inner = " ∨ ".join(inputs_expr)
                        expr_dict[elem_id] = f"({inner})"
                else:
                    expr_dict[elem_id] = "OR()"
                    
            elif elem['type'] == 'XOR':
                inputs_expr = []
                for inp_id in elem['inputs']:
                    if inp_id in expr_dict:
                        inputs_expr.append(expr_dict[inp_id])
                    else:
                        inputs_expr.append(f"({inp_id})")
                
                if len(inputs_expr) == 1:
                    expr_dict[elem_id] = inputs_expr[0]
                elif len(inputs_expr) == 2:
                    expr_dict[elem_id] = f"({inputs_expr[0]} ⊕ {inputs_expr[1]})"
                elif len(inputs_expr) > 2:
                    inner = " ⊕ ".join(inputs_expr)
                    expr_dict[elem_id] = f"({inner})"
                else:
                    expr_dict[elem_id] = "XOR()"
                    
            elif elem['type'] == 'NOT':
                inputs_expr = []
                for inp_id in elem['inputs']:
                    if inp_id in expr_dict:
                        inputs_expr.append(expr_dict[inp_id])
                    else:
                        inputs_expr.append(f"({inp_id})")
                
                if inputs_expr:
                    expr_dict[elem_id] = f"¬{inputs_expr[0]}"
                else:
                    expr_dict[elem_id] = "NOT()"
                    
            elif elem['type'] == 'OUTPUT':
                if elem['inputs']:
                    inp_id = elem['inputs'][0]
                    if inp_id in expr_dict:
                        expr_dict[elem_id] = expr_dict[inp_id]
                    else:
                        expr_dict[elem_id] = f"OUT({inp_id})"
                else:
                    expr_dict[elem_id] = "NO_INPUT"
        
        output_exprs = []
        for output_id in self.outputs:
            if output_id in expr_dict:
                output_name = f"O{self.outputs.index(output_id) + 1}"
                output_exprs.append(f"{output_name} = {expr_dict[output_id]}")
        
        if len(output_exprs) == 1:
            final_expr = output_exprs[0]
        else:
            final_expr = " ∧ ".join([f"({expr})" for expr in output_exprs])
        
        return {
            'full_expression': final_expr,
            'output_expressions': output_exprs,
            'element_expressions': expr_dict,
            'input_mapping': input_names
        }


class SimpleLogicParser:
    def __init__(self, circuit_data):
        self.circuit = circuit_data
        
    def parse_simple(self):
        inputs = []
        gates = {}
        outputs = []
        
        for elem in self.circuit['elements']:
            if elem['type'] == 'INPUT':
                inputs.append(elem)
            elif elem['type'] == 'OUTPUT':
                outputs.append(elem)
            else:
                gates[(elem['x'], elem['y'])] = elem
        
        inputs.sort(key=lambda e: e['y'])
        outputs.sort(key=lambda e: e['y'])
        
        input_names = [chr(65 + i) for i in range(len(inputs))]
        expressions = []
        
        for i, output in enumerate(outputs):
            output_name = f"O{i+1}"
            output_x, output_y = output['x'], output['y']
            
            connected_gate = None
            for conn in self.circuit['connections']:
                end_x = (conn['end'][0] + conn['end'][2]) / 2
                end_y = (conn['end'][1] + conn['end'][3]) / 2
                
                if abs(end_x - output_x) < 30 and abs(end_y - output_y) < 30:
                    start_x = (conn['start'][0] + conn['start'][2]) / 2
                    start_y = (conn['start'][1] + conn['start'][3]) / 2
                    
                    for gate_pos, gate in gates.items():
                        if abs(start_x - gate['x']) < 30 and abs(start_y - gate['y']) < 30:
                            connected_gate = gate
                            break
                    break
            
            if connected_gate:
                gate_type = connected_gate['type']
                gate_x, gate_y = connected_gate['x'], gate['y']
                
                gate_inputs = []
                for conn in self.circuit['connections']:
                    end_x = (conn['end'][0] + conn['end'][2]) / 2
                    end_y = (conn['end'][1] + conn['end'][3]) / 2
                    
                    if abs(end_x - gate_x) < 30 and abs(end_y - gate_y) < 30:
                        start_x = (conn['start'][0] + conn['start'][2]) / 2
                        start_y = (conn['start'][1] + conn['start'][3]) / 2
                        
                        found = False
                        for j, inp in enumerate(inputs):
                            if abs(start_x - inp['x']) < 30 and abs(start_y - inp['y']) < 30:
                                gate_inputs.append(input_names[j])
                                found = True
                                break
                        
                        if not found:
                            for gate_pos, other_gate in gates.items():
                                if (abs(start_x - other_gate['x']) < 30 and 
                                    abs(start_y - other_gate['y']) < 30):
                                    gate_inputs.append(f"G({other_gate['type']})")
                                    break
                
                if gate_type == 'AND':
                    if len(gate_inputs) >= 2:
                        expr = f"({' ∧ '.join(gate_inputs)})"
                    else:
                        expr = f"AND({', '.join(gate_inputs)})"
                elif gate_type == 'OR':
                    if len(gate_inputs) >= 2:
                        expr = f"({' ∨ '.join(gate_inputs)})"
                    else:
                        expr = f"OR({', '.join(gate_inputs)})"
                elif gate_type == 'XOR':
                    if len(gate_inputs) >= 2:
                        expr = f"({' ⊕ '.join(gate_inputs)})"
                    else:
                        expr = f"XOR({', '.join(gate_inputs)})"
                elif gate_type == 'NOT':
                    if gate_inputs:
                        expr = f"¬{gate_inputs[0]}"
                    else:
                        expr = "NOT()"
                
                expressions.append(f"{output_name} = {expr}")
            else:
                expressions.append(f"{output_name} = NO_CONNECTION")
        
        if expressions:
            final_expr = " ∧ ".join([f"({expr})" for expr in expressions])
        else:
            final_expr = "NO_EXPRESSIONS"
        
        return {
            'expression': final_expr,
            'outputs': expressions,
            'inputs': input_names
        }


def main():
    circuit_data = {
        "elements": [
            {"type": "AND", "x": 371, "y": 156},
            {"type": "OR", "x": 371, "y": 225},
            {"type": "NOT", "x": 369, "y": 289},
            {"type": "XOR", "x": 370, "y": 353},
            {"type": "INPUT", "x": 239, "y": 303},
            {"type": "INPUT", "x": 242, "y": 258},
            {"type": "INPUT", "x": 242, "y": 211},
            {"type": "INPUT", "x": 244, "y": 153},
            {"type": "INPUT", "x": 246, "y": 110},
            {"type": "INPUT", "x": 241, "y": 405},
            {"type": "INPUT", "x": 241, "y": 352},
            {"type": "OUTPUT", "x": 470, "y": 350},
            {"type": "OUTPUT", "x": 476, "y": 288},
            {"type": "OUTPUT", "x": 471, "y": 226},
            {"type": "OUTPUT", "x": 461, "y": 151}
        ],
        "connections": [
            {"start": [281.0, 125.0, 291.0, 135.0], "end": [366.0, 161.0, 376.0, 171.0]},
            {"start": [279.0, 168.0, 289.0, 178.0], "end": [366.0, 181.0, 376.0, 191.0]},
            {"start": [277.0, 226.0, 287.0, 236.0], "end": [366.0, 230.0, 376.0, 240.0]},
            {"start": [277.0, 273.0, 287.0, 283.0], "end": [366.0, 250.0, 376.0, 260.0]},
            {"start": [274.0, 318.0, 284.0, 328.0], "end": [364.0, 304.0, 374.0, 314.0]},
            {"start": [276.0, 367.0, 286.0, 377.0], "end": [365.0, 358.0, 375.0, 368.0]},
            {"start": [276.0, 420.0, 286.0, 430.0], "end": [365.0, 378.0, 375.0, 388.0]},
            {"start": [405.0, 368.0, 415.0, 378.0], "end": [465.0, 365.0, 475.0, 375.0]},
            {"start": [405.0, 304.0, 414.0, 314.0], "end": [471.0, 303.0, 481.0, 313.0]},
            {"start": [406.0, 240.0, 416.0, 250.0], "end": [466.0, 241.0, 476.0, 251.0]},
            {"start": [406.0, 171.0, 416.0, 181.0], "end": [456.0, 166.0, 466.0, 176.0]}
        ]
    }
    
    print("=== Анализ логической схемы ===\n")
    
    parser = SimpleLogicParser(circuit_data)
    result = parser.parse_simple()
    
    print("Входы (сверху вниз):")
    for i, inp_name in enumerate(result['inputs']):
        print(f"  {inp_name}: Вход {i+1}")
    
    print("\nВыражения для выходов:")
    for expr in result['outputs']:
        print(f"  {expr}")
    
    print("\n" + "="*60)
    print("ИТОГОВОЕ ВЫРАЖЕНИЕ:")
    print("="*60)
    print(result['expression'])
    print("="*60)
    
    print("\nАльтернативное представление (с использованием &, |, ~, ^):")
    
    alt_expr = result['expression']
    alt_expr = alt_expr.replace('∧', '&').replace('∨', '|').replace('¬', '~').replace('⊕', '^')
    print(alt_expr)
    
    print("\n" + "="*60)
    print("Восстановленная структура (на основе координат):")
    print("="*60)
    
    elements_by_x = {}
    for elem in circuit_data['elements']:
        x_pos = elem['x']
        if x_pos not in elements_by_x:
            elements_by_x[x_pos] = []
        elements_by_x[x_pos].append(elem)
    
    for x_pos in sorted(elements_by_x.keys()):
        elements = sorted(elements_by_x[x_pos], key=lambda e: e['y'])
        print(f"\nX ≈ {x_pos}:")
        for elem in elements:
            print(f"  {elem['type']} (y={elem['y']})")


if __name__ == "__main__":
    main()