CREATE TABLE
    IF NOT EXISTS lemma_status (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        status ENUM ('pending', 'accepted') NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS lemmata (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        lemma VARCHAR(100) NOT NULL,
        created DATETIME DEFAULT CURRENT_TIMESTAMP,
        status_id INTEGER NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS source_kind (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        kind ENUM (
            'book',
            'article',
            'conversation',
            'film'
        ) NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(255) NOT NULL,
        kind_id INTEGER NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS lemmata_sources (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        lemma_id INTEGER NOT NULL,
        source_id INTEGER NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS context (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        context TEXT NOT NULL,
        created DATETIME DEFAULT CURRENT_TIMESTAMP,
        source_id INTEGER NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS lemma_context (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        lemma_id INTEGER NOT NULL,
        context_id INTEGER NOT NULL,
        upos_tag ENUM (
            'NOUN',
            'VERB',
            'ADJ',
            'ADV',
            'PROPN',
            'PRON',
            'DET',
            'ADP',
            'NUM',
            'CONJ',
            'PRT',
            'PUNCT',
            'X'
        ) NOT NULL,
        detailed_tag VARCHAR(10) NOT NULL
    );