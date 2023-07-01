"""
db
==
Database interface for the lex database
"""
import os
from typing import Literal, NewType

import MySQLdb
from dotenv import load_dotenv

Environment = Literal["PROD", "DEV"]

SourceKindId = NewType("SourceKindId", int)
SourceId = NewType("SourceId", int)
StatusId = NewType("StatusId", int)
LemmaId = NewType("LemmaId", int)
LemmataSourceId = NewType("LemmataSourceId", int)
ContextId = NewType("ContextId", int)
LemmaContextId = NewType("LemmaContextId", int)

UposTag = Literal[
    "NOUN",
    "VERB",
    "ADJ",
    "ADV",
    "PROPN",
    "PRON",
    "DET",
    "ADP",
    "NUM",
    "CONJ",
    "PRT",
    "PUNCT",
    "X",
]


class LexDbIntegrator:
    """
    Exposes methods to interact with the database
    """

    def __init__(self, env: Environment) -> None:
        """
        Initializes the database connection
        """
        self.env = env

        load_dotenv()
        host = os.getenv(f"HOST_{env}")
        user = os.getenv(f"USERNAME_{env}")
        passwd = os.getenv(f"PASSWORD_{env}")
        db = os.getenv("DATABASE")
        ssl_mode = "VERIFY_IDENTITY"
        ssl = {"ca": "/etc/ssl/cert.pem"}

        self.connection = MySQLdb.connect(
            host=host,
            user=user,
            passwd=passwd,
            db=db,
            autocommit=True,
            ssl_mode=ssl_mode,
            ssl=ssl,
        )

    def close_connection(self):
        """
        Closes the database connection
        """
        self.connection.close()

    def empty_all_tables(self):
        """
        Wipes the database.
        NOTE: Only to be used on the development branch
        of the database.
        """
        assert self.env == "DEV"
        cursor = self.connection.cursor()
        statements = [
            "DELETE FROM source_kind;",
            "DELETE FROM lemma_status;",
            "DELETE FROM sources;",
            "DELETE FROM lemmata;",
            "DELETE FROM lemmata_sources;",
            "DELETE FROM context;",
            "DELETE FROM lemma_context;",
        ]
        for s in statements:
            cursor.execute(s, [])
        self.connection.commit()
        cursor.close()

    def add_source_kind(self, source_kind: str) -> SourceKindId:
        """
        Adds a new source kind to the database if it doesn't exist already.
        Returns -1 if invalid source kind.
        """
        cursor = self.connection.cursor()
        sql = "INSERT IGNORE INTO source_kind (kind) VALUES (%s)"
        cursor.execute(sql, (source_kind,))
        self.connection.commit()
        cursor.close()
        return SourceKindId(self.get_source_kind_id(source_kind))

    def get_source_kind_id(self, source_kind: str) -> SourceKindId:
        """
        Returns the id of a source kind. Returns -1 if the kind doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT id FROM source_kind WHERE kind = %s"
        cursor.execute(sql, (source_kind,))
        source_kind_id = res[0] if (res := cursor.fetchone()) else -1
        cursor.close()
        return SourceKindId(source_kind_id)

    def get_source_kind(self, source_kind_id: SourceKindId) -> str | None:
        """
        Returns the kind of a source kind. Returns -1 if the kind doesn't
        exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT kind FROM source_kind WHERE id = %s"
        cursor.execute(sql, (source_kind_id,))
        source_kind = res[0] if (res := cursor.fetchone()) else None
        cursor.close()
        return source_kind

    def add_source(self, title: str, source_kind_id: SourceKindId) -> SourceId:
        """
        Adds a new source to the database if it doesn't exist already.
        Returns -1 if aborted because of invalid source kind id.
        """
        if not self.get_source_kind(source_kind_id):
            return SourceId(-1)

        cursor = self.connection.cursor()
        sql = (
            "INSERT IGNORE INTO sources (title, source_kind_id) VALUES"
            " (%s, %s)"
        )
        cursor.execute(sql, (title, source_kind_id))
        self.connection.commit()
        cursor.close()
        return SourceId(self.get_source_id(title, source_kind_id))

    def get_source_id(
        self, title: str, source_kind_id: SourceKindId
    ) -> SourceId:
        """
        Returns the id of a source. Returns -1 if the source doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT id FROM sources WHERE title = %s AND source_kind_id = %s"
        cursor.execute(sql, (title, source_kind_id))
        source_id = res[0] if (res := cursor.fetchone()) else -1
        cursor.close()
        return SourceId(source_id)

    def get_source(self, source_id: SourceId) -> str | None:
        """
        Returns the title of a source. Returns None if the source doesn't
        exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT title FROM sources WHERE id = %s"
        cursor.execute(sql, (source_id,))
        source = res[0] if (res := cursor.fetchone()) else None
        cursor.close()
        return source

    def add_status(self, status: str) -> StatusId:
        """
        Adds a new status to the database if it doesn't exist already.
        Returns -1 if invalid status.
        """
        cursor = self.connection.cursor()
        sql = "INSERT IGNORE INTO lemma_status (status) VALUES (%s)"
        cursor.execute(sql, (status,))
        self.connection.commit()
        cursor.close()
        return StatusId(self.get_status_id(status))

    def get_status_id(self, status: str) -> StatusId:
        """
        Returns the id of a status. Returns -1 if the status doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT id FROM lemma_status WHERE status = %s"
        cursor.execute(sql, (status,))
        status_id = res[0] if (res := cursor.fetchone()) else -1
        cursor.close()
        return StatusId(status_id)

    def get_status_by_id(self, status_id: StatusId) -> str | None:
        """
        Returns the status of a lemma. Returns None if the status doesn't
        exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT status FROM lemma_status WHERE id = %s"
        cursor.execute(sql, (status_id,))
        status = res[0] if (res := cursor.fetchone()) else None
        cursor.close()
        return status

    def get_status_by_lemma(self, lemma: LemmaId) -> str:
        """
        Returns the status of a lemma. Guaranteed to be a valid status
        given the database constraints.
        """
        cursor = self.connection.cursor()
        sql = "SELECT status_id FROM lemmata WHERE id = %s"
        cursor.execute(sql, (lemma,))
        status_id = cursor.fetchone()[0]
        sql = "SELECT status FROM lemma_status WHERE id = %s"
        cursor.execute(sql, (status_id,))
        status = cursor.fetchone()[0]
        cursor.close()
        return status

    def add_lemma(self, lemma: str, status_id: StatusId) -> LemmaId:
        """
        Adds a new lemma to the database if it doesn't exist already.
        Returns -1 if aborted because of invalid status id.
        """
        if not self.get_status_by_id(status_id):
            return LemmaId(-1)

        if (lemma_id := self.get_lemma_id(lemma)) != -1:
            return lemma_id

        cursor = self.connection.cursor()
        sql = "INSERT INTO lemmata (lemma, status_id) VALUES (%s, %s)"
        cursor.execute(sql, (lemma, status_id))
        self.connection.commit()
        cursor.close()
        return LemmaId(self.get_lemma_id(lemma))

    def get_lemma_id(self, lemma: str) -> LemmaId:
        """
        Returns the id of a lemma. Returns -1 if the lemma doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT id FROM lemmata WHERE lemma = %s"
        cursor.execute(sql, (lemma,))
        lemma_id = res[0] if (res := cursor.fetchone()) else -1
        cursor.close()
        return LemmaId(lemma_id)

    def get_lemma(self, lemma_id: LemmaId) -> str | None:
        """
        Returns the lemma of a lemma. Returns None if the lemma doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT lemma FROM lemmata WHERE id = %s"
        cursor.execute(sql, (lemma_id,))
        lemma = res[0] if (res := cursor.fetchone()) else None
        cursor.close()
        return lemma

    def lemmata_source(
        self, lemma_id: LemmaId, source_id: SourceId
    ) -> LemmataSourceId:
        """
        Adds a new lemma-source relation to the database.
        """
        # check that lemma id and source id exist
        if not self.get_lemma(lemma_id) or not self.get_source(source_id):
            return LemmataSourceId(-1)

        cursor = self.connection.cursor()
        sql = (
            "INSERT INTO lemmata_sources (lemma_id, source_id) VALUES (%s, %s)"
        )
        cursor.execute(sql, (lemma_id, source_id))
        self.connection.commit()
        cursor.close()
        return LemmataSourceId(
            self.get_lemmata_source_ids(lemma_id, source_id)[-1]
        )

    def get_lemmata_source_ids(
        self, lemma_id: LemmaId, source_id: SourceId
    ) -> list[LemmataSourceId]:
        """
        Returns the id of a lemma-source relation. Returns -1 if the relation
        doesn't exist.
        """
        cursor = self.connection.cursor()
        # select all ids where lemma_id and source_id match

        sql = (
            "SELECT id FROM lemmata_sources WHERE lemma_id = %s AND source_id"
            " = %s"
        )
        cursor.execute(sql, (lemma_id, source_id))
        ids = [
            LemmataSourceId(lemma_id) for lemma_id in cursor.fetchall()
        ] or [LemmataSourceId(-1)]
        cursor.close()
        return ids

    def add_context(self, context: str, source_id: SourceId) -> ContextId:
        """
        Adds a new context to the database if it doesn't exist already.
        Returns -1 if the source doesn't exist.
        """
        if not self.get_source(source_id):
            return ContextId(-1)

        if (context_id := self.get_context_id(context, source_id)) != -1:
            return context_id

        cursor = self.connection.cursor()
        sql = "INSERT INTO contexts (context, source_id) VALUES (%s, %s)"
        cursor.execute(sql, (context, source_id))
        self.connection.commit()
        cursor.close()
        return ContextId(self.get_context_id(context, source_id))

    def get_context_id(self, context: str, source_id: SourceId) -> ContextId:
        """
        Returns the id of a context. Returns -1 if the context doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT id FROM contexts WHERE context = %s AND source_id = %s"
        cursor.execute(sql, (context, source_id))
        context_id = res[0] if (res := cursor.fetchone()) else -1
        cursor.close()
        return ContextId(context_id)

    def get_context(self, context_id: ContextId) -> str | None:
        """
        Returns the context of a context. Returns None if the context doesn't
        exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT context FROM contexts WHERE id = %s"
        cursor.execute(sql, (context_id,))
        context = res[0] if (res := cursor.fetchone()) else None
        cursor.close()
        return context

    def add_lemma_context(
        self,
        lemma_id: LemmaId,
        context_id: ContextId,
        upos_tag: UposTag,
        detailed_tag: str,
    ) -> LemmaContextId:
        """
        Adds a new lemma-context relation to the database.
        """
        # check that lemma id and context id exist
        if not self.get_lemma(lemma_id) or not self.get_context(context_id):
            return LemmaContextId(-1)

        cursor = self.connection.cursor()
        sql = (
            "INSERT INTO lemma_context (lemma_id, context_id, upos_tag,"
            " detailed_tag) VALUES (%s, %s, %s, %s)"
        )
        cursor.execute(sql, (lemma_id, context_id, upos_tag, detailed_tag))
        self.connection.commit()
        cursor.close()
        return LemmaContextId(
            self.get_lemma_context_ids(
                lemma_id, context_id, upos_tag, detailed_tag
            )[-1]
        )

    def get_lemma_context_ids(
        self,
        lemma_id: LemmaId,
        context_id: ContextId,
        upos_tag: UposTag,
        detailed_tag: str,
    ) -> list[LemmaContextId]:
        """
        Returns the id of a lemma-context relation. Returns -1 if the relation
        doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = (
            "SELECT id FROM lemma_context WHERE lemma_id = %s AND"
            " context_id = %s AND upos_tag = %s AND detailed_tag = %s"
        )
        cursor.execute(sql, (lemma_id, context_id, upos_tag, detailed_tag))
        ids = [LemmaContextId(lemma_id) for lemma_id in cursor.fetchall()] or [
            LemmaContextId(-1)
        ]
        cursor.close()
        return ids

    def change_lemma_status(self, lemma_id: LemmaId, status: str) -> bool:
        """
        Changes the status of a lemma.
        """
        if not self.get_lemma(lemma_id) or not (
            status_id := self.get_status_id(status)
        ):
            return False

        cursor = self.connection.cursor()
        sql = "UPDATE lemmata SET status_id = %s WHERE id = %s"
        cursor.execute(sql, (status_id, lemma_id))
        self.connection.commit()
        cursor.close()
        return status == self.get_status_by_lemma(lemma_id)

    # def change_lemma_context_upos_tag(
    #     self, lemma_context_id: LemmaContextId, upos_tag: UposTag
    # ) -> bool:
    #     """
    #     Changes the upos tag of a lemma-context relation.

    #     TODO: if multiple lemma-context relations exist, ask the user which
    #           one
    #     they want to change.
    #     TODO: test that behaviour
    #     """
    #     if not self.get_lemma_context(lemma_context_id):
    #         return False

    #     cursor = self.connection.cursor()
    #     sql = "UPDATE lemma_context SET upos_tag = %s WHERE id = %s"
    #     cursor.execute(sql, (upos_tag, lemma_context_id))
    #     self.connection.commit()
    #     cursor.close()
    #     return upos_tag == self.get_lemma_context(lemma_context_id)


if __name__ == "__main__":
    db = LexDbIntegrator("DEV")
    # print(db.add_new_source_kind("book"))
    # print(db.add_new_source_kind("book"))
    # print(db.add_new_source_kind("film"))
    # print(db.add_new_source_kind("invalid"))
    # print(db.get_source_kind_id("test"))
    # db.empty_all_tables()
    db.close_connection()
