"""
db
==
Programmatic interface for interacting with the lex database.
"""
import os
from typing import Any

import MySQLdb
from dotenv import load_dotenv
from pydantic import parse_obj_as

from dbtypes import (
    Context,
    ContextId,
    Environment,
    Lemma,
    LemmaContextId,
    LemmaContextRelation,
    LemmaId,
    LemmaSourceId,
    LemmaSourceRelation,
    Source,
    SourceId,
    SourceKind,
    SourceKindId,
    SourceKindVal,
    Status,
    StatusId,
    StatusVal,
    UposTag,
)


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
        host = os.getenv(f"HOST_{env.value}")
        user = os.getenv(f"USERNAME_{env.value}")
        passwd = os.getenv(f"PASSWORD_{env.value}")
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

    def truncate_all_tables(self):
        """
        Wipes the database rows while preserving the schema.
        """
        assert self.env in [Environment.DEV, Environment.DEVADMIN]
        cursor = self.connection.cursor()
        statements = [
            "TRUNCATE TABLE source_kind;",
            "TRUNCATE TABLE lemma_status;",
            "TRUNCATE TABLE source;",
            "TRUNCATE TABLE lemma;",
            "TRUNCATE TABLE lemma_source;",
            "TRUNCATE TABLE context;",
            "TRUNCATE TABLE lemma_context;",
        ]
        for s in statements:
            cursor.execute(s, [])
        self.connection.commit()
        cursor.close()

    def add_source_kind(self, source_kind: SourceKind) -> SourceKindId:
        """
        Adds a new source kind to the database if it doesn't exist already.
        Returns -1 if invalid source kind.
        """
        cursor = self.connection.cursor()
        sql = "INSERT IGNORE INTO source_kind (kind) VALUES (%s)"
        cursor.execute(sql, (source_kind.kind.value,))
        self.connection.commit()
        cursor.close()
        return SourceKindId(self.get_source_kind_id(source_kind.kind))

    def get_source_kind_id(self, source_kind: SourceKindVal) -> SourceKindId:
        """
        Returns the id of a source kind. Returns -1 if the kind doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM source_kind WHERE kind = %s"
        cursor.execute(sql, (source_kind.value,))
        source_kind_id = res[0] if (res := cursor.fetchone()) else -1
        cursor.close()
        return SourceKindId(source_kind_id)

    def get_source_kind(
        self, source_kind_id: SourceKindId
    ) -> SourceKind | None:
        """
        Returns a SourceKind object. Returns None if the kind doesn't
        exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM source_kind WHERE id = %s"
        cursor.execute(sql, (source_kind_id,))

        source_kind = (
            parse_obj_as(SourceKind, {"id": res[0], "kind": res[1]})
            if (res := cursor.fetchone())
            else None
        )

        cursor.close()
        return source_kind

    def add_source(self, source: Source) -> SourceId:
        """
        Adds a new source to the database if it doesn't exist already.
        Returns -1 if aborted because of invalid source kind id.
        """
        if not self.get_source_kind(source.source_kind_id):
            return SourceId(-1)

        cursor = self.connection.cursor()
        sql = (
            "INSERT IGNORE INTO source (title, source_kind_id) VALUES (%s, %s)"
        )
        cursor.execute(sql, (source.title, source.source_kind_id))
        self.connection.commit()
        cursor.close()
        return SourceId(
            self.get_source_id(source.title, source.source_kind_id)
        )

    def get_source_id(
        self, title: str, source_kind_id: SourceKindId
    ) -> SourceId:
        """
        Returns the id of a source. Returns -1 if the source doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT id FROM source WHERE title = %s AND source_kind_id = %s"
        cursor.execute(sql, (title, source_kind_id))
        source_id = res[0] if (res := cursor.fetchone()) else -1
        cursor.close()
        return SourceId(source_id)

    def get_source(self, source_id: SourceId) -> Source | None:
        """
        Returns a Source object. Returns None if the source doesn't
        exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM source WHERE id = %s"
        cursor.execute(sql, (source_id,))

        source = (
            parse_obj_as(
                Source,
                {"id": res[0], "title": res[1], "source_kind_id": res[2]},
            )
            if (res := cursor.fetchone())
            else None
        )

        cursor.close()
        return source

    def add_status(self, status_val: StatusVal) -> StatusId:
        """
        Adds a new status to the database if it doesn't exist already.
        Returns -1 if invalid status.
        """
        cursor = self.connection.cursor()
        sql = "INSERT IGNORE INTO lemma_status (status) VALUES (%s)"
        cursor.execute(sql, (status_val.value,))
        self.connection.commit()
        cursor.close()
        return StatusId(self.get_status_id(status_val))

    def get_status_id(self, status_val: StatusVal) -> StatusId:
        """
        Returns the id of a status. Returns -1 if the status doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM lemma_status WHERE status = %s"
        cursor.execute(sql, (status_val.value,))
        if status := (
            parse_obj_as(Status, {"id": res[0], "status": res[1]})
            if (res := cursor.fetchone())
            else None
        ):
            status_id = status.id
        else:
            status_id = StatusId(-1)
        cursor.close()
        return status_id

    def get_status_by_id(self, status_id: StatusId) -> Status | None:
        """
        Returns the status of a lemma. Returns None if the status doesn't
        exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM lemma_status WHERE id = %s"
        cursor.execute(sql, (status_id,))

        status = (
            parse_obj_as(Status, {"id": res[0], "status": res[1]})
            if (res := cursor.fetchone())
            else None
        )

        cursor.close()
        return status

    def add_lemma(self, lemma: Lemma) -> LemmaId:
        """
        Adds a new lemma to the database if it doesn't exist already.
        Returns -1 if aborted because of invalid status id.
        """
        if not self.get_status_by_id(lemma.status_id):
            return LemmaId(-1)

        if (lemma_id := self.get_lemma_id(lemma.lemma)) != -1:
            return lemma_id

        cursor = self.connection.cursor()
        sql = "INSERT INTO lemma (lemma, status_id) VALUES (%s, %s)"
        cursor.execute(sql, (lemma.lemma, lemma.status_id))
        self.connection.commit()
        cursor.close()
        return LemmaId(self.get_lemma_id(lemma.lemma))

    def get_lemma(self, lemma_id: LemmaId) -> Lemma | None:
        """
        Returns a lemma. Returns None if the lemma doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM lemma WHERE id = %s"
        cursor.execute(sql, (lemma_id,))

        lemma = (
            parse_obj_as(
                Lemma,
                {
                    "id": res[0],
                    "lemma": res[1],
                    "created": res[2],
                    "status_id": res[3],
                },
            )
            if (res := cursor.fetchone())
            else None
        )
        cursor.close()
        return lemma

    def get_lemma_id(self, lemma_value: str) -> LemmaId:
        """
        Returns the id of a lemma. Returns -1 if the lemma doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM lemma WHERE lemma = %s"
        cursor.execute(sql, (lemma_value,))
        if lemma := (
            parse_obj_as(
                Lemma,
                {
                    "id": res[0],
                    "lemma": res[1],
                    "created": res[2],
                    "status_id": res[3],
                },
            )
            if (res := cursor.fetchone())
            else None
        ):
            lemma_id = lemma.id
        else:
            lemma_id = LemmaId(-1)

        cursor.close()
        return LemmaId(lemma_id)

    def get_lemma_status(self, lemma_id: LemmaId) -> Status | None:
        """
        Returns the status of a lemma. Returns None if the lemma id is invalid
        """
        if lemma := self.get_lemma(lemma_id):
            return self.get_status_by_id(lemma.status_id)
        else:
            return None

    def add_lemma_source_relation(
        self, lemma_source_relation: LemmaSourceRelation
    ) -> LemmaSourceId:
        """
        Adds a new lemma-source relation to the database.
        """
        # check that lemma id and source id exist
        if not self.get_lemma(
            lemma_source_relation.lemma_id
        ) or not self.get_source(lemma_source_relation.source_id):
            return LemmaSourceId(-1)

        cursor = self.connection.cursor()
        sql = "INSERT INTO lemma_source (lemma_id, source_id) VALUES (%s, %s)"
        cursor.execute(
            sql,
            (lemma_source_relation.lemma_id, lemma_source_relation.source_id),
        )
        self.connection.commit()
        cursor.close()
        return LemmaSourceId(
            self.get_lemma_source_relation_ids(
                lemma_source_relation.lemma_id, lemma_source_relation.source_id
            )[-1]
        )

    def get_lemma_sources(self, lemma_id: LemmaId) -> list[Source]:
        """
        Returns all sources in which a lemma appears in.
        """
        cursor = self.connection.cursor()
        sql = "SELECT source_id FROM lemma_source WHERE lemma_id = %s"
        cursor.execute(sql, (lemma_id,))
        source_ids = [
            SourceId(source_id[0]) for source_id in cursor.fetchall() or []
        ]
        cursor.close()
        return [
            source
            for source in (
                self.get_source(source_id) for source_id in source_ids
            )
            if source
        ]

    def get_lemma_source_relation_ids(
        self, lemma_id: LemmaId, source_id: SourceId
    ) -> list[LemmaSourceId]:
        """
        Returns the ids of all lemma-source relations.
        """
        cursor = self.connection.cursor()

        sql = (
            "SELECT id FROM lemma_source WHERE lemma_id = %s AND source_id"
            " = %s"
        )
        cursor.execute(sql, (lemma_id, source_id))
        ids = [LemmaSourceId(lemma_id) for lemma_id in cursor.fetchall() or []]
        cursor.close()
        return ids

    def add_context(self, context: Context) -> ContextId:  # noqa: F821
        """
        Adds a new context to the database if it doesn't exist already.
        Returns -1 if the source doesn't exist.
        """
        if not self.get_source(context.source_id):
            return ContextId(-1)

        if (
            context_id := self.get_context_id(
                context.context_value, context.source_id
            )
        ) != -1:
            return context_id

        cursor = self.connection.cursor()
        sql = "INSERT INTO context (context_value, source_id) VALUES (%s, %s)"
        cursor.execute(sql, (context.context_value, context.source_id))
        self.connection.commit()
        cursor.close()
        return ContextId(
            self.get_context_id(context.context_value, context.source_id)
        )

    def get_context(self, context_id: ContextId) -> Context | None:
        """
        Returns a context. Returns None if the context doesn't
        exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM context WHERE id = %s"
        cursor.execute(sql, (context_id,))
        context = (
            parse_obj_as(
                Context,
                {
                    "id": res[0],
                    "context_value": res[1],
                    "created": res[2],
                    "source_id": res[3],
                },
            )
            if (res := cursor.fetchone())
            else None
        )
        cursor.close()
        return context

    def get_context_id(
        self, context_value: str, source_id: SourceId
    ) -> ContextId:
        """
        Returns the id of a context. Returns -1 if the context doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = (
            "SELECT * FROM context WHERE context_value = %s AND source_id = %s"
        )
        cursor.execute(sql, (context_value, source_id))
        context = (
            parse_obj_as(
                Context,
                {
                    "id": res[0],
                    "context_value": res[1],
                    "created": res[2],
                    "source_id": res[3],
                },
            )
            if (res := cursor.fetchone())
            else None
        )
        cursor.close()
        return context.id if context else ContextId(-1)

    def add_lemma_context_relation(
        self,
        lemma_context: LemmaContextRelation,
    ) -> LemmaContextId:
        """
        Adds a new lemma-context relation to the database.
        """
        # check that lemma id and context id exist
        if not self.get_lemma(lemma_context.lemma_id) or not self.get_context(
            lemma_context.context_id
        ):
            return LemmaContextId(-1)

        cursor = self.connection.cursor()
        sql = (
            "INSERT INTO lemma_context (lemma_id, context_id, upos_tag,"
            " detailed_tag) VALUES (%s, %s, %s, %s)"
        )

        keys_to_exclude = {"id"}
        d = lemma_context.dict(exclude=keys_to_exclude)
        d.update({"upos_tag": lemma_context.upos_tag.value})

        cursor.execute(
            sql,
            (*d.values(),),
        )
        self.connection.commit()
        cursor.close()
        return LemmaContextId(
            self.get_lemma_context_relations(lemma_context)[-1].id
            # TODO: verify that the last id is always the one we just added
        )

    def get_lemma_context_relation(
        self, lemma_context_id: LemmaContextId
    ) -> LemmaContextRelation | None:
        """
        Returns a lemma-context relation.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM lemma_context WHERE id = %s"
        cursor.execute(sql, (lemma_context_id,))
        lemma_context = (
            parse_obj_as(
                LemmaContextRelation,
                {
                    "id": res[0],
                    "lemma_id": res[1],
                    "context_id": res[2],
                    "upos_tag": res[3],
                    "detailed_tag": res[4],
                },
            )
            if (res := cursor.fetchone())
            else None
        )
        cursor.close()
        return lemma_context

    def get_lemma_contexts(self, lemma_id: LemmaId) -> list[Context]:
        """
        Returns all contexts a lemma appears in.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM lemma_context WHERE lemma_id = %s"
        cursor.execute(sql, (lemma_id,))

        context_ids = [
            parse_obj_as(
                LemmaContextRelation,
                {
                    "id": res[0],
                    "lemma_id": res[1],
                    "context_id": res[2],
                    "upos_tag": res[3],
                    "detailed_tag": res[4],
                },
            ).context_id
            for res in cursor.fetchall()
        ]
        return [
            context
            for context in (
                self.get_context(context_id) for context_id in context_ids
            )
            if context is not None
        ]

    def get_lemma_context_relations(
        self, lemma_context: LemmaContextRelation
    ) -> list[LemmaContextRelation]:
        """
        Returns the ids of all lemma-context relations matching the arg.
        Returns -1 if the relation doesn't exist.
        lemma_context.id of arg is ignored.
        """
        cursor = self.connection.cursor()
        sql = (
            "SELECT * FROM lemma_context WHERE lemma_id = %s AND"
            " context_id = %s AND upos_tag = %s AND detailed_tag = %s"
        )

        keys_to_exclude = {"id"}
        d = lemma_context.dict(exclude=keys_to_exclude)
        d.update({"upos_tag": lemma_context.upos_tag.value})

        cursor.execute(
            sql,
            (*d.values(),),
        )

        lemma_context_relations = [
            parse_obj_as(
                LemmaContextRelation,
                {
                    "id": res[0],
                    "lemma_id": res[1],
                    "context_id": res[2],
                    "upos_tag": res[3],
                    "detailed_tag": res[4],
                },
            )
            for res in cursor.fetchall()
        ]

        cursor.close()
        return lemma_context_relations

    def get_status(self, status_id: StatusId) -> Status | None:
        """
        Returns a status.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM lemma_status WHERE id = %s"
        cursor.execute(sql, (status_id,))
        status = (
            parse_obj_as(
                Status,
                {
                    "id": res[0],
                    "status": res[1],
                },
            )
            if (res := cursor.fetchone())
            else None
        )
        cursor.close()
        return status

    def update_lemma_status(
        self, lemma_id: LemmaId, new_status_id: StatusId
    ) -> bool:
        """
        Changes the status of a lemma.
        """
        if (
            not self.get_lemma(lemma_id)
            or self.get_status(new_status_id) == -1
        ):
            return False

        cursor = self.connection.cursor()
        sql = "UPDATE lemma SET status_id = %s WHERE id = %s"
        cursor.execute(sql, (new_status_id, lemma_id))
        self.connection.commit()
        cursor.close()
        if s := self.get_lemma_status(lemma_id):
            return s.id == new_status_id
        else:
            return False

    def update_lemma_context_relation(
        self,
        lemma_context_id: LemmaContextId,
        new_upos_tag: UposTag | None = None,
        new_detailed_tag: str | None = None,
    ) -> bool:
        """
        Changes the upos tag of a lemma-context relation.
        TODO: instead of having two optional args, overload this function
        """
        if not self.get_lemma_context_relation(lemma_context_id):
            return False

        cursor = self.connection.cursor()

        args: Any
        match (new_upos_tag, new_detailed_tag):
            case (None, None):
                return False
            case (_, None):
                assert new_upos_tag is not None
                sql = "UPDATE lemma_context SET upos_tag = %s WHERE id = %s"
                args = (new_upos_tag.value, lemma_context_id)
            case (None, _):
                sql = (
                    "UPDATE lemma_context SET detailed_tag = %s WHERE id = %s"
                )
                args = (new_detailed_tag, lemma_context_id)
            case _:
                assert new_upos_tag is not None
                sql = (
                    "UPDATE lemma_context SET upos_tag = %s, detailed_tag = %s"
                    " WHERE id = %s"
                )
                args = (
                    new_upos_tag.value,
                    new_detailed_tag,
                    lemma_context_id,
                )

        cursor.execute(sql, args)
        self.connection.commit()
        cursor.close()
        lemma_context = self.get_lemma_context_relation(lemma_context_id)
        v1 = lemma_context is not None
        v2 = (
            lemma_context.upos_tag == new_upos_tag
            if lemma_context and new_upos_tag
            else True
        )
        v3 = (
            lemma_context.detailed_tag == new_detailed_tag
            if lemma_context and new_detailed_tag
            else True
        )
        return v1 and v2 and v3

    def delete_lemma(self, lemma_id: LemmaId) -> bool:
        """
        Deletes a lemma and its associated data from the database.
        """
        if not self.get_lemma(lemma_id):
            return False

        cursor = self.connection.cursor()

        # get all source ids associated with the lemma from lemma_source:
        sql = "SELECT source_id FROM lemma_source WHERE lemma_id = %s"
        cursor.execute(sql, (lemma_id,))
        source_ids = set(
            cursor.fetchall() or []
        )  # TODO: check if fetchall returns None or [] by default

        # delete all entries in lemmat_source with the lemma id:
        sql = "DELETE FROM lemma_source WHERE lemma_id = %s"
        cursor.execute(sql, (lemma_id,))
        self.connection.commit()

        # for all source_ids, check if there are still entries in the
        # lemma_source table:
        for source_id in source_ids:
            cursor.execute(
                "SELECT id FROM lemma_source WHERE source_id = %s",
                (source_id,),
            )
            if not cursor.fetchone():
                cursor.execute(
                    "DELETE FROM source WHERE id = %s", (source_id,)
                )
                self.connection.commit()

        # get all context ids associated with the lemma from lemma_context:
        sql = "SELECT context_id FROM lemma_context WHERE lemma_id = %s"
        cursor.execute(sql, (lemma_id,))
        context_ids = set(cursor.fetchall() or [])

        # delete all entries in lemma_context with the lemma id:
        sql = "DELETE FROM lemma_context WHERE lemma_id = %s"
        cursor.execute(sql, (lemma_id,))
        self.connection.commit()

        # for each contextID, check if there are still entries in the
        # lemma_context table, if not delete from context table rows
        # with same contextID
        kept_context_ids = set()
        for context_id in context_ids:
            cursor.execute(
                "SELECT id FROM lemma_context WHERE context_id = %s",
                (context_id,),
            )
            if not cursor.fetchone():
                cursor.execute(
                    "DELETE FROM context WHERE id = %s", (context_id,)
                )
                self.connection.commit()
            else:
                kept_context_ids.add(context_id)

        # for each kept context id, get context_value and remove lemma id
        # from it
        for context_id in kept_context_ids:
            cursor.execute(
                "SELECT context_value FROM context WHERE id = %s",
                (context_id,),
            )
            context_value = cursor.fetchone()[0]
            context_value = context_value.replace(f"::{lemma_id}", "")
            cursor.execute(
                "UPDATE context SET context_value = %s WHERE id = %s",
                (context_value, context_id),
            )
            self.connection.commit()

        # finally, delete the lemma from the lemma table:
        sql = "DELETE FROM lemma WHERE id = %s"
        cursor.execute(sql, (lemma_id,))
        self.connection.commit()

        cursor.close()
        return not self.get_lemma(lemma_id)


if __name__ == "__main__":
    db = LexDbIntegrator(Environment.DEV)