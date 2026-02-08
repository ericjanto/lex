conda env create -f environment.yml
conda activate lex-cli

poetry init

Adding new spacy model:
poetry add <model_url...tar.gz>

URL: https://github.com/explosion/spacy-models/releases/ -> use search to find the latest model release
