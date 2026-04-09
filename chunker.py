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

                    chunks.append({
                        'type': 'function',
                        'name': name,
                        'code': code,
                        'body': body,
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'language': 'python',
                        'file_path': file_path
                    })
        return chunks
