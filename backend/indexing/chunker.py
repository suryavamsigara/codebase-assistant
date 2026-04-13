from pathlib import Path
from tree_sitter import Language, Parser, Tree, Node
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from typing import Generator

class CodeChunker:
    def __init__(self):
        self.language = Language(tspython.language())

        self.parsers = {
            "python": Parser(Language(tspython.language())),
            "javascript": Parser(Language(tsjavascript.language())),
        }

        self.lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".md": "markdown"
        }
    
    def _get_language_from_path(self, file_path: str) -> str:
        """Detects language from file extension"""
        ext = Path(file_path).suffix.lower()
        return self.lang_map.get(ext, 'unknown')
    
    def _traverse_tree(self, tree: Tree) -> Generator[Node, None, None]:
        cursor = tree.walk()

        visited_children = False

        while True:
            if not visited_children:
                yield cursor.node

                if not cursor.goto_first_child():
                    visited_children = True
            elif cursor.goto_next_sibling():
                visited_children = False
            elif not cursor.goto_parent():
                break

    def chunk_file(self, code, file_path):
        language = self._get_language_from_path(file_path)

        if language == "python":
            return self.chunk_python(code, file_path, "python")
        
        if language == "javascript":
            return self.chunk_javascript(code, file_path, "javascript")
        
        else:
            return self._chunk_by_lines(code, file_path)

    def chunk_python(self, code: str, file_path: str, language: str) -> list[dict]:
        parser = self.parsers["python"]
        tree = parser.parse(bytes(code, 'utf-8'))

        chunks = []

        for node in self._traverse_tree(tree):
            if node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = code[name_node.start_byte:name_node.end_byte]

                    body_node = node.child_by_field_name('body')
                    if body_node:
                        body = code[body_node.start_byte:body_node.end_byte]
                    else:
                        body = ""

                    docstring = self._extract_docstring(node, code)

                    parent = node.parent
                    parent_class = None

                    while parent:
                        if parent.type == 'class_definition':
                            class_name_node = parent.child_by_field_name('name')
                            if class_name_node:
                                parent_class = code[class_name_node.start_byte:class_name_node.end_byte]
                            break
                        parent = parent.parent

                    chunks.append({
                        'type': 'function',
                        'name': name,
                        'docstring': docstring,
                        'code': body,
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'language': language,
                        'file_path': file_path,
                        'parent_class': parent_class
                    })
            
            elif node.type == 'class_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = code[name_node.start_byte:name_node.end_byte]

                    docstring = self._extract_docstring(node, code)

                    methods = []

                    body_node = node.child_by_field_name('body')
                    if body_node:
                        for child in body_node.children:
                            if child.type == 'function_definition':
                                fn_name_node = child.child_by_field_name('name')
                                if fn_name_node:
                                    fn_name = code[fn_name_node.start_byte:fn_name_node.end_byte]
                                    methods.append(fn_name)

                    chunks.append({
                        'type': 'class',
                        'name': name,
                        'docstring': docstring,
                        'methods': methods,
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'language': 'python',
                        'file_path': file_path,
                    })
        return chunks
    
    def chunk_javascript(self, code: str, file_path: str, language: str) -> list[dict]:
        parser = self.parsers["javascript"]
        tree = parser.parse(bytes(code, 'utf-8'))

        chunks = []

        for node in self._traverse_tree(tree):
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                name = code[name_node.start_byte:name_node.end_byte]

                body_node = node.child_by_field_name('body')
                if body_node:
                    body = code[body_node.start_byte:body_node.end_byte]
                else:
                    body = ""

                parent = node.parent
                parent_class = None

                while parent:
                    if parent.type == 'class_declaration':
                        class_name_node = parent.child_by_field_name('node')
                        if class_name_node:
                            parent_class = code[class_name_node.start_byte:class_name_node.end_byte]
                        break
                    parent = parent.parent

                chunks.append({
                    'type': 'function',
                    'name': name,
                    'code': body,
                    'start_line': node.start_point[0] + 1,
                    'end_line': node.end_point[0] + 1,
                    'language': language,
                    'file_path': file_path,
                    'parent_class': parent_class
                })

            if node.type == 'arrow_function':
                name = self._find_arrow_function_name(node, code)
                body_node = node.child_by_field_name('body')
                if body_node:
                    body = code[body_node.start_byte:body_node.end_byte]
                else:
                    body = ""
                
                chunks.append({
                    'type': 'function',
                    'name': name,
                    'code': body,
                    'start_line': node.start_point[0] + 1,
                    'end_line': node.end_point[0] + 1,
                    'language': language,
                    'file_path': file_path
                })
            
            if node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                name = code[name_node.start_byte:name_node.end_byte]

                methods = []
                body_node = node.child_by_field_name('body')
                if body_node:
                    for child in body_node.children:
                        if child.type == 'method_definition':
                            prop_name = child.child_by_field_name('name')
                            if prop_name:
                                method_name = code[prop_name.start_byte:prop_name.end_byte]
                                methods.append(method_name)

                chunks.append({
                    'type': 'class',
                    'name': name,
                    'methods': methods,
                    'start_line': node.start_point[0] + 1,
                    'end_line': node.end_point[0] + 1,
                    'language': language,
                    'file_path': file_path,
                })
        return chunks
    
    def _find_arrow_function_name(self, node: Node, code: str):
        """Find variable/property name assigned to arrow function"""
        
        parent = node.parent

        while parent:
            # Case 1: const add = () => {}
            if parent.type == 'variable_declarator':
                name_node = parent.child_by_field_name('name')
                if name_node:
                    return code[name_node.start_byte:name_node.end_byte]

            # Case 2: { add: () => {} }
            elif parent.type == 'pair':
                key_node = parent.child_by_field_name('key')
                if key_node:
                    return code[key_node.start_byte:key_node.end_byte]

            # Case 3: class fields
            elif parent.type in ['public_field_definition', 'method_definition']:
                name_node = parent.child_by_field_name('name')
                if name_node:
                    return code[name_node.start_byte:name_node.end_byte]

            parent = parent.parent

        return None

    def _extract_docstring(self, node, code) -> str:
        """Extract docstring from function or class node"""
        body = node.child_by_field_name('body')
        if not body:
            return ""
        
        for child in body.children:
            if child.type == 'expression_statement':
                if child.children:
                    first = child.children[0]
                    if first.type == 'string':
                        return code[first.start_byte:first.end_byte]
                break
        return ""
    
    def _chunk_by_lines(self, code: str, file_path: str) -> list[dict]:
        """Fallback: Chunk by lines for unknown file types"""

        chunks = []
        lines = code.split('\n')
        chunk_size = 50
        overlap = 10

        for i in range(0, len(lines), chunk_size-overlap):
            chunk_lines = lines[i:i+chunk_size]
            chunk_code = '\n'.join(chunk_lines)

            chunks.append({
                'type': 'code_block',
                'name': f'lines_{i+1}_{i+len(chunk_lines)}',
                'code': chunk_code,
                'start_line': i + 1,
                'end_line': i + len(chunk_lines),
                'language': 'unknown',
                'file_path': file_path
            })
        
        return chunks
