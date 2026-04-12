import os
from pathlib import Path
from tree_sitter import Language, Parser, Tree, Node
import tree_sitter_python as tspython
from typing import Generator, List

class CodeChunker:
    def __init__(self):
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)

    def chunk_python(self, code: str, file_path: str) -> List[dict]:
        parser = self.parser
        tree = parser.parse(bytes(code, 'utf-8'))
        root = tree.root_node

        chunks = []

        def traverse_tree(tree: Tree) -> Generator[Node, None, None]:
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

        for node in traverse_tree(tree):
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
                        'language': 'python',
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
    
    def _extract_docstring(self, node, code):
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
