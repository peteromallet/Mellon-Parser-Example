import ast
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)


class NodeBase:
    """Base class for all nodes in the system."""
    label: str = "Base"
    description: str = "Base node class"
    category: str = "base"
    execution_type: str = "none"

    # Default empty params dictionary
    params: Dict[str, Dict[str, Any]] = {}

    def execute(self, *args, **kwargs) -> Any:
        """Base execute method that should be overridden by child classes."""
        raise NotImplementedError("Execute method must be implemented by child class")


class PythonClassParser:
    def __init__(self) -> None:
        """Initialize any stateful variables, if needed."""
        self.current_class: Optional[Dict[str, Any]] = None

    def parse_value(self, node: ast.AST) -> Any:
        """
        Convert AST nodes to Python values without executing code.

        Returns a Python representation of the AST node or a placeholder string
        (e.g. "<error>") on failure.
        """
        if isinstance(node, ast.Constant):
            # Python 3.8+ uses ast.Constant
            return node.value
        elif isinstance(node, ast.Dict):
            result_dict = {}
            for k, v in zip(node.keys, node.values):
                key = self._safe_parse(k, "<parse_error_key>")
                val = self._safe_parse(v, "<parse_error_val>")
                result_dict[key] = val
            return result_dict
        elif isinstance(node, ast.List):
            return [self._safe_parse(elem, "<parse_error_elem>") for elem in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._safe_parse(elem, "<parse_error_elem>") for elem in node.elts)
        elif isinstance(node, ast.Set):
            return {self._safe_parse(elem, "<parse_error_elem>") for elem in node.elts}
        elif isinstance(node, ast.Name):
            if node.id == 'True':
                return True
            elif node.id == 'False':
                return False
            elif node.id == 'None':
                return None
            return node.id
        elif isinstance(node, ast.Str):
            # For Python < 3.8 (older code), these might be ast.Str instead of ast.Constant
            return node.s
        elif isinstance(node, (ast.Num, ast.Bytes)):
            # For Python < 3.8, numeric/bytes might appear in ast.Num or ast.Bytes
            return node.n
        else:
            return self._unparse_with_fallback(node)

    def _safe_parse(self, node: ast.AST, fallback: str) -> Any:
        """Helper to parse a node with a fallback on any exception."""
        try:
            return self.parse_value(node)
        except Exception as e:
            logging.error(f"Error parsing AST node {node}: {e}")
            return fallback

    def _unparse_with_fallback(self, node: ast.AST) -> str:
        """Attempt to unparse the node, return a fallback string if that fails."""
        try:
            return ast.unparse(node)
        except Exception as unparse_ex:
            logging.error(f"Unsupported node type or unparse error: {unparse_ex}")
            return "<unparse_error>"

    def extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract information from a class definition AST node."""
        class_info = {
            'name': node.name,
            'bases': [],
            'docstring': None,
            'attributes': {},
            'methods': [],
            'decorators': [],
            'parsing_errors': []
        }

        # Process base classes
        for base in node.bases:
            try:
                base_str = ast.unparse(base)
                class_info['bases'].append(base_str)
            except Exception as ex:
                msg = f"Error parsing base class in {node.name}: {ex}"
                logging.error(msg)
                class_info['parsing_errors'].append(msg)

        # Docstring extraction
        try:
            class_info['docstring'] = ast.get_docstring(node)
        except Exception as ex_doc:
            msg = f"Error getting docstring for class {node.name}: {ex_doc}"
            logging.error(msg)
            class_info['parsing_errors'].append(msg)

        # Decorators
        try:
            for dec in node.decorator_list:
                class_info['decorators'].append(self._unparse_with_fallback(dec))
        except Exception as ex_dec:
            msg = f"Error parsing decorators for class {node.name}: {ex_dec}"
            logging.error(msg)
            class_info['parsing_errors'].append(msg)

        # Body (attributes, methods, etc.)
        for item in node.body:
            try:
                self._process_class_item(node.name, item, class_info)
            except Exception as item_ex:
                msg = f"Error processing item in class {node.name}: {item_ex}"
                logging.error(msg)
                class_info['parsing_errors'].append(msg)

        return class_info

    def _process_class_item(self, class_name: str, item: ast.AST, class_info: Dict[str, Any]) -> None:
        """Process a single AST node inside a class definition."""
        # Handle class-level attributes
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    parsed_value = self.parse_value(item.value)
                    class_info['attributes'][target.id] = parsed_value

        elif isinstance(item, ast.AnnAssign) and item.value:
            if isinstance(item.target, ast.Name):
                attr_value = self.parse_value(item.value)
                try:
                    attr_type = ast.unparse(item.annotation)
                except Exception as type_ex:
                    logging.error(f"Error parsing annotation for attribute {item.target.id}"
                                  f" in class {class_name}: {type_ex}")
                    attr_type = "<annotation_error>"
                    class_info['parsing_errors'].append(
                        f"Annotation error in attribute {item.target.id}: {type_ex}"
                    )
                class_info['attributes'][item.target.id] = {
                    'value': attr_value,
                    'type': attr_type
                }

        # Handle methods
        elif isinstance(item, ast.FunctionDef):
            method_info = {
                'name': item.name,
                'decorators': [],
                'docstring': None,
                'args': {},
                'return_type': None
            }
            # Decorators
            try:
                for dec in item.decorator_list:
                    method_info['decorators'].append(self._unparse_with_fallback(dec))
            except Exception as dec_ex:
                logging.error(f"Error parsing decorators for method {item.name} in class {class_name}: {dec_ex}")
                method_info['decorators'] = ["<decorator_error>"]
                class_info['parsing_errors'].append(f"Decorator error in method {item.name}: {dec_ex}")

            # Docstring
            try:
                method_info['docstring'] = ast.get_docstring(item)
            except Exception as doc_ex:
                logging.error(f"Error getting docstring for method {item.name} in class {class_name}: {doc_ex}")
                method_info['docstring'] = "<doc_error>"
                class_info['parsing_errors'].append(f"Docstring error in method {item.name}: {doc_ex}")

            # Arguments
            try:
                method_info['args'] = self._extract_arguments(item.args)
            except Exception as arg_ex:
                logging.error(f"Error extracting arguments for method {item.name} in class {class_name}: {arg_ex}")
                method_info['args'] = {}
                class_info['parsing_errors'].append(f"Arguments error in method {item.name}: {arg_ex}")

            # Return type
            if item.returns:
                try:
                    method_info['return_type'] = ast.unparse(item.returns)
                except Exception as ret_ex:
                    logging.error(f"Error parsing return type for method {item.name} in class {class_name}: {ret_ex}")
                    method_info['return_type'] = "<return_type_error>"
                    class_info['parsing_errors'].append(f"Return type error in method {item.name}: {ret_ex}")

            class_info['methods'].append(method_info)

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

        # Positional arguments
        for arg in args.args:
            arg_info = {
                'name': arg.arg,
                'annotation': None
            }
            if arg.annotation:
                try:
                    arg_info['annotation'] = ast.unparse(arg.annotation)
                except Exception as e_args:
                    logging.error(f"Error processing annotation for arg {arg.arg}: {e_args}")
                    arg_info['annotation'] = "<annotation_error>"
            arguments['args'].append(arg_info)

        # Defaults
        try:
            defaults_start = len(args.args) - len(args.defaults)
            for i, default in enumerate(args.defaults):
                arg_name = args.args[defaults_start + i].arg
                parsed_def = self._safe_parse(default, "<default_parse_error>")
                arguments['defaults'].append({'arg': arg_name, 'value': parsed_def})
        except Exception as def_ex:
            logging.error(f"Error processing default arguments: {def_ex}")

        # Keyword-only arguments & defaults
        try:
            for kw in args.kwonlyargs:
                kw_info = {
                    'name': kw.arg,
                    'annotation': None
                }
                if kw.annotation:
                    try:
                        kw_info['annotation'] = ast.unparse(kw.annotation)
                    except Exception as kw_ex:
                        logging.error(f"Error processing kwonly annotation for arg {kw.arg}: {kw_ex}")
                        kw_info['annotation'] = "<annotation_error>"
                arguments['kwonly_args'].append(kw_info)

            for default in args.kw_defaults:
                if default is None:
                    arguments['kwonly_defaults'].append(None)
                else:
                    arguments['kwonly_defaults'].append(self._safe_parse(default, "<kw_default_error>"))
        except Exception as kw_ex:
            logging.error(f"Error processing kwonly arguments: {kw_ex}")

        # *args
        if args.vararg:
            try:
                arguments['vararg'] = args.vararg.arg
            except Exception as var_ex:
                logging.error(f"Error processing vararg: {var_ex}")
                arguments['vararg'] = "<vararg_error>"

        # **kwargs
        if args.kwarg:
            try:
                arguments['kwarg'] = args.kwarg.arg
            except Exception as kwarg_ex:
                logging.error(f"Error processing kwarg: {kwarg_ex}")
                arguments['kwarg'] = "<kwarg_error>"

        return arguments


class PythonFolderParser:
    def __init__(self, base_paths: List[str]) -> None:
        self.base_paths = base_paths
        self.parser = PythonClassParser()

    def scan_folders(self) -> Dict[str, Any]:
        """
        Scan folders for Python files and extract class information.

        Returns a dictionary with keys:
          - 'scanned_folders': List of folders scanned
          - 'files': List of files that contained matching classes
          - 'classes': Combined class info from all files
          - 'errors': Any collected error information
        """
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
                results['errors'].append({'folder': str(path), 'error': error_msg})
                logging.error(error_msg)
                continue

            for python_file in path.rglob('*.py'):
                file_results = self.parse_file(python_file)
                # Merge file results
                if file_results.get('classes'):
                    results['files'].append(str(python_file))
                    results['classes'].extend(file_results['classes'])
                if file_results.get('errors'):
                    for err in file_results['errors']:
                        # Example: optionally skip certain errors
                        if "Syntax error" in err.get("error", ""):
                            logging.info(f"Skipping syntax error from file {python_file}")
                        else:
                            results['errors'].append(err)

        return results

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single Python file and extract class information."""
        results = {'classes': [], 'errors': []}

        try:
            with file_path.open('r', encoding='utf-8') as f:
                content = f.read()
        except Exception as read_ex:
            error_msg = f"Error reading file {file_path}: {read_ex}"
            results['errors'].append({'file': str(file_path), 'error': error_msg})
            logging.error(error_msg)
            return results

        try:
            tree = ast.parse(content)
        except SyntaxError as syn_ex:
            error_msg = f"Syntax error in file {file_path}: {syn_ex}"
            results['errors'].append({'file': str(file_path), 'error': error_msg})
            logging.error(error_msg)
            return results
        except Exception as parse_ex:
            error_msg = f"Error parsing AST in file {file_path}: {parse_ex}"
            results['errors'].append({'file': str(file_path), 'error': error_msg})
            logging.error(error_msg)
            return results

        # Walk the AST, collecting classes that inherit NodeBase
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                try:
                    class_info = self.parser.extract_class_info(node)
                    # Check if NodeBase is in the base classes
                    if not any("NodeBase" in base for base in class_info.get('bases', [])):
                        continue
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
    """
    Parse folders and return a JSON string of the results:
      {
        "scanned_folders": [...],
        "files": [...],
        "classes": [...],
        "errors": [...]
      }
    """
    parser = PythonFolderParser(folders)
    results = parser.scan_folders()
    return json.dumps(results, indent=2)


if __name__ == '__main__':
    # Example usage
    folders = ['./tests']
    results_json = parse_folders(folders)

    try:
        parsed_results = json.loads(results_json)
    except json.JSONDecodeError as json_ex:
        logging.error(f"JSON parsing error: {json_ex}")
        parsed_results = {}

    # Group classes by filename
    files_dict = {}
    for cls in parsed_results.get('classes', []):
        file_name = cls.get('file', 'Unknown file')
        files_dict.setdefault(file_name, []).append(cls)

    # Print classes and parameters
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

    # Log any parsing errors
    if parsed_results.get('errors'):
        print("-- Errors encountered during parsing --")
        for error in parsed_results['errors']:
            logging.error(error)
            print(error)
