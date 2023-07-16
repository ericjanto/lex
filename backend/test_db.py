import subprocess

import pytest

from backend.db import LexDbIntegrator
from backend.dbtypes import (
    Context,
    ContextId,
    DbEnvironment,
    Lemma,
    LemmaContextId,
    LemmaContextRelation,
    LemmaId,
    LemmaSourceRelation,
    Source,
    SourceId,
    SourceKindId,
    SourceKindVal,
    StatusId,
    StatusVal,
    UposTag,
)
from backend.utils import relativy_path


@pytest.fixture
def db():
    db = LexDbIntegrator(DbEnvironment.DEVADMIN)
    db.truncate_all_tables()
    yield db
    db.truncate_all_tables()
    db.close_connection()


db_changed = pytest.mark.skipif(
    condition=not bool(
        subprocess.run(
            ["git", "diff", "--exit-code", relativy_path("db.py")]
        ).returncode
    ),
    reason="db.py has not changed",
)


class TestInexpensiveDbMethods:
    def test_connection_initialisation(self, db: LexDbIntegrator):
        assert db.connection.open

    def test_close_connection(self):
        db = LexDbIntegrator(DbEnvironment.DEV)
        assert not db.connection.closed
        db.close_connection()
        assert db.connection.closed

    def test_empty_all_tables_prod_fail(self):
        db = LexDbIntegrator(DbEnvironment.PROD)
        with pytest.raises(AssertionError):
            db.truncate_all_tables()


