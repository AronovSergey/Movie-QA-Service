# LEARNING: An empty __init__.py marks this directory as a Python package.
# With the src/ layout, Python cannot import from here accidentally without
# the package being installed first — which protects against "works on my
# machine but breaks in CI" import order bugs.
