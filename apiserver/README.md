conda config --set auto_activate_base False
conda env create -f environment.yml
conda activate lex-api

mypy --install-types
mypy . (from apiserver folder)

Most Python filenames are prefixed with `_` so that they are not interpreted as
lambdas by Vercel.
