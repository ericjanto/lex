Lex is a vocabulary management system for personal use.

## Concept

```txt
Parse file             --> fileparser
Extract relevant words --> tokeniser
Update knowledge base  --> sync
```

## Local setup

You can create a virtual env using conda. For this you need
anaconda installed in your system. A recommended configuration
is to set the automatic activation of the `base` env to false,
running:

```
conda config --set auto_activate_base False
```

Using the `enviroment.yml` you can create the new env.

1. Create the environment using:
   ```
   conda env create -f environment.yml
   ```
2. Activate the environment
   ```
   conda activate lex
   ```
3. Deactivate after use
   ```
   conda deactivate
   ```

Alternatively, if you don't want to use a virtual env you can install all requirements:

```
pip install -r requirements.txt
```

## commitizen
- `cz commit` to commit staged files

## Supporting a new language
- Tokeniser: check if language supported, otherwise use English as default
- Tagger: only Russian and English supported, so would need to train own tagger
- Tag set: do research on which tag set to use, how to map it to universal tag set. pos_sent_tag uses a PerceptronTagger() under the hood
- Lemmatisation
