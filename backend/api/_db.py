"""
db
==
Programmatic interface for interacting with the lex database.
"""
import os
import re
from collections import Counter, OrderedDict, defaultdict
from typing import Any, Union

import mysql.connector
from dotenv import load_dotenv
from pydantic import parse_obj_as
from tabulate import tabulate

from ._dbtypes import (
    Context,
    ContextId,
    DbEnvironment,
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

    def __init__(self, env: DbEnvironment) -> None:
        """
        Initializes the database connection
        """
        self.env = env

        load_dotenv()
        host = os.getenv(f"HOST_{env.value}")
        user = os.getenv(f"USERNAME_{env.value}")
        passwd = os.getenv(f"PASSWORD_{env.value}")
        db = os.getenv("DATABASE")

        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            passwd=passwd,
            db=db,
            autocommit=True,
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
        assert self.env in [DbEnvironment.DEV, DbEnvironment.DEVADMIN]
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

    def add_source_kind(self, source_kind: SourceKindVal) -> SourceKindId:
        """
        Adds a new source kind to the database if it doesn't exist already.
        Returns -1 if invalid source kind.
        """
        cursor = self.connection.cursor()
        sql = "INSERT IGNORE INTO source_kind (kind) VALUES (%s)"
        cursor.execute(sql, (source_kind.value,))
        self.connection.commit()
        skid = self.get_source_kind_id(source_kind)
        cursor.close()
        return skid

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
    ) -> Union[SourceKind, None]:
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
            "INSERT IGNORE INTO source (title, source_kind_id, author, lang)"
            " VALUES (%s, %s, %s, %s)"
        )
        cursor.execute(
            sql,
            (source.title, source.source_kind_id, source.author, source.lang),
        )
        self.connection.commit()
        cursor.close()
        return self.get_source_id(source.title, source.source_kind_id)

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

    def get_source(self, source_id: SourceId) -> Union[Source, None]:
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
                {
                    "id": res[0],
                    "title": res[1],
                    "source_kind_id": res[2],
                    "author": res[3],
                    "lang": res[4],
                    "removed_lemmata_num": res[5],
                },
            )
            if (res := cursor.fetchone())
            else None
        )

        cursor.close()
        return source

    def get_paginated_sources(
        self,
        page: int,
        page_size: int,
        filter_params: Union[dict[str, Union[int, str]], None] = None,
    ) -> list[Source]:
        """
        Returns a list of all sources within the pagination range.

        filter_params is an optional filter parameter which is a dict of
        {column_name: value} items.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM source"
        if filter_params:
            for i, param in enumerate(filter_params.items() or []):
                sql += " WHERE" if i == 0 else " AND"
                sql += f" {param[0]} = %s"
        sql += " ORDER BY id LIMIT %s OFFSET %s"

        cursor.execute(
            sql,
            (
                *list(filter_params.values() if filter_params else []),
                page_size,
                page_size * (page - 1),
            ),
        )

        sources = [
            parse_obj_as(
                Source,
                {
                    "id": res[0],
                    "title": res[1],
                    "source_kind_id": res[2],
                    "author": res[3],
                    "lang": res[4],
                    "removed_lemmata_num": res[5],
                },
            )
            for res in cursor.fetchall()
        ]
        cursor.close()
        return sources

    def add_status(self, status_val: StatusVal) -> StatusId:
        """
        Adds a new status to the database if it doesn't exist already.
        Returns -1 if invalid status.
        """
        cursor = self.connection.cursor()
        sql = "INSERT IGNORE INTO lemma_status (status) VALUES (%s)"
        cursor.execute(sql, (status_val.value,))
        self.connection.commit()
        return self.get_status_id(status_val)

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

    def get_status_by_id(self, status_id: StatusId) -> Union[Status, None]:
        """
        Returns the status of a lemma. Returns None if the status doesn't
        exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM lemma_status WHERE id = %s"
        cursor.execute(sql, (status_id,))

        status = (
            Status(id=res[0][0], status=res[0][1])
            if (res := cursor.fetchall())
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

        if not self.get_source(lemma.found_in_source):
            return LemmaId(-1)

        cursor = self.connection.cursor()
        sql = (
            "INSERT INTO lemma (lemma, status_id, found_in_source) VALUES (%s,"
            " %s, %s)"
        )
        cursor.execute(
            sql, (lemma.lemma, lemma.status_id, lemma.found_in_source)
        )
        self.connection.commit()
        lemma_id = self.get_lemma_id(lemma.lemma)
        cursor.close()
        return lemma_id

    def bulk_add_lemma(
        self,
        lemmata_values: list[str],
        status_id: StatusId,
        found_in_source: SourceId,
    ) -> dict[str, LemmaId]:
        """ """
        if not self.get_status_by_id(status_id):
            return {}

        if not self.get_source(found_in_source):
            return {}

        lemmata_values = list(OrderedDict.fromkeys(lemmata_values))

        already_in_db = self.bulk_get_lemma_id_dict(lemmata_values)

        to_push = list(
            filter(
                lambda lemma_val: lemma_val not in already_in_db.keys(),
                lemmata_values,
            )
        )

        if not to_push:
            return already_in_db

        sql = (
            "INSERT INTO lemma (lemma, status_id, found_in_source)"
            " VALUES (%s, %s, %s)"
        )

        query_data = [
            (lemma_val, status_id, found_in_source) for lemma_val in to_push
        ]

        cursor = self.connection.cursor()
        cursor.executemany(sql, query_data)
        self.connection.commit()

        lemma_id_dict = self.bulk_get_lemma_id_dict(lemmata_values)

        cursor.close()

        return lemma_id_dict

    def get_lemma(self, lemma_id: LemmaId) -> Union[Lemma, None]:
        """
        Returns a lemma. Returns None if the lemma doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM lemma WHERE id = %s LIMIT 1"
        cursor.execute(sql, (lemma_id,))

        lemma = (
            parse_obj_as(
                Lemma,
                {
                    "id": res[0],
                    "lemma": res[1],
                    "created": res[2],
                    "status_id": res[3],
                    "found_in_source": res[4],
                },
            )
            if (res := (cursor.fetchall() or [[]])[0])
            else None
        )
        cursor.close()
        return lemma

    def bulk_get_lemmata(self, lemma_ids: list[LemmaId]) -> list[Lemma]:
        lemma_ids = list(OrderedDict.fromkeys(lemma_ids))
        cursor = self.connection.cursor()
        sql = (
            "SELECT * FROM lemma WHERE id IN ("
            + ",".join(["%s"] * len(lemma_ids))
            + ")"
        )
        cursor.execute(sql, lemma_ids)
        lemmata = [
            Lemma(
                id=row[0],
                lemma=row[1],
                created=row[2],
                status_id=row[3],
                found_in_source=row[4],
            )
            for row in cursor.fetchall() or []
        ]
        cursor.close()
        return lemmata

    def get_status_lemma_rows(
        self,
        status_val: StatusVal,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Lemma]:
        status_id = self.get_status_id(status_val)
        cursor = self.connection.cursor()

        if page and page_size:
            limit = page_size
            offset = (page - 1) * page_size
            sql = "SELECT * FROM lemma WHERE status_id = %s LIMIT %s OFFSET %s"
            cursor.execute(sql, (status_id, limit, offset))
        else:
            sql = "SELECT * FROM lemma WHERE status_id = %s"
            cursor.execute(sql, (status_id,))

        return [
            Lemma(
                id=row[0],
                lemma=row[1],
                created=row[2],
                status_id=row[3],
                found_in_source=row[4],
            )
            for row in cursor.fetchall()
        ]

    def get_status_lemma_rows_table(
        self,
        status_val: StatusVal,
        page: int = 1,
        page_size: int = 100,
    ) -> str:
        status_id = self.get_status_id(status_val)
        cursor = self.connection.cursor()

        if page and page_size:
            limit = page_size
            offset = (page - 1) * page_size
            sql = "SELECT * FROM lemma WHERE status_id = %s LIMIT %s OFFSET %s"
            cursor.execute(sql, (status_id, limit, offset))
        else:
            sql = "SELECT * FROM lemma WHERE status_id = %s"
            cursor.execute(sql, (status_id,))

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return tabulate(rows, headers=columns)

    def get_lemma_id(self, lemma_value: str) -> LemmaId:
        """
        Returns the id of a lemma. Returns -1 if the lemma doesn't exist.
        """
        cursor = self.connection.cursor()
        sql = "SELECT id FROM lemma WHERE lemma = %s"
        cursor.execute(sql, (lemma_value,))
        lemma_id = (
            LemmaId(res[0][0]) if (res := cursor.fetchall()) else LemmaId(-1)
        )

        cursor.close()
        return lemma_id

    def bulk_get_lemma_id_dict(
        self, lemmata_values: list[str]
    ) -> dict[str, LemmaId]:
        cursor = self.connection.cursor()
        sql = (
            "SELECT id, lemma FROM lemma WHERE lemma IN ("
            + ",".join(["%s"] * len(lemmata_values))
            + ")"
        )
        cursor.execute(sql, lemmata_values)
        lemma_val_id_dict = {
            res[1]: LemmaId(res[0]) for res in cursor.fetchall() or []
        }
        cursor.close()
        return lemma_val_id_dict

    def get_lemma_status(self, lemma_id: LemmaId) -> Union[Status, None]:
        """
        Returns the status of a lemma. Returns None if the lemma id is invalid
        """
        if lemma := self.get_lemma(lemma_id):
            return self.get_status_by_id(lemma.status_id)
        else:
            return None

    def add_lemma_source_relation(
        self, lemma_source_relation: LemmaSourceRelation
    ) -> bool:
        """
        Adds a new lemma-source relation to the database.
        """
        # check that lemma id and source id exist
        if not self.get_lemma(
            lemma_source_relation.lemma_id
        ) or not self.get_source(lemma_source_relation.source_id):
            return False

        cursor = self.connection.cursor()
        sql = "INSERT INTO lemma_source (lemma_id, source_id) VALUES (%s, %s)"
        cursor.execute(
            sql,
            (lemma_source_relation.lemma_id, lemma_source_relation.source_id),
        )
        self.connection.commit()
        cursor.close()
        return True

    def bulk_add_lemma_source_relations(
        self, rels: list[LemmaSourceRelation]
    ) -> bool:
        if not rels:
            return False

        if not self.get_source(source_id := rels[0].source_id):
            return False

        rels = list(OrderedDict.fromkeys(rels))

        if not self._all_lemmata_exist(
            lemma_ids := [rel.lemma_id for rel in rels]
        ):
            return False

        query_data = [(lid, source_id) for lid in lemma_ids]
        cursor = self.connection.cursor()
        sql = "INSERT INTO lemma_source (lemma_id, source_id) VALUES (%s, %s)"
        cursor.executemany(sql, query_data)
        self.connection.commit()
        cursor.close()
        return True

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
        self,
        lemma_id: LemmaId,
        source_id: SourceId,
        limit: Union[int, None] = None,
    ) -> list[LemmaSourceId]:
        """
        Returns the ids of all lemma-source relations.
        NOTE: this is a very expensive db operation.
        """
        cursor = self.connection.cursor()

        if limit is not None:
            sql = (
                "SELECT id FROM lemma_source WHERE lemma_id = %s AND source_id"
                " = %s ORDER BY id DESC LIMIT %s"
            )
            cursor.execute(sql, (lemma_id, source_id, limit))
            ids = [
                LemmaSourceId(lemma_id[0]) for lemma_id in cursor.fetchall()
            ]
        else:
            sql = (
                "SELECT id FROM lemma_source WHERE lemma_id = %s AND source_id"
                " = %s"
            )
            cursor.execute(sql, (lemma_id, source_id))
            ids = [
                LemmaSourceId(lemma_id[0])
                for lemma_id in cursor.fetchall() or []
            ]
        cursor.close()
        return ids

    def add_context(self, context: Context) -> ContextId:  # noqa: F821
        """
        Adds a new context to the database if it doesn't exist already.
        Returns -1 if the source doesn't exist.
        """
        if not self.get_source(context.source_id):
            print(
                "Did not add context because source id not associated with"
                " source"
            )
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
        cursor.execute("SELECT LAST_INSERT_ID()")
        ctid = ContextId(cursor.fetchall()[0][0])
        if ctid == 0:
            ctid = self.get_context_id(
                context.context_value, context.source_id
            )
        cursor.close()
        return ctid

    def get_context(self, context_id: ContextId) -> Union[Context, None]:
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

    def bulk_get_contexts(self, cids: list[ContextId]) -> list[Context]:
        cids = list(OrderedDict.fromkeys(cids))
        sql = (
            "SELECT * FROM context WHERE id IN ("
            + ",".join(["%s"] * len(cids))
            + ")"
        )
        cursor = self.connection.cursor()
        cursor.execute(sql, cids)
        contexts = [
            parse_obj_as(
                Context,
                {
                    "id": res[0],
                    "context_value": res[1],
                    "created": res[2],
                    "source_id": res[3],
                },
            )
            for res in cursor.fetchall() or []
        ]
        cursor.close()
        return contexts

    def get_paginated_contexts(
        self, page: int, page_size: int
    ) -> list[Context]:
        """
        Returns a list of contexts.
        """
        cursor = self.connection.cursor()
        sql = "SELECT * FROM context ORDER BY id LIMIT %s OFFSET %s"
        cursor.execute(sql, (page_size, page_size * (page - 1)))
        contexts = [
            parse_obj_as(
                Context,
                {
                    "id": res[0],
                    "context_value": res[1],
                    "created": res[2],
                    "source_id": res[3],
                },
            )
            for res in cursor.fetchall()
        ]
        cursor.close()
        return contexts

    def get_paginated_source_contexts(
        self, source_id: SourceId, page: int, page_size: int
    ) -> list[Context]:
        """
        Returns a list of contexts.
        """
        cursor = self.connection.cursor()
        sql = (
            "SELECT * FROM context WHERE source_id = %s ORDER BY id LIMIT %s"
            " OFFSET %s"
        )
        cursor.execute(sql, (source_id, page_size, page_size * (page - 1)))
        contexts = [
            parse_obj_as(
                Context,
                {
                    "id": res[0],
                    "context_value": res[1],
                    "created": res[2],
                    "source_id": res[3],
                },
            )
            for res in cursor.fetchall()
        ]
        cursor.close()
        return contexts

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
        cursor.execute("SELECT LAST_INSERT_ID()")
        lcid = LemmaContextId(cursor.fetchall()[0][0])
        cursor.close()
        return lcid

    def bulk_add_lemma_context_relations(
        self, rels: list[LemmaContextRelation]
    ) -> bool:
        """ """
        if not self._all_lemmata_exist([rel.lemma_id for rel in rels]):
            return False

        if not self._all_contexts_exist([rel.context_id for rel in rels]):
            return False

        rels = list(OrderedDict.fromkeys(rels))

        keys_to_exclude = {"id"}
        query_data = []
        for rel in rels:
            d = rel.dict(exclude=keys_to_exclude)
            d.update({"upos_tag": rel.upos_tag.value})
            query_data.append(list(d.values()))

        sql = (
            "INSERT INTO lemma_context (lemma_id, context_id, upos_tag,"
            " detailed_tag) VALUES (%s, %s, %s, %s)"
        )

        cursor = self.connection.cursor()
        cursor.executemany(sql, query_data)
        self.connection.commit()
        cursor.close()
        return True

    def get_lemma_context_relation(
        self, lemma_context_id: LemmaContextId
    ) -> Union[LemmaContextRelation, None]:
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

    def get_lemma_contexts(
        self, lemma_id: LemmaId, page: int, page_size: int
    ) -> list[Context]:
        """
        Returns all contexts a lemma appears in.
        """
        cursor = self.connection.cursor()
        limit = page_size
        offset = (page - 1) * page_size

        sql = (
            "SELECT * FROM lemma_context WHERE lemma_id = %s ORDER BY"
            " context_id LIMIT %s OFFSET %s"
        )
        cursor.execute(
            sql,
            (
                lemma_id,
                limit,
                offset,
            ),
        )

        context_ids = sorted(
            {
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
            }
        )

        # TODO bulk retrieve contexts
        # TODO or just join the tables
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

    def get_status(self, status_id: StatusId) -> Union[Status, None]:
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

    def update_lemmata_status(
        self, lemma_ids: list[LemmaId], new_status_id: StatusId
    ) -> bool:
        """
        Changes the status of all lemmata in the list.
        Doesn't update any of them if one of the ids doesn't exist.
        """
        if self.get_status(new_status_id) == -1:
            return False

        for lid in lemma_ids:
            if not self.get_lemma(lid):
                return False
            if s := self.get_lemma_status(lid):
                if s.id == new_status_id:
                    return False

        cursor = self.connection.cursor()
        sql = (
            "UPDATE lemma SET status_id = %s WHERE id IN"
            f" ({','.join(map(str, lemma_ids))})"
        )
        cursor.execute(sql, (new_status_id,))
        self.connection.commit()
        cursor.close()
        if s := self.get_lemma_status(lemma_ids.pop()):
            return s.id == new_status_id
        else:
            return False

    def update_lemma_context_relation(
        self,
        lemma_context_id: LemmaContextId,
        new_upos_tag: Union[UposTag, None] = None,
        new_detailed_tag: Union[str, None] = None,
    ) -> bool:
        """
        Changes the upos tag of a lemma-context relation.
        TODO: instead of having two optional args, overload this function
        """
        if not self.get_lemma_context_relation(lemma_context_id):
            return False

        cursor = self.connection.cursor()

        args: Any
        if new_upos_tag is None and new_detailed_tag is None:
            return False
        elif new_upos_tag is not None and new_detailed_tag is None:
            sql = "UPDATE lemma_context SET upos_tag = %s WHERE id = %s"
            args = (new_upos_tag.value, lemma_context_id)
        elif new_upos_tag is None:
            sql = "UPDATE lemma_context SET detailed_tag = %s WHERE id = %s"
            args = (new_detailed_tag, lemma_context_id)
        else:
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

        Keeps source and contexts even if they were only associated with
        the deleted lemma.
        """
        if not self.get_lemma(lemma_id):
            return False

        cursor = self.connection.cursor()

        # get all source ids associated with the lemma from lemma_source:
        # sql = "SELECT source_id FROM lemma_source WHERE lemma_id = %s"
        # cursor.execute(sql, (lemma_id,))
        # source_ids = {t[0] for t in cursor.fetchall() or []}

        # delete all entries in lemma_source with the lemma id:
        sql = "DELETE FROM lemma_source WHERE lemma_id = %s"
        cursor.execute(sql, (lemma_id,))
        self.connection.commit()

        # for all source_ids, check if there are still entries in the
        # lemma_source table:
        # for source_id in source_ids:  # NOTE: this is already [(sid,),...]
        #     cursor.execute(
        #         "SELECT id FROM lemma_source WHERE source_id = %s LIMIT 1",
        #         (source_id,),
        #     )
        #     if not cursor.fetchall():
        #         cursor.execute(
        #             "DELETE FROM source WHERE id = %s", (source_id,)
        #         )
        #         self.connection.commit()

        # get the found_in_value of the lemma:
        cursor.execute(
            "SELECT found_in_source FROM lemma WHERE id = %s LIMIT 1",
            (lemma_id,),
        )
        found_in_source = cursor.fetchall()[0][0]

        # increase the removed_lemmata_num of the source, if it still exists:
        if source := self.get_source(found_in_source):
            cursor.execute(
                "UPDATE source SET removed_lemmata_num = %s WHERE id = %s",
                (source.removed_lemmata_num + 1, found_in_source),
            )
            self.connection.commit()

        # get all context ids associated with the lemma from lemma_context:
        sql = "SELECT context_id FROM lemma_context WHERE lemma_id = %s"
        cursor.execute(sql, (lemma_id,))
        context_ids = {t[0] for t in cursor.fetchall() or []}

        # delete all entries in lemma_context with the lemma id:
        sql = "DELETE FROM lemma_context WHERE lemma_id = %s"
        cursor.execute(sql, (lemma_id,))
        self.connection.commit()

        # for each contextID, check if there are still entries in the
        # lemma_context table, if not delete from context table rows
        # with same contextID
        # kept_context_ids = set()
        # for context_id in context_ids:
        #     cursor.execute(
        #         "SELECT id FROM lemma_context WHERE context_id = %s LIMIT 1",
        #         (context_id,),
        #     )
        #     if not cursor.fetchall():
        #         cursor.execute(
        #             "DELETE FROM context WHERE id = %s", (context_id,)
        #         )
        #         self.connection.commit()
        #     else:
        #         kept_context_ids.add(context_id)

        # for each kept context id, get context_value and remove lemma id
        # from it
        for context_id in context_ids:
            cursor.execute(
                "SELECT context_value FROM context WHERE id = %s LIMIT 1",
                (context_id,),
            )
            context_value = cursor.fetchall()[0][0]
            context_value = re.sub(
                rf"(::{lemma_id})(\D)", r"\g<2>", context_value
            )
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

    def bulk_delete_lemmata(self, lemma_ids: set[LemmaId]) -> bool:
        """
        TODO: @ej test this spaghetti code
        """
        lemma_ids = list(lemma_ids)
        if not self._all_lemmata_exist(lemma_ids):
            return False

        cursor = self.connection.cursor()
        lemma_id_placeholders = "(" + ",".join(["%s"] * len(lemma_ids)) + ")"
        sql_lemma_source = (
            "DELETE FROM lemma_source WHERE lemma_id IN"
            f" {lemma_id_placeholders}"
        )
        cursor.execute(sql_lemma_source, lemma_ids)
        self.connection.commit()

        sql_found_in_source = (
            "SELECT found_in_source FROM lemma WHERE id IN"
            f" {lemma_id_placeholders}"
        )

        cursor.execute(sql_found_in_source, lemma_ids)
        found_in_source_ids = [SourceId(res[0]) for res in cursor.fetchall()]

        counter = Counter(found_in_source_ids)
        source_ids_by_occurences = defaultdict(list)
        for source_id, occurences in counter.items():
            source_ids_by_occurences[occurences].append(source_id)

        for (
            occurences,
            source_ids_of_count,
        ) in source_ids_by_occurences.items():
            sql_source = (
                "UPDATE source SET removed_lemmata_num = removed_lemmata_num +"
                " %s WHERE id IN ("
                + ",".join(["%s"] * len(source_ids_of_count))
                + ")"
            )
            cursor.execute(sql_source, (occurences, source_ids_of_count))
            self.connection.commit()

        sql_context_ids = (
            "SELECT context_id FROM lemma_context WHERE lemma_id IN"
            f" {lemma_id_placeholders}"
        )
        cursor.execute(sql_context_ids, lemma_ids)
        context_ids = list({ContextId(res[0]) for res in cursor.fetchall()})
        sql_lemma_context = (
            "DELETE FROM lemma_context WHERE lemma_id IN"
            f" {lemma_id_placeholders}"
        )
        cursor.execute(sql_lemma_context, lemma_ids)
        self.connection.commit()

        # For all contexts in context_ids, update the context_value using
        # a regex replacement to remove the lemma_ids, similar to:
        # re.sub(
        #    rf"(::{lemma_id})(\D)", r"\g<2>", context_value
        # )
        # This can be performed using mysql 8.0 regex_replace function:
        sql_replace_lids = (
            "UPDATE context SET context_value = REGEXP_REPLACE("
            "context_value, %s, %s) WHERE id IN ("
            + ",".join(["%s"] * len(context_ids))
            + ")"
        )
        print(sql_replace_lids)

        # to test this manually: insert a lemma source with title
        # "test::1 replacing::1-various::1 ids." as json serialised thing
        # replacing should be testing with regex...
        # TODO
        # SELECT REGEXP_REPLACE('stackoverflow','(.{5})(.*)','$2$1');
        # https://stackoverflow.com/questions/7058209/how-do-i-refer-to-capture-groups-in-a-mysql-regex

    def _all_lemmata_exist(self, lemma_ids: list[LemmaId]) -> bool:
        lemmata = self.bulk_get_lemmata(lemma_ids)
        return {lemma.id for lemma in lemmata} == set(lemma_ids)

    def _all_contexts_exist(self, cids: list[ContextId]) -> bool:
        contexts = self.bulk_get_contexts(cids)
        return {context.id for context in contexts} == set(cids)


if __name__ == "__main__":
    db = LexDbIntegrator(DbEnvironment.DEV)
