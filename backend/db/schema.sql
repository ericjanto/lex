CREATE TABLE
    IF NOT EXISTS lemma_status (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        status ENUM ('staged', 'committed', 'pushed') NOT NULL UNIQUE
    );

INSERT INTO
    lemma_status (status)
VALUES
    ('staged'),
    ('committed'),
    ('pushed');

CREATE TABLE
    IF NOT EXISTS lemma (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        lemma VARCHAR(100) NOT NULL UNIQUE,
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
        ) NOT NULL UNIQUE
    );

CREATE TABLE
    IF NOT EXISTS source (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(255) NOT NULL,
        source_kind_id INTEGER NOT NULL,
        CONSTRAINT unique_title_kind_id UNIQUE (title, source_kind_id)
    );

CREATE TABLE
    IF NOT EXISTS lemma_source (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        lemma_id INTEGER NOT NULL,
        source_id INTEGER NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS context (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        context_value TEXT NOT NULL,
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