@db_changed
class TestExpensiveDbMethods:
    def test_truncate_all_tables_success(self, db: LexDbIntegrator):
        cursor = db.connection.cursor()

        # Populate tables | sourcery skip: no-loop-in-tests
        tables = [
            "source_kind",
            "lemma_status",
            "lemma",
            "source",
            "lemma_source",
            "context",
            "lemma_context",
        ]

        db.add_source_kind(SourceKindVal.BOOK)
        # add new lemma_status
        status_id = db.add_status(StatusVal.PENDING)
        # add new lemma
        lemma_id = db.add_lemma(Lemma(lemma="hobbit", status_id=status_id))
        # add new source
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        # add new lemma_source
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        # add new context
        context_id = db.add_context(
            Context(context_value="somecontext", source_id=source_id)
        )
        # add new lemma_context
        db.add_lemma_context_relation(
            LemmaContextRelation(
                lemma_id=lemma_id,
                context_id=context_id,
                upos_tag=UposTag.NOUN,
                detailed_tag="NN",
            )
        )

        # Validate that the tables are not empty | sourcery skip:
        # no-loop-in-tests
        for table in tables[:1]:  # TODO: ammend this
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            assert cursor.fetchone()[0] > 0

        db.truncate_all_tables()

        # Validate that the tables are empty | sourcery skip: no-loop-in-tests
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            assert cursor.fetchone()[0] == 0

        cursor.close()

    def test_add_source_kind_success(self, db: LexDbIntegrator):
        assert db.add_source_kind(SourceKindVal.BOOK) > 0

    def test_add_source_kind_same_id(self, db: LexDbIntegrator):
        source_kind_id_first = db.add_source_kind(SourceKindVal.BOOK)
        source_kind_id_second = db.add_source_kind(SourceKindVal.BOOK)
        assert source_kind_id_first == source_kind_id_second

    def test_get_source_kind_id_invalid_kind(self, db: LexDbIntegrator):
        db.truncate_all_tables()
        assert db.get_source_kind_id(SourceKindVal.BOOK) == -1

    def test_get_source_kind_id_valid_kind(self, db: LexDbIntegrator):
        db.truncate_all_tables()
        db.add_source_kind(SourceKindVal.BOOK)
        assert db.get_source_kind_id(SourceKindVal.BOOK) == 1

    def test_get_source_kind_invalid_id(self, db: LexDbIntegrator):
        assert db.get_source_kind(SourceKindId(-1)) is None

    def test_add_source_success_valid_source_kind_id(
        self, db: LexDbIntegrator
    ):
        db.truncate_all_tables()
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        assert (
            db.add_source(
                Source(title="The Hobbit", source_kind_id=source_kind_id)
            )
            == 1
        )

    def test_add_source_fails_invalid_source_kind_id(
        self, db: LexDbIntegrator
    ):
        assert (
            db.add_source(
                Source(title="The Hobbit", source_kind_id=SourceKindId(-1))
            )
            == -1
        )

    def test_add_source_twice_same_id(self, db: LexDbIntegrator):
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id_first = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        source_id_second = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        assert source_id_first == source_id_second

    def test_get_source_id_invalid_source(self, db: LexDbIntegrator):
        assert db.get_source_id("invalid_source", SourceKindId(-1)) == -1

    def test_get_source_id_valid_source(self, db: LexDbIntegrator):
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        assert db.get_source_id("The Hobbit", source_kind_id) == source_id

    def test_get_source(self, db: LexDbIntegrator):
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source = Source(title="The Hobbit", source_kind_id=source_kind_id)
        source_id = db.add_source(source)
        source.id = source_id
        assert db.get_source(source_id) == source

    def test_add_status_same_status_twice(self, db: LexDbIntegrator):
        status_id_1 = db.add_status(StatusVal.ACCEPTED)
        status_id_2 = db.add_status(StatusVal.ACCEPTED)
        assert status_id_1 == status_id_2

    def test_add_status_valid_status(self, db: LexDbIntegrator):
        db.truncate_all_tables()
        assert db.add_status(StatusVal.PENDING) == 1

    def test_get_status_id_valid_status(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        assert db.get_status_id(StatusVal.PENDING) == status_id

    def test_get_status_by_id_invalid_status_id(self, db: LexDbIntegrator):
        assert db.get_status_by_id(StatusId(-1)) is None

    def test_get_status_by_id_valid_status_id(self, db: LexDbIntegrator):
        status_val = StatusVal.PENDING
        status_id = db.add_status(status_val)
        assert (s := db.get_status_by_id(status_id)) is not None
        assert s.status == status_val

    def test_get_lemma_status_invalid_lemma_id(self, db: LexDbIntegrator):
        assert db.get_lemma_status(LemmaId(-1)) is None

    def test_get_status_by_lemma_valid_lemma_id(self, db: LexDbIntegrator):
        status_val = StatusVal.PENDING
        status_id = db.add_status(status_val)
        lemma_id = db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id))
        assert (s := db.get_lemma_status(lemma_id)) is not None
        assert s.status == status_val

    def test_add_lemma_invalid_status_id(self, db: LexDbIntegrator):
        assert (
            db.add_lemma(Lemma(lemma="test-lemma", status_id=StatusId(-1)))
            == -1
        )

    def test_add_lemma_valid_status_id(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        assert (
            db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id)) != -1
        )

    def test_add_lemma_same_lemma_twice(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id_1 = db.add_lemma(
            Lemma(lemma="test-lemma", status_id=status_id)
        )
        lemma_id_2 = db.add_lemma(
            Lemma(lemma="test-lemma", status_id=status_id)
        )
        assert lemma_id_1 == lemma_id_2

    def test_get_lemma_id_invalid_lemma(self, db: LexDbIntegrator):
        assert db.get_lemma_id("invalid_lemma") == -1

    def test_get_lemma_id_valid_lemma(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        db.add_lemma(Lemma(lemma="test_lemma", status_id=status_id))
        assert db.get_lemma_id("test_lemma") != -1

    def test_get_lemma_invalid_lemma_id(self, db: LexDbIntegrator):
        assert db.get_lemma(LemmaId(-1)) is None

    def test_get_lemma_valid_lemma_id(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id = db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id))
        assert db.get_lemma(lemma_id) is not None

    def test_add_lemma_source_invalid_ids(self, db: LexDbIntegrator):
        assert (
            db.add_lemma_source_relation(
                LemmaSourceRelation(
                    lemma_id=LemmaId(-1), source_id=SourceId(-1)
                )
            )
            == -1
        )

    def test_add_lemma_source_valid_ids(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id = db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id))
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        assert (
            db.add_lemma_source_relation(
                LemmaSourceRelation(lemma_id=lemma_id, source_id=source_id)
            )
            != -1
        )

    def test_get_lemma_source_ids_invalid_ids(self, db: LexDbIntegrator):
        assert (
            db.get_lemma_source_relation_ids(LemmaId(-1), SourceId(-1)) == []
        )

    def test_get_lemma_sources_ids_valid_lemma_id(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id = db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id))
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id_1 = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        source_id_2 = db.add_source(
            Source(title="The Hobbit 2", source_kind_id=source_kind_id)
        )
        db.add_lemma_source_relation(
            LemmaSourceRelation(lemma_id=lemma_id, source_id=source_id_1)
        )
        db.add_lemma_source_relation(
            LemmaSourceRelation(lemma_id=lemma_id, source_id=source_id_2)
        )
        assert [ls.id for ls in db.get_lemma_sources(lemma_id)] == [
            source_id_1,
            source_id_2,
        ]

    def test_get_lemma_source_invalid_lemma_id(self, db: LexDbIntegrator):
        assert db.get_lemma_sources(LemmaId(-1)) == []

    def test_get_lemma_source_ids_valid_ids(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id = db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id))
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        db.add_lemma_source_relation(
            LemmaSourceRelation(lemma_id=lemma_id, source_id=source_id)
        )
        db.add_lemma_source_relation(
            LemmaSourceRelation(lemma_id=lemma_id, source_id=source_id)
        )
        assert len(db.get_lemma_source_relation_ids(lemma_id, source_id)) == 2

    def test_add_context_invalid_source_id(self, db: LexDbIntegrator):
        assert (
            db.add_context(
                Context(context_value="context", source_id=SourceId(-1))
            )
            == -1
        )

    def test_add_context_valid_source_id(self, db: LexDbIntegrator):
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        assert (
            db.add_context(
                Context(context_value="context", source_id=source_id)
            )
            != -1
        )

    def test_add_context_same_context_twice(self, db: LexDbIntegrator):
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        context_id_1 = db.add_context(
            Context(context_value="context", source_id=source_id)
        )
        context_id_2 = db.add_context(
            Context(context_value="context", source_id=source_id)
        )
        assert context_id_1 == context_id_2

    def test_get_context_id_invalid_context(self, db: LexDbIntegrator):
        assert db.get_context_id("invalid_context", SourceId(-1)) == -1

    def test_get_context_id_valid_context(self, db: LexDbIntegrator):
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        db.add_context(Context(context_value="context", source_id=source_id))
        assert db.get_context_id("context", source_id) != -1

    def test_get_context_invalid_context_id(self, db: LexDbIntegrator):
        assert db.get_context(ContextId(-1)) is None

    def test_get_context_valid_context_id(self, db: LexDbIntegrator):
        db.truncate_all_tables()
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        context_id = db.add_context(
            Context(context_value="context", source_id=source_id)
        )
        assert db.get_context(context_id) is not None

    def test_add_lemma_context_invalid_ids(self, db: LexDbIntegrator):
        assert (
            db.add_lemma_context_relation(
                LemmaContextRelation(
                    lemma_id=LemmaId(-1),
                    context_id=ContextId(-1),
                    upos_tag=UposTag.NOUN,
                    detailed_tag="NNP",
                )
            )
            == -1
        )

    def test_add_lemma_context_valid_ids(self, db: LexDbIntegrator):
        db.truncate_all_tables()
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id = db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id))
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        context_id = db.add_context(
            Context(context_value="context", source_id=source_id)
        )
        assert (
            db.add_lemma_context_relation(
                LemmaContextRelation(
                    lemma_id=lemma_id,
                    context_id=context_id,
                    upos_tag=UposTag.NOUN,
                    detailed_tag="NNP",
                )
            )
            != -1
        )

    def test_get_lemma_context_relations_invalid_ids(
        self, db: LexDbIntegrator
    ):
        assert (
            db.get_lemma_context_relations(
                LemmaContextRelation(
                    lemma_id=LemmaId(-1),
                    context_id=ContextId(-1),
                    upos_tag=UposTag.NOUN,
                    detailed_tag="NNP",
                )
            )
            == []
        )

    def test_get_lemma_context_relations_valid_ids(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id = db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id))
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        context_id = db.add_context(
            Context(context_value="context", source_id=source_id)
        )
        lcr = LemmaContextRelation(
            lemma_id=lemma_id,
            context_id=context_id,
            upos_tag=UposTag.NOUN,
            detailed_tag="NNP",
        )
        db.add_lemma_context_relation(lcr)
        db.add_lemma_context_relation(lcr)
        assert len(db.get_lemma_context_relations(lcr)) == 2

    def test_change_lemma_status_invalid_id(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        assert db.update_lemma_status(LemmaId(-1), status_id) is False

    def test_change_lemma_status_valid_ids(self, db: LexDbIntegrator):
        old_status_id = db.add_status(StatusVal.PENDING)
        new_status_id = db.add_status(StatusVal.ACCEPTED)
        lemma_id = db.add_lemma(
            Lemma(lemma="test_lemma", status_id=old_status_id)
        )
        assert db.update_lemma_status(lemma_id, new_status_id)

    def test_change_lemma_context_upos_tag_invalid_ids(
        self, db: LexDbIntegrator
    ):
        assert (
            db.update_lemma_context_relation(
                LemmaContextId(-1), new_upos_tag=UposTag.NOUN
            )
            is False
        )

    def test_change_lemma_context_upos_tag_valid_ids(
        self, db: LexDbIntegrator
    ):
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id = db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id))
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        context_id = db.add_context(
            Context(context_value="context", source_id=source_id)
        )
        lemma_context_id = db.add_lemma_context_relation(
            LemmaContextRelation(
                lemma_id=lemma_id,
                context_id=context_id,
                upos_tag=UposTag.NOUN,
                detailed_tag="NNP",
            )
        )
        assert db.update_lemma_context_relation(
            lemma_context_id, new_upos_tag=UposTag.VERB
        )
        lcr = db.get_lemma_context_relation(lemma_context_id)
        assert lcr is not None
        assert lcr.upos_tag == UposTag.VERB

    def test_get_lemma_context(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id = db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id))
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        context_id = db.add_context(
            Context(context_value="context", source_id=source_id)
        )
        lc = LemmaContextRelation(
            lemma_id=lemma_id,
            context_id=context_id,
            upos_tag=UposTag.NOUN,
            detailed_tag="NNP",
        )
        lemma_context_id = db.add_lemma_context_relation(lc)
        lc.id = lemma_context_id
        assert db.get_lemma_context_relation(lemma_context_id) == lc
        assert db.get_lemma_context_relation(LemmaContextId(-1)) is None

    def test_get_lemma_contexts(self, db: LexDbIntegrator):
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id = db.add_lemma(Lemma(lemma="test-lemma", status_id=status_id))
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        context_id = db.add_context(
            Context(context_value="context", source_id=source_id)
        )
        lemma_context_id = db.add_lemma_context_relation(
            LemmaContextRelation(
                lemma_id=lemma_id,
                context_id=context_id,
                upos_tag=UposTag.NOUN,
                detailed_tag="NNP",
            )
        )
        assert db.get_lemma_contexts(lemma_id)[0].id == lemma_context_id

    def test_delete_lemma_invalid_id(self, db: LexDbIntegrator):
        assert db.delete_lemma(LemmaId(-1)) is False
        # set up the test scenario described above
        status_id = db.add_status(StatusVal.PENDING)
        lemma_id_delete = db.add_lemma(
            Lemma(lemma="test-lemma", status_id=status_id)
        )
        lemma_id_remain = db.add_lemma(
            Lemma(lemma="remain-lemma", status_id=status_id)
        )
        source_kind_id = db.add_source_kind(SourceKindVal.BOOK)
        source_id_delete = db.add_source(
            Source(title="The Hobbit", source_kind_id=source_kind_id)
        )
        source_id_remain = db.add_source(
            Source(
                title="The Lord of the Rings", source_kind_id=source_kind_id
            )
        )
        context_id_delete = db.add_context(
            Context(context_value="context", source_id=source_id_delete)
        )
        context_id_remain = db.add_context(
            Context(
                context_value=(
                    f"context-remain::{lemma_id_delete}::{lemma_id_remain}"
                ),
                source_id=source_id_remain,
            )
        )
        db.add_lemma_source_relation(
            LemmaSourceRelation(
                lemma_id=lemma_id_delete, source_id=source_id_delete
            )
        )
        db.add_lemma_source_relation(
            LemmaSourceRelation(
                lemma_id=lemma_id_delete, source_id=source_id_remain
            )
        )
        db.add_lemma_source_relation(
            LemmaSourceRelation(
                lemma_id=lemma_id_remain, source_id=source_id_remain
            )
        )
        db.add_lemma_context_relation(
            LemmaContextRelation(
                lemma_id=lemma_id_delete,
                context_id=context_id_delete,
                upos_tag=UposTag.NOUN,
                detailed_tag="NNP",
            )
        )
        db.add_lemma_context_relation(
            LemmaContextRelation(
                lemma_id=lemma_id_delete,
                context_id=context_id_remain,
                upos_tag=UposTag.NOUN,
                detailed_tag="NNP",
            )
        )
        db.add_lemma_context_relation(
            LemmaContextRelation(
                lemma_id=lemma_id_remain,
                context_id=context_id_remain,
                upos_tag=UposTag.NOUN,
                detailed_tag="NNP",
            )
        )
        assert db.delete_lemma(lemma_id_delete) is True
        assert len(db.get_lemma_sources(lemma_id_delete)) == 0
        assert len(db.get_lemma_contexts(lemma_id_delete)) == 0
        assert (cr := db.get_context(context_id_remain)) is not None
        assert str(lemma_id_delete) not in cr.context_value
        assert str(lemma_id_remain) in cr.context_value
        assert db.get_lemma(lemma_id_delete) is None
