conda config --set auto_activate_base False
conda env create -f environment.yml
conda activate lex-api

mypy --install-types
mypy . (from apiserver folder)
