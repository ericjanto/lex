"""
db
==
Lex database API
"""

import os
import re
from collections import Counter, OrderedDict
from typing import Union

from dotenv import load_dotenv
from pydantic import parse_obj_as
from supabase import Client, create_client
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
        # Updated environment variables for Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        # Get the appropriate schema based on environment
        self.schema = os.getenv(
            "SUPABASE_SCHEMA_PROD"
            if env == DbEnvironment.PROD
            else "SUPABASE_SCHEMA_DEV",
            "public",
        )

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )

        # Changed connection from MySQL to Supabase
        self.connection: Client = create_client(supabase_url, supabase_key)

    def truncate_all_tables(self):
        """
        Wipes the database rows while preserving the schema.
        """
        assert self.env == DbEnvironment.DEV

        tables = [
            "source_kind",
            "lemma_status",
            "source",
            "lemma",
            "lemma_source",
            "context",
            "lemma_context",
        ]

        truncate_query = (
            f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;"
        )
        self.connection.rpc("execute_sql", {"sql": truncate_query}).execute()

    def add_source_kind(self, source_kind: SourceKindVal) -> SourceKindId:
        """
        Adds a new source kind to the database if it doesn't exist already.
        Returns -1 if invalid source kind.
        """
        # Check if source kind exists first
        existing_id = self.get_source_kind_id(source_kind)
        if existing_id != -1:
            return existing_id

        # Insert the new source kind
        response = (
            self.connection.table("source_kind")
            .insert({"kind": source_kind.value})
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return SourceKindId(-1)

        return SourceKindId(response.data[0]["id"])

    def get_source_kind_id(self, source_kind: SourceKindVal) -> SourceKindId:
        """
        Returns the id of a source kind. Returns -1 if the kind doesn't exist.
        """
        response = (
            self.connection.table("source_kind")
            .select("id")
            .eq("kind", source_kind.value)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return SourceKindId(-1)

        return SourceKindId(response.data[0]["id"])

    def get_source_kind(
        self, source_kind_id: SourceKindId
    ) -> Union[SourceKind, None]:
        """
        Returns a SourceKind object. Returns None if the kind doesn't
        exist.
        """
        response = (
            self.connection.table("source_kind")
            .select("*")
            .eq("id", source_kind_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return None

        return parse_obj_as(SourceKind, response.data[0])

    def add_source(self, source: Source) -> SourceId:
        """
        Adds a new source to the database if it doesn't exist already.
        Returns -1 if aborted because of invalid source kind id.
        """
        if not self.get_source_kind(source.source_kind_id):
            return SourceId(-1)

        # Check if source exists first
        existing_id = self.get_source_id(source.title, source.source_kind_id)
        if existing_id != -1:
            return existing_id

        # Insert the new source
        response = (
            self.connection.table("source")
            .insert(
                {
                    "title": source.title,
                    "source_kind_id": source.source_kind_id,
                    "author": source.author,
                    "lang": source.lang,
                    "removed_lemmata_num": 0,  # Default value
                }
            )
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return SourceId(-1)

        return SourceId(response.data[0]["id"])

    def get_source_id(
        self, title: str, source_kind_id: SourceKindId
    ) -> SourceId:
        """
        Returns the id of a source. Returns -1 if the source doesn't exist.
        """
        response = (
            self.connection.table("source")
            .select("id")
            .eq("title", title)
            .eq("source_kind_id", source_kind_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return SourceId(-1)

        return SourceId(response.data[0]["id"])

    def get_source(self, source_id: SourceId) -> Union[Source, None]:
        """
        Returns a Source object. Returns None if the source doesn't
        exist.
        """
        response = (
            self.connection.table("source")
            .select("*")
            .eq("id", source_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return None

        return parse_obj_as(Source, response.data[0])

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
        query = self.connection.table("source").select("*")

        # Apply any filters if provided
        if filter_params:
            for col_name, value in filter_params.items():
                query = query.eq(col_name, value)

        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size - 1

        response = query.order("id").range(start, end).execute()

        if not response.data:
            return []

        return [parse_obj_as(Source, item) for item in response.data]

    def add_status(self, status_val: StatusVal) -> StatusId:
        """
        Adds a new status to the database if it doesn't exist already.
        Returns -1 if invalid status.
        """
        # Check if status exists first
        existing_id = self.get_status_id(status_val)
        if existing_id != -1:
            return existing_id

        # Insert new status
        response = (
            self.connection.table("lemma_status")
            .insert({"status": status_val.value})
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return StatusId(-1)

        return StatusId(response.data[0]["id"])

    def get_status_id(self, status_val: StatusVal) -> StatusId:
        """
        Returns the id of a status. Returns -1 if the status doesn't exist.
        """
        response = (
            self.connection.table("lemma_status")
            .select("id")
            .eq("status", status_val.value)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return StatusId(-1)

        return StatusId(response.data[0]["id"])

    def get_status_by_id(self, status_id: StatusId) -> Union[Status, None]:
        """
        Returns the status of a lemma. Returns None if the status doesn't
        exist.
        """
        response = (
            self.connection.table("lemma_status")
            .select("*")
            .eq("id", status_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return None

        return parse_obj_as(Status, response.data[0])

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

        # Insert new lemma using Supabase
        response = (
            self.connection.table("lemma")
            .insert(
                {
                    "lemma": lemma.lemma,
                    "status_id": lemma.status_id,
                    "found_in_source": lemma.found_in_source,
                }
            )
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return LemmaId(-1)

        return LemmaId(response.data[0]["id"])

    def bulk_add_lemma(
        self,
        lemmata_values: list[str],
        status_id: StatusId,
        found_in_source: SourceId,
    ) -> dict[str, LemmaId]:
        """
        Bulk adds lemmata. Skips those that are already in the database.
        Returns map of lemma->id
        """
        # Verify status exists
        if not self.get_status_by_id(status_id):
            return {}

        # Verify source exists
        if not self.get_source(found_in_source):
            return {}

        result = {}
        remaining_lemmata = []

        # Check which lemmata already exist
        for lemma in lemmata_values:
            lemma_id = self.get_lemma_id(lemma)
            if lemma_id != -1:
                result[lemma] = lemma_id
            else:
                remaining_lemmata.append(lemma)

        # Insert new lemmata in batches if any remain
        if remaining_lemmata:
            # Prepare batch data for insert
            insert_data = [
                {
                    "lemma": lemma,
                    "status_id": status_id,
                    "found_in_source": found_in_source,
                }
                for lemma in remaining_lemmata
            ]

            # Batch insert using Supabase
            response = (
                self.connection.table("lemma").insert(insert_data).execute()
            )

            if response.data:
                # Map the inserted lemmata to their new IDs
                for item in response.data:
                    result[item["lemma"]] = item["id"]

        return result

    def get_lemma(self, lemma_id: LemmaId) -> Union[Lemma, None]:
        """
        Returns a lemma. Returns None if the lemma doesn't exist.
        """
        response = (
            self.connection.table("lemma")
            .select("*")
            .eq("id", lemma_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return None

        return parse_obj_as(Lemma, response.data[0])

    def bulk_get_lemmata(self, lemma_ids: list[LemmaId]) -> list[Lemma]:
        """
        Retrieve multiple lemmata by their IDs
        """
        if not lemma_ids:
            return []

        lemma_ids = list(OrderedDict.fromkeys(lemma_ids))

        # Using Supabase's .in_() filter to get multiple lemmata at once
        response = (
            self.connection.table("lemma")
            .select("*")
            .in_("id", lemma_ids)
            .execute()
        )

        if not response.data:
            return []

        return [parse_obj_as(Lemma, item) for item in response.data]

    def get_status_lemma_rows(
        self,
        status_val: StatusVal,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Lemma]:
        """
        Returns a list of all lemmata with the given status.
        """
        status_id = self.get_status_id(status_val)

        # Set up pagination
        start = (page - 1) * page_size
        end = start + page_size - 1

        # Query for lemmata with the given status
        response = (
            self.connection.table("lemma")
            .select("*")
            .eq("status_id", status_id)
            .order("id")
            .range(start, end)
            .execute()
        )

        if not response.data:
            return []

        return [parse_obj_as(Lemma, item) for item in response.data]

    def get_status_lemma_rows_table(
        self,
        status_val: StatusVal,
        page: int = 1,
        page_size: int = 100,
    ) -> str:
        """
        Returns a tabulated string representation of all lemmata with the
        given status.
        """
        status_id = self.get_status_id(status_val)

        # Set up pagination
        start = (page - 1) * page_size
        end = start + page_size - 1

        # Query for lemmata with the given status
        response = (
            self.connection.table("lemma")
            .select("*")
            .eq("status_id", status_id)
            .order("id")
            .range(start, end)
            .execute()
        )

        if not response.data:
            return "No data found"

        # Convert to tabular format
        columns = list(response.data[0].keys())
        rows = [[item[col] for col in columns] for item in response.data]
        return tabulate(rows, headers=columns)

    def get_lemma_id(self, lemma_value: str) -> LemmaId:
        """
        Returns the id of a lemma. Returns -1 if the lemma doesn't exist.
        """
        response = (
            self.connection.table("lemma")
            .select("id")
            .eq("lemma", lemma_value)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return LemmaId(-1)

        return LemmaId(response.data[0]["id"])

    def bulk_get_lemma_id_dict(
        self, lemmata_values: list[str]
    ) -> dict[str, LemmaId]:
        """
        Returns a dictionary mapping lemma values to their IDs
        """
        if not lemmata_values:
            return {}

        # Using Supabase's .in_() filter to get multiple lemmata at once
        response = (
            self.connection.table("lemma")
            .select("id, lemma")
            .in_("lemma", lemmata_values)
            .execute()
        )

        if not response.data:
            return {}

        # Map lemma values to IDs
        return {item["lemma"]: LemmaId(item["id"]) for item in response.data}

    def get_lemma_status(self, lemma_id: LemmaId) -> Union[Status, None]:
        """
        Returns the status of a lemma. Returns None if the lemma id is invalid
        """
        # First get the lemma to find its status_id
        response = (
            self.connection.table("lemma")
            .select("status_id")
            .eq("id", lemma_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return None

        # Then get the status using the status_id
        status_id = response.data[0]["status_id"]
        return self.get_status_by_id(status_id)

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

        # Insert new relation using Supabase
        response = (
            self.connection.table("lemma_source")
            .insert(
                {
                    "lemma_id": lemma_source_relation.lemma_id,
                    "source_id": lemma_source_relation.source_id,
                }
            )
            .execute()
        )

        return response.data is not None and len(response.data) > 0

    def bulk_add_lemma_source_relations(
        self, rels: list[LemmaSourceRelation]
    ) -> bool:
        """
        Add multiple lemma-source relations at once
        """
        if not rels:
            return False

        if not self.get_source(rels[0].source_id):
            return False

        # Remove duplicates
        rels = [rel for i, rel in enumerate(rels) if rel not in rels[i + 1 :]]

        if not self._all_lemmata_exist([rel.lemma_id for rel in rels]):
            return False

        # Prepare data for bulk insert
        insert_data = [
            {"lemma_id": rel.lemma_id, "source_id": rel.source_id}
            for rel in rels
        ]

        # Batch insert using Supabase
        response = (
            self.connection.table("lemma_source").insert(insert_data).execute()
        )

        return response.data is not None and len(response.data) > 0

    def get_lemma_sources(self, lemma_id: LemmaId) -> list[Source]:
        """
        Returns all sources in which a lemma appears in.
        """
        # First get source IDs from lemma_source table
        response = (
            self.connection.table("lemma_source")
            .select("source_id")
            .eq("lemma_id", lemma_id)
            .execute()
        )

        if not response.data:
            return []

        # Extract unique source IDs
        source_ids = [SourceId(item["source_id"]) for item in response.data]

        # Get all sources using these IDs
        sources = []
        for source_id in source_ids:
            if source := self.get_source(source_id):
                sources.append(source)

        return sources

    def get_lemma_source_relation_ids(
        self,
        lemma_id: LemmaId,
        source_id: SourceId,
        limit: Union[int, None] = None,
    ) -> list[LemmaSourceId]:
        """
        Returns the ids of all lemma-source relations.
        """
        query = (
            self.connection.table("lemma_source")
            .select("id")
            .eq("lemma_id", lemma_id)
            .eq("source_id", source_id)
            .order("id", desc=True)
        )

        # Apply limit if provided
        if limit is not None:
            query = query.limit(limit)

        response = query.execute()

        if not response.data:
            return []

        return [LemmaSourceId(item["id"]) for item in response.data]

    def add_context(self, context: Context) -> ContextId:
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

        # Check if context exists first
        if (
            context_id := self.get_context_id(
                context.context_value, context.source_id
            )
        ) != -1:
            return context_id

        # Insert new context using Supabase
        response = (
            self.connection.table("context")
            .insert(
                {
                    "context_value": context.context_value,
                    "source_id": context.source_id,
                }
            )
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return ContextId(-1)

        return ContextId(response.data[0]["id"])

    def get_context(self, context_id: ContextId) -> Union[Context, None]:
        """
        Returns a context. Returns None if the context doesn't
        exist.
        """
        response = (
            self.connection.table("context")
            .select("*")
            .eq("id", context_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return None

        return parse_obj_as(Context, response.data[0])

    def bulk_get_contexts(self, cids: list[ContextId]) -> list[Context]:
        """
        Get multiple contexts by their IDs
        """
        if not cids:
            return []

        cids = list(OrderedDict.fromkeys(cids))

        # Using Supabase's in_ filter to retrieve multiple contexts at once
        response = (
            self.connection.table("context")
            .select("*")
            .in_("id", cids)
            .execute()
        )

        if not response.data:
            return []

        return [parse_obj_as(Context, item) for item in response.data]

    def get_paginated_contexts(
        self, page: int, page_size: int
    ) -> list[Context]:
        """
        Returns a list of contexts.
        """
        # Set up pagination
        start = (page - 1) * page_size
        end = start + page_size - 1

        # Query using Supabase
        response = (
            self.connection.table("context")
            .select("*")
            .order("id")
            .range(start, end)
            .execute()
        )

        if not response.data:
            return []

        return [parse_obj_as(Context, item) for item in response.data]

    def get_paginated_source_contexts(
        self, source_id: SourceId, page: int, page_size: int
    ) -> list[Context]:
        """
        Returns a list of contexts from a specific source with pagination.
        """
        # Set up pagination
        start = (page - 1) * page_size
        end = start + page_size - 1

        # Query using Supabase
        response = (
            self.connection.table("context")
            .select("*")
            .eq("source_id", source_id)
            .order("id")
            .range(start, end)
            .execute()
        )

        if not response.data:
            return []

        return [parse_obj_as(Context, item) for item in response.data]

    def get_context_id(
        self, context_value: str, source_id: SourceId
    ) -> ContextId:
        """
        Returns the id of a context. Returns -1 if the context doesn't exist.
        """
        # Using Supabase to query for context
        response = (
            self.connection.table("context")
            .select("id")
            .eq("context_value", context_value)
            .eq("source_id", source_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return ContextId(-1)

        return ContextId(response.data[0]["id"])

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

        # Insert using Supabase
        response = (
            self.connection.table("lemma_context")
            .insert(
                {
                    "lemma_id": lemma_context.lemma_id,
                    "context_id": lemma_context.context_id,
                    "upos_tag": lemma_context.upos_tag.value,
                    "detailed_tag": lemma_context.detailed_tag,
                }
            )
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return LemmaContextId(-1)

        return LemmaContextId(response.data[0]["id"])

    def bulk_add_lemma_context_relations(
        self, rels: list[LemmaContextRelation]
    ) -> bool:
        """
        Add multiple lemma-context relations at once
        """
        if not rels:
            return False

        if not self._all_lemmata_exist([rel.lemma_id for rel in rels]):
            return False

        if not self._all_contexts_exist([rel.context_id for rel in rels]):
            return False

        # Remove duplicates
        rels = [rel for i, rel in enumerate(rels) if rel not in rels[i + 1 :]]

        # Prepare data for bulk insert
        insert_data = []
        for rel in rels:
            insert_data.append(
                {
                    "lemma_id": rel.lemma_id,
                    "context_id": rel.context_id,
                    "upos_tag": rel.upos_tag.value,
                    "detailed_tag": rel.detailed_tag,
                }
            )

        # Batch insert using Supabase
        response = (
            self.connection.table("lemma_context")
            .insert(insert_data)
            .execute()
        )

        return response.data is not None and len(response.data) > 0

    def get_lemma_context_relation(
        self, lemma_context_id: LemmaContextId
    ) -> Union[LemmaContextRelation, None]:
        """
        Returns a lemma-context relation.
        """
        response = (
            self.connection.table("lemma_context")
            .select("*")
            .eq("id", lemma_context_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return None

        # Convert upos_tag string value to UposTag enum
        result_data = response.data[0]
        return parse_obj_as(LemmaContextRelation, result_data)

    def get_lemma_contexts(
        self, lemma_id: LemmaId, page: int, page_size: int
    ) -> list[Context]:
        """
        Returns all contexts a lemma appears in.
        """
        # Calculate pagination limits
        limit = page_size
        offset = (page - 1) * page_size

        # First get context_ids from lemma_context table
        response = (
            self.connection.table("lemma_context")
            .select("context_id")
            .eq("lemma_id", lemma_id)
            .order("context_id")
            .range(offset, offset + limit - 1)
            .execute()
        )

        if not response.data:
            return []

        # Extract unique context IDs
        context_ids = sorted({item["context_id"] for item in response.data})

        # Now fetch the actual contexts
        if not context_ids:
            return []

        contexts_response = (
            self.connection.table("context")
            .select("*")
            .in_("id", context_ids)
            .execute()
        )

        if not contexts_response.data:
            return []

        return [parse_obj_as(Context, item) for item in contexts_response.data]

    def get_lemma_context_relations(
        self, lemma_context: LemmaContextRelation
    ) -> list[LemmaContextRelation]:
        """
        Returns the ids of all lemma-context relations matching the arg.
        Returns -1 if the relation doesn't exist.
        lemma_context.id of arg is ignored.
        """
        # Filter out id field from query parameters
        keys_to_exclude = {"id"}
        d = lemma_context.dict(exclude=keys_to_exclude)

        # Query using Supabase
        query = (
            self.connection.table("lemma_context")
            .select("*")
            .eq("lemma_id", d["lemma_id"])
            .eq("context_id", d["context_id"])
            .eq("upos_tag", lemma_context.upos_tag.value)
        )

        if d.get("detailed_tag"):
            query = query.eq("detailed_tag", d["detailed_tag"])

        response = query.execute()

        if not response.data:
            return []

        return [
            parse_obj_as(LemmaContextRelation, item) for item in response.data
        ]

    def get_status(self, status_id: StatusId) -> Union[Status, None]:
        """
        Returns a status.
        """
        # This is the same as get_status_by_id, using Supabase
        response = (
            self.connection.table("lemma_status")
            .select("*")
            .eq("id", status_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return None

        return parse_obj_as(Status, response.data[0])

    def update_lemmata_status(
        self, lemma_ids: list[LemmaId], new_status_id: StatusId
    ) -> bool:
        """
        Changes the status of all lemmata in the list.
        Doesn't update any of them if one of the ids doesn't exist.
        """
        # Verify new status exists
        if not self.get_status_by_id(new_status_id):
            return False

        # Verify all lemma IDs exist
        for lid in lemma_ids:
            if not self.get_lemma(lid):
                return False
            if s := self.get_lemma_status(lid):
                if s.id == new_status_id:
                    return False

        # Update using Supabase
        response = (
            self.connection.table("lemma")
            .update({"status_id": new_status_id})
            .in_("id", lemma_ids)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return False

        # Verify update was successful
        if lemma_ids:
            status = self.get_lemma_status(lemma_ids[0])
            return status is not None and status.id == new_status_id
        return True

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
        # Check if relation exists
        if not self.get_lemma_context_relation(lemma_context_id):
            return False

        # Nothing to update
        if new_upos_tag is None and new_detailed_tag is None:
            return False

        # Prepare update data
        update_data = {}
        if new_upos_tag is not None:
            update_data["upos_tag"] = new_upos_tag.value
        if new_detailed_tag is not None:
            update_data["detailed_tag"] = new_detailed_tag

        # Update using Supabase
        response = (
            self.connection.table("lemma_context")
            .update(update_data)
            .eq("id", lemma_context_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            return False

        # Verify update was successful
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
        # Check if lemma exists
        lemma = self.get_lemma(lemma_id)
        if not lemma:
            return False

        # Get the found_in_source of the lemma before deleting
        found_in_source = lemma.found_in_source

        # Get all context IDs associated with the lemma from lemma_context
        response = (
            self.connection.table("lemma_context")
            .select("context_id")
            .eq("lemma_id", lemma_id)
            .execute()
        )
        context_ids = {
            ContextId(item["context_id"]) for item in response.data or []
        }

        # For each context ID, update the context_value to remove this
        # lemma_id references
        for context_id in context_ids:
            # First get the context value
            context_response = (
                self.connection.table("context")
                .select("context_value")
                .eq("id", context_id)
                .execute()
            )
            if context_response.data and len(context_response.data) > 0:
                context_value = context_response.data[0]["context_value"]
                # Remove lemma_id references using regex
                updated_context_value = re.sub(
                    rf"(::{lemma_id})(\D)", r"\g<2>", context_value
                )
                # Update the context value
                self.connection.table("context").update(
                    {"context_value": updated_context_value}
                ).eq("id", context_id).execute()

        # Delete all entries in lemma_context with this lemma_id
        self.connection.table("lemma_context").delete().eq(
            "lemma_id", lemma_id
        ).execute()

        # Delete all entries in lemma_source with this lemma_id
        self.connection.table("lemma_source").delete().eq(
            "lemma_id", lemma_id
        ).execute()

        # If the source exists, increase its removed_lemmata_num counter
        source = self.get_source(found_in_source)
        if source:
            self.connection.table("source").update(
                {"removed_lemmata_num": source.removed_lemmata_num + 1}
            ).eq("id", found_in_source).execute()

        # Finally delete the lemma itself
        self.connection.table("lemma").delete().eq("id", lemma_id).execute()

        # Verify deletion was successful
        return self.get_lemma(lemma_id) is None

    def bulk_delete_lemmata(self, lemma_ids: set[LemmaId]) -> bool:
        """
        Bulk delete multiple lemmata and their related data
        """
        lemma_ids = list(lemma_ids)
        if not self._all_lemmata_exist(lemma_ids):
            return False

        # Get all lemma data before deletion
        lemmata = self.bulk_get_lemmata(lemma_ids)

        # Track source IDs for later updating removed_lemmata_num
        source_counter = Counter([lemma.found_in_source for lemma in lemmata])

        # Get all context IDs associated with the lemmata from lemma_context
        response = (
            self.connection.table("lemma_context")
            .select("context_id")
            .in_("lemma_id", lemma_ids)
            .execute()
        )
        context_ids = {
            ContextId(item["context_id"]) for item in response.data or []
        }

        # For each context ID, update the context_value to remove lemma_id
        # references
        for context_id in context_ids:
            # First get the context value
            context_response = (
                self.connection.table("context")
                .select("context_value")
                .eq("id", context_id)
                .execute()
            )
            if context_response.data and len(context_response.data) > 0:
                context_value = context_response.data[0]["context_value"]
                updated_context_value = context_value

                # Apply regex replacement for each lemma ID
                for lemma_id in lemma_ids:
                    updated_context_value = re.sub(
                        rf"(::{lemma_id})(\D)", r"\g<2>", updated_context_value
                    )

                # Update the context value if changed
                if updated_context_value != context_value:
                    self.connection.table("context").update(
                        {"context_value": updated_context_value}
                    ).eq("id", context_id).execute()

        # Delete all entries in lemma_context with these lemma_ids
        self.connection.table("lemma_context").delete().in_(
            "lemma_id", lemma_ids
        ).execute()

        # Delete all entries in lemma_source with these lemma_ids
        self.connection.table("lemma_source").delete().in_(
            "lemma_id", lemma_ids
        ).execute()

        # Update removed_lemmata_num for each affected source
        for source_id, count in source_counter.items():
            source = self.get_source(source_id)
            if source:
                self.connection.table("source").update(
                    {"removed_lemmata_num": source.removed_lemmata_num + count}
                ).eq("id", source_id).execute()

        # Finally delete the lemmata themselves
        self.connection.table("lemma").delete().in_("id", lemma_ids).execute()

        # Verify deletion was successful (none of the lemmata should exist
        # anymore)
        return len(self.bulk_get_lemmata(lemma_ids)) == 0

    def _all_lemmata_exist(self, lemma_ids: list[LemmaId]) -> bool:
        """
        Check if all lemmata in a list exist
        """
        if not lemma_ids:
            return True

        # Supabase requires a different approach than count(*)
        response = (
            self.connection.table("lemma")
            .select("id")
            .in_("id", lemma_ids)
            .execute()
        )

        if not response.data:
            return False

        # Compare the count of returned IDs with the count of requested IDs
        return len(response.data) == len(lemma_ids)

    def _all_contexts_exist(self, context_ids: list[ContextId]) -> bool:
        """
        Check if all contexts in a list exist
        """
        if not context_ids:
            return True

        response = (
            self.connection.table("context")
            .select("id")
            .in_("id", context_ids)
            .execute()
        )

        if not response.data:
            return False

        # Compare the count of returned IDs with the count of requested IDs
        return len(response.data) == len(context_ids)

    def delete_lemma_context_relation(
        self, lemma_context_id: LemmaContextId
    ) -> bool:
        """
        Deletes a lemma-context relation from the database.
        """
        # Check if relation exists first
        if not self.get_lemma_context_relation(lemma_context_id):
            return False

        # Delete using Supabase
        response = (
            self.connection.table("lemma_context")
            .delete()
            .eq("id", lemma_context_id)
            .execute()
        )

        return response.data is not None and len(response.data) > 0


if __name__ == "__main__":
    """
    Examples of how to use the Supabase-based LexDbIntegrator
    """
    # Initialize connection to Supabase
    db = LexDbIntegrator(DbEnvironment.DEV)
    sk_id = db.add_source_kind(SourceKindVal.BOOK)
    print(f"Added source kind with ID: {sk_id}")

    db.truncate_all_tables()
