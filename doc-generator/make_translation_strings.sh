#!/bin/bash

pygettext.py -d doc_generator -o locale/doc_generator.pot doc_generator.py parse_supplement.py schema_traverser.py doc_formatter/doc_formatter.py doc_formatter/html_generator.py doc_formatter/markdown_generator.py doc_formatter/toc_parser.py doc_formatter/csv_generator.py doc_formatter/property_index_generator.py doc_gen_util/doc_gen_util.py
