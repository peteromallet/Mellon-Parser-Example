import ast
import json
from pathlib import Path
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)

class PythonClassParser:
    def __init__(self):
        self.current_class = None
    
    def parse_value(self, node: ast.AST) -> Any:
        """Convert AST nodes to Python values without executing code."""
        try:
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Dict):
                result_dict = {}
                for k, v in zip(node.keys, node.values):
                    try:
                        key = self.parse_value(k)
                        val = self.parse_value(v)
                        result_dict[key] = val
                    except Exception as inner_ex:
                        logging.error(f"Error parsing dict element: {inner_ex}")
                        result_dict[str(k)] = "<parse_error>"
                return result_dict
            elif isinstance(node, ast.List):
                return [self.parse_value(elem) for elem in node.elts]
            elif isinstance(node, ast.Tuple):
                return tuple(self.parse_value(elem) for elem in node.elts)
            elif isinstance(node, ast.Set):
                return {self.parse_value(elem) for elem in node.elts}
            elif isinstance(node, ast.Name):
                if node.id == 'True':
                    return True
                elif node.id == 'False':
                    return False
                elif node.id == 'None':
                    return None
                return node.id
            elif isinstance(node, ast.Str):
                return node.s
            elif isinstance(node, (ast.Num, ast.Bytes)):
                return node.n
            else:
                try:
                    return ast.unparse(node)
                except Exception as unparse_ex:
                    logging.error(f"Unsupported node type with unparse error: {unparse_ex}")
                    return "<unparse_error>"
        except Exception as e:
            logging.error(f"Error parsing AST node: {e}")
            return "<error>"
    
    def extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract information from a class definition."""
        class_info = {
            'name': node.name,
            'bases': [],
            'docstring': None,
            'attributes': {},
            'methods': [],
            'decorators': [],
            'parsing_errors': []
        }
        # Process bases robustly
        for base in node.bases:
            try:
                base_str = ast.unparse(base)
                class_info['bases'].append(base_str)
            except Exception as ex:
                logging.error(f"Error parsing base class in {node.name}: {ex}")
                class_info['parsing_errors'].append(f"Error parsing base class: {ex}")
        
        try:
            class_info['docstring'] = ast.get_docstring(node)
        except Exception as ex_doc:
            logging.error(f"Error getting docstring for class {node.name}: {ex_doc}")
            class_info['parsing_errors'].append(f"Docstring parse error: {ex_doc}")
        
        try:
            class_info['decorators'] = [ast.unparse(dec) for dec in node.decorator_list]
        except Exception as ex_dec:
            logging.error(f"Error parsing decorators for class {node.name}: {ex_dec}")
            class_info['parsing_errors'].append(f"Decorator parse error: {ex_dec}")
        
        for item in node.body:
            try:
                if isinstance(item, ast.Assign):
                    # Handle class attributes
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            class_info['attributes'][target.id] = self.parse_value(item.value)
                elif isinstance(item, ast.AnnAssign) and item.value:
                    # Handle type-annotated attributes
                    if isinstance(item.target, ast.Name):
                        attr_value = self.parse_value(item.value)
                        try:
                            attr_type = ast.unparse(item.annotation)
                        except Exception as type_ex:
                            logging.error(f"Error parsing annotation for attribute {item.target.id} in class {node.name}: {type_ex}")
                            attr_type = "<annotation_error>"
                            class_info['parsing_errors'].append(f"Annotation error in attribute {item.target.id}: {type_ex}")
                        class_info['attributes'][item.target.id] = {
                            'value': attr_value,
                            'type': attr_type
                        }
                elif isinstance(item, ast.FunctionDef):
                    # Extract method information robustly
                    method_info = {
                        'name': item.name,
                        'decorators': [],
                        'docstring': None,
                        'args': {},
                        'return_type': None
                    }
                    try:
                        method_info['decorators'] = [ast.unparse(dec) for dec in item.decorator_list]
                    except Exception as dec_ex:
                        logging.error(f"Error parsing decorators for method {item.name} in class {node.name}: {dec_ex}")
                        method_info['decorators'] = ["<decorator_error>"]
                        class_info['parsing_errors'].append(f"Decorator error in method {item.name}: {dec_ex}")
                    try:
                        method_info['docstring'] = ast.get_docstring(item)
                    except Exception as doc_ex:
                        logging.error(f"Error getting docstring for method {item.name} in class {node.name}: {doc_ex}")
                        method_info['docstring'] = "<doc_error>"
                        class_info['parsing_errors'].append(f"Docstring error in method {item.name}: {doc_ex}")
                    try:
                        method_info['args'] = self._extract_arguments(item.args)
                    except Exception as arg_ex:
                        logging.error(f"Error extracting arguments for method {item.name} in class {node.name}: {arg_ex}")
                        method_info['args'] = {}
                        class_info['parsing_errors'].append(f"Arguments error in method {item.name}: {arg_ex}")
                    try:
                        if item.returns:
                            method_info['return_type'] = ast.unparse(item.returns)
                    except Exception as ret_ex:
                        logging.error(f"Error parsing return type for method {item.name} in class {node.name}: {ret_ex}")
                        method_info['return_type'] = "<return_type_error>"
                        class_info['parsing_errors'].append(f"Return type error in method {item.name}: {ret_ex}")
                    class_info['methods'].append(method_info)
            except Exception as item_ex:
                error_message = f"Error processing item in class {node.name}: {item_ex}"
                logging.error(error_message)
                class_info['parsing_errors'].append(error_message)
        return class_info
    
    def _extract_arguments(self, args: ast.arguments) -> Dict[str, Any]:
        """Extract argument information from a function definition."""
        arguments = {
            'args': [],
            'defaults': [],
            'kwonly_args': [],
            'kwonly_defaults': [],
            'vararg': None,
            'kwarg': None,
        }
        
        try:
            for arg in args.args:
                arg_info = {
                    'name': arg.arg,
                    'annotation': ast.unparse(arg.annotation) if arg.annotation else None
                }
                arguments['args'].append(arg_info)
        except Exception as e_args:
            logging.error(f"Error processing regular arguments: {e_args}")
        
        try:
            defaults_start = len(args.args) - len(args.defaults)
            for i, default in enumerate(args.defaults):
                try:
                    arguments['defaults'].append({
                        'arg': args.args[defaults_start + i].arg,
                        'value': self.parse_value(default)
                    })
                except Exception as def_ex:
                    logging.error(f"Error processing default value for argument {args.args[defaults_start + i].arg}: {def_ex}")
                    arguments['defaults'].append({
                        'arg': args.args[defaults_start + i].arg,
                        'value': "<default_parse_error>"
                    })
        except Exception as def_total_ex:
            logging.error(f"Error processing default arguments: {def_total_ex}")
        
        try:
            for kw in args.kwonlyargs:
                kw_info = {
                    'name': kw.arg,
                    'annotation': ast.unparse(kw.annotation) if kw.annotation else None
                }
                arguments['kwonly_args'].append(kw_info)
            for default in args.kw_defaults:
                try:
                    arguments['kwonly_defaults'].append(self.parse_value(default) if default is not None else None)
                except Exception as kwdef_ex:
                    logging.error(f"Error processing kw default: {kwdef_ex}")
                    arguments['kwonly_defaults'].append("<kw_default_error>")
        except Exception as kw_ex:
            logging.error(f"Error processing kwonly arguments: {kw_ex}")
        
        if args.vararg:
            try:
                arguments['vararg'] = args.vararg.arg
            except Exception as var_ex:
                logging.error(f"Error processing vararg: {var_ex}")
                arguments['vararg'] = "<vararg_error>"
        if args.kwarg:
            try:
                arguments['kwarg'] = args.kwarg.arg
            except Exception as kwarg_ex:
                logging.error(f"Error processing kwarg: {kwarg_ex}")
                arguments['kwarg'] = "<kwarg_error>"
        
        return arguments

class PythonFolderParser:
    def __init__(self, base_paths: List[str]):
        self.base_paths = base_paths
        self.parser = PythonClassParser()
        
    def scan_folders(self) -> Dict[str, Any]:
        """Scan folders for Python files and extract class information."""
        results = {
            'scanned_folders': self.base_paths,
            'files': [],
            'classes': [],
            'errors': []
        }
        
        for base_path in self.base_paths:
            path = Path(base_path)
            if not path.exists():
                error_msg = f"Folder does not exist: {base_path}"
                results['errors'].append({
                    'folder': str(path),
                    'error': error_msg
                })
                logging.error(error_msg)
                continue
                
            for python_file in path.rglob('*.py'):
                try:
                    file_results = self.parse_file(python_file)
                    if file_results.get('classes'):
                        results['files'].append(str(python_file))
                        results['classes'].extend(file_results['classes'])
                    if file_results.get('errors'):
                        for error in file_results['errors']:
                            if "Syntax error" in error.get("error", ""):
                                logging.info(f"Skipping syntax error error from file {python_file}")
                            else:
                                results['errors'].append(error)
                except Exception as e:
                    error_detail = f"Error parsing file {python_file}: {e}"
                    results['errors'].append({
                        'file': str(python_file),
                        'error': error_detail
                    })
                    logging.error(error_detail)
        
        return results
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single Python file and extract class information."""
        results = {
            'classes': [],
            'errors': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as read_ex:
            error_msg = f"Error reading file {file_path}: {read_ex}"
            results['errors'].append({
                'file': str(file_path),
                'error': error_msg
            })
            logging.error(error_msg)
            return results
        
        try:
            tree = ast.parse(content)
        except SyntaxError as syn_ex:
            error_msg = f"Syntax error in file {file_path}: {syn_ex}"
            logging.error(error_msg)
            # Return an empty result to skip invalid files, with a consistent structure
            return {'classes': [], 'errors': []}
        except Exception as parse_ex:
            error_msg = f"Error parsing AST in file {file_path}: {parse_ex}"
            results['errors'].append({
                'file': str(file_path),
                'error': error_msg
            })
            logging.error(error_msg)
            return results
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                try:
                    class_info = self.parser.extract_class_info(node)
                    class_info['file'] = str(file_path)
                    results['classes'].append(class_info)
                except Exception as ex:
                    error_detail = f"Error extracting class {node.name} in file {file_path}: {ex}"
                    results['errors'].append({
                        'file': str(file_path),
                        'class': node.name,
                        'error': error_detail
                    })
                    logging.error(error_detail)
                        
        return results

def parse_folders(folders: List[str]) -> str:
    """Parse folders and return JSON string of results."""
    parser = PythonFolderParser(folders)
    results = parser.scan_folders()
    return json.dumps(results, indent=2)

if __name__ == '__main__':
    # Iterate through the python files inside the "custom" folder
    folders = ['./tests']
    results = parse_folders(folders)
    
    try:
        parsed_results = json.loads(results)
    except json.JSONDecodeError as json_ex:
        logging.error(f"JSON parsing error: {json_ex}")
        parsed_results = {}
    
    # Group classes by filename
    files_dict = {}
    for cls in parsed_results.get('classes', []):
        file_name = cls.get('file', 'Unknown file')
        files_dict.setdefault(file_name, []).append(cls)
    
    # Iterate over each file and print its classes and parameters in the desired format.
    try:
        for file_name, classes in files_dict.items():
            print(f"---\n{file_name}\n---")
            for cls in classes:
                print(f"--{cls.get('name')}")
                params = cls.get('attributes', {}).get('params')
                if isinstance(params, dict):
                    for param_name, details in params.items():
                        print(f"    --{param_name}--")
                        if isinstance(details, dict):
                            for key, value in details.items():
                                print(f"        --{key} | {value}")
            print()  # Blank line between file groups
    except Exception as print_ex:
        logging.error(f"Error printing class information: {print_ex}")
    
    # Log parsing errors if any
    if parsed_results.get('errors'):
        print("-- Errors encountered during parsing --")
        for error in parsed_results.get('errors'):
            logging.error(error)
            print(error)