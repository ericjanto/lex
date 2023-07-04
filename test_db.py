import subprocess

import pytest

from db import LexDbIntegrator


@pytest.fixture
def lex_db_integrator():
    lex_db_integrator = LexDbIntegrator("DEV")
    lex_db_integrator.empty_all_tables()
    yield lex_db_integrator
    lex_db_integrator.close_connection()


db_changed = pytest.mark.skipif(
    condition=not bool(
        subprocess.run(["git", "diff", "--exit-code", "db.py"]).returncode
    ),
    reason="db.py has not changed",
)


class TestInexpensiveDbMethods:
    def test_connection_initialisation(self, lex_db_integrator):
        assert lex_db_integrator.connection.open

    def test_close_connection(self):
        lex_db_integrator = LexDbIntegrator("DEV")
        assert not lex_db_integrator.connection.closed
        lex_db_integrator.close_connection()
        assert lex_db_integrator.connection.closed

    def test_empty_all_tables_prod_fail(self):
        lex_db_integrator = LexDbIntegrator("PROD")
        with pytest.raises(AssertionError):
            lex_db_integrator.empty_all_tables()


@db_changed
class TestExpensiveDbMethods:
    def test_empty_all_tables_success(self, lex_db_integrator):
        cursor = lex_db_integrator.connection.cursor()

        # Populate tables | sourcery skip: no-loop-in-tests
        tables = [
            "source_kind",
            "lemma_status",
            "lemmata",
            "sources",
            "lemmata_sources",
            "context",
            "lemma_context",
        ]

        lex_db_integrator.add_source_kind("book")
        # TODO: add more data to the tables once the correspondings methods are
        # implemented

        # Validate that the tables are not empty | sourcery skip:
        # no-loop-in-tests
        for table in tables[:1]:  # TODO: ammend this
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            assert cursor.fetchone()[0] > 0

        lex_db_integrator.empty_all_tables()

        # Validate that the tables are empty | sourcery skip: no-loop-in-tests
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            assert cursor.fetchone()[0] == 0

        cursor.close()

    def test_add_source_kind_success(self, lex_db_integrator):
        assert lex_db_integrator.add_source_kind("book") > 0

    def test_add_source_kind_same_id(self, lex_db_integrator):
        source_kind_id_first = lex_db_integrator.add_source_kind("book")
        source_kind_id_second = lex_db_integrator.add_source_kind("book")
        assert source_kind_id_first == source_kind_id_second

    def test_add_source_kind_invalid_kind(self, lex_db_integrator):
        assert lex_db_integrator.add_source_kind("invalid_kind") == -1

    def test_get_source_kind_id_invalid_kind(self, lex_db_integrator):
        assert lex_db_integrator.get_source_kind_id("invalid_kind") == -1

    def test_get_source_kind_id_valid_kind(self, lex_db_integrator):
        lex_db_integrator.add_source_kind("book")
        assert lex_db_integrator.get_source_kind_id("book") != -1

    def test_get_source_kind_valid_id(self, lex_db_integrator):
        source_kind = "book"
        lex_db_integrator.add_source_kind(source_kind)
        source_kind_id = lex_db_integrator.get_source_kind_id(source_kind)
        assert lex_db_integrator.get_source_kind(source_kind_id) == source_kind

    def test_get_source_kind_invalid_id(self, lex_db_integrator):
        assert lex_db_integrator.get_source_kind(-1) is None

    # check from below

    def test_add_source_fails_invalid_source_kind_id(self, lex_db_integrator):
        assert lex_db_integrator.add_source("The Hobbit", -1) == -1

    def test_add_source_success_valid_source_kind_id(self, lex_db_integrator):
        source_kind_id = lex_db_integrator.add_source_kind("book")
        assert lex_db_integrator.add_source("The Hobbit", source_kind_id) != -1

    def test_get_source_id_invalid_source(self, lex_db_integrator):
        assert lex_db_integrator.get_source_id("invalid_source", -1) == -1

    def test_get_source_id_valid_source(self, lex_db_integrator):
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        assert (
            lex_db_integrator.get_source_id("The Hobbit", source_kind_id)
            == source_id
        )

    def test_get_source_title_invalid_source_id(self, lex_db_integrator):
        assert lex_db_integrator.get_source_title(-1) is None

    def test_get_source_title_valid_source_id(self, lex_db_integrator):
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        assert lex_db_integrator.get_source_title(source_id) == "The Hobbit"

    def test_get_source_title(self, lex_db_integrator):
        source_kind = "book"
        source_title = "The Hobbit"
        source_kind_id = lex_db_integrator.add_source_kind(source_kind)
        source_id = lex_db_integrator.add_source(source_title, source_kind_id)
        assert lex_db_integrator.get_source_title(source_id) == source_title

    def test_add_status_invalid_status(self, lex_db_integrator):
        assert lex_db_integrator.add_status(None) == -1

    def test_add_status_same_status_twice(self, lex_db_integrator):
        status = "valid_status"
        status_id_1 = lex_db_integrator.add_status(status)
        status_id_2 = lex_db_integrator.add_status(status)
        assert status_id_1 == status_id_2

    def test_add_status_valid_status(self, lex_db_integrator):
        status = "pending"
        assert lex_db_integrator.add_status(status) != -1

    def test_get_status_id_invalid_status(self, lex_db_integrator):
        assert lex_db_integrator.get_status_id("invalid_status") == -1

    def test_get_status_id_valid_status(self, lex_db_integrator):
        status = "valid_status"
        status_id = lex_db_integrator.add_status(status)
        assert lex_db_integrator.get_status_id(status) == status_id

    def test_get_status_by_id_invalid_status_id(self, lex_db_integrator):
        assert lex_db_integrator.get_status_by_id(-1) is None

    def test_get_status_by_id_valid_status_id(self, lex_db_integrator):
        status = "pending"
        status_id = lex_db_integrator.add_status(status)
        assert lex_db_integrator.get_status_by_id(status_id) == status

    def test_get_status_by_lemma_invalid_lemma_id(self, lex_db_integrator):
        assert lex_db_integrator.get_status_by_lemma(-1) is None

    def test_get_status_by_lemma_valid_lemma_id(self, lex_db_integrator):
        status = "pending"
        status_id = lex_db_integrator.add_status(status)
        lemma_id = lex_db_integrator.add_lemma("test-lemma", status_id)
        assert lex_db_integrator.get_status_by_lemma(lemma_id) == status

    def test_add_lemma_invalid_status_id(self, lex_db_integrator):
        assert lex_db_integrator.add_lemma("test-lemma", -1) == -1

    def test_add_lemma_valid_status_id(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        assert lex_db_integrator.add_lemma("test-lemma", status_id) != -1

    def test_add_lemma_same_lemma_twice(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lemma_id_1 = lex_db_integrator.add_lemma("test-lemma", status_id)
        lemma_id_2 = lex_db_integrator.add_lemma("test-lemma", status_id)
        assert lemma_id_1 == lemma_id_2

    def test_get_lemma_id_invalid_lemma(self, lex_db_integrator):
        assert lex_db_integrator.get_lemma_id("invalid_lemma") == -1

    def test_get_lemma_id_valid_lemma(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lex_db_integrator.add_lemma("test_lemma", status_id)
        assert lex_db_integrator.get_lemma_id("test_lemma") != -1

    def test_get_lemma_invalid_lemma_id(self, lex_db_integrator):
        assert lex_db_integrator.get_lemma(-1) is None

    def test_get_lemma_valid_lemma_id(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lemma_id = lex_db_integrator.add_lemma("test-lemma", status_id)
        assert lex_db_integrator.get_lemma(lemma_id) is not None

    def test_add_lemma_source_invalid_ids(self, lex_db_integrator):
        assert lex_db_integrator.add_lemmata_source(-1, -1) == -1

    def test_add_lemma_source_valid_ids(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lemma_id = lex_db_integrator.add_lemma("test-lemma", status_id)
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        assert lex_db_integrator.add_lemmata_source(lemma_id, source_id) != -1

    def test_get_lemmata_source_ids_invalid_ids(self, lex_db_integrator):
        assert lex_db_integrator.get_lemmata_source_ids(-1, -1) == []

    def test_get_lemmata_source_ids_valid_lemma_id(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lemma_id = lex_db_integrator.add_lemma("test-lemma", status_id)
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id_1 = lex_db_integrator.add_source(
            "The Hobbit", source_kind_id
        )
        source_id_2 = lex_db_integrator.add_source(
            "The Hobbit 2", source_kind_id
        )
        lex_db_integrator.add_lemmata_source(lemma_id, source_id_1)
        lex_db_integrator.add_lemmata_source(lemma_id, source_id_2)
        assert lex_db_integrator.get_lemma_sources(lemma_id) == [
            source_id_1,
            source_id_2,
        ]

    def test_get_lemma_sources_invalid_lemma_id(self, lex_db_integrator):
        assert lex_db_integrator.get_lemma_sources(-1) == []

    def test_get_lemmata_source_ids_valid_ids(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lemma_id = lex_db_integrator.add_lemma("test-lemma", status_id)
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        lex_db_integrator.add_lemmata_source(lemma_id, source_id)
        lex_db_integrator.add_lemmata_source(lemma_id, source_id)
        assert (
            len(lex_db_integrator.get_lemmata_source_ids(lemma_id, source_id))
            == 2
        )

    def test_add_context_invalid_source_id(self, lex_db_integrator):
        assert lex_db_integrator.add_context("context", -1) == -1

    def test_add_context_valid_source_id(self, lex_db_integrator):
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        assert lex_db_integrator.add_context("context", source_id) != -1

    def test_add_context_same_context_twice(self, lex_db_integrator):
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        context_id_1 = lex_db_integrator.add_context("context", source_id)
        context_id_2 = lex_db_integrator.add_context("context", source_id)
        assert context_id_1 == context_id_2

    def test_get_context_id_invalid_context(self, lex_db_integrator):
        assert lex_db_integrator.get_context_id("invalid_context", -1) == -1

    def test_get_context_id_valid_context(self, lex_db_integrator):
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        lex_db_integrator.add_context("context", source_id)
        assert lex_db_integrator.get_context_id("context", source_id) != -1

    def test_get_context_invalid_context_id(self, lex_db_integrator):
        assert lex_db_integrator.get_context(-1) is None

    def test_get_context_valid_context_id(self, lex_db_integrator):
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        context_id = lex_db_integrator.add_context("context", source_id)
        assert lex_db_integrator.get_context(context_id) is not None

    def test_add_lemma_context_invalid_ids(self, lex_db_integrator):
        assert lex_db_integrator.add_lemma_context(-1, -1, "NOUN", "NNP") == -1

    def test_add_lemma_context_valid_ids(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lemma_id = lex_db_integrator.add_lemma("test-lemma", status_id)
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        context_id = lex_db_integrator.add_context("context", source_id)
        assert (
            lex_db_integrator.add_lemma_context(
                lemma_id, context_id, "NOUN", "NNP"
            )
            != -1
        )

    def test_get_lemmata_context_ids_invalid_ids(self, lex_db_integrator):
        assert (
            lex_db_integrator.get_lemma_context_ids(-1, -1, "NOUN", "NNP")
            == []
        )

    def test_get_lemmata_context_ids_valid_ids(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lemma_id = lex_db_integrator.add_lemma("test-lemma", status_id)
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        context_id = lex_db_integrator.add_context("context", source_id)
        lex_db_integrator.add_lemma_context(
            lemma_id, context_id, "NOUN", "NNP"
        )
        lex_db_integrator.add_lemma_context(
            lemma_id, context_id, "NOUN", "NNP"
        )
        assert (
            len(
                lex_db_integrator.get_lemma_context_ids(
                    lemma_id, context_id, "NOUN", "NNP"
                )
            )
            == 2
        )

    def test_change_lemma_status_invalid_ids(self, lex_db_integrator):
        assert lex_db_integrator.change_lemma_status(-1, -1) is False

    def test_change_lemma_status_valid_ids(self, lex_db_integrator):
        old_status_id = lex_db_integrator.add_status("pending")
        lex_db_integrator.add_status("accepted")
        lemma_id = lex_db_integrator.add_lemma("test_lemma", old_status_id)
        assert lex_db_integrator.change_lemma_status(lemma_id, "accepted")

    def test_change_lemma_context_upos_tag_invalid_ids(
        self, lex_db_integrator
    ):
        assert (
            lex_db_integrator.change_lemma_context_upos_tag(-1, "NOUN")
            is False
        )

    def test_change_lemma_context_upos_tag_valid_ids(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lemma_id = lex_db_integrator.add_lemma("test-lemma", status_id)
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        context_id = lex_db_integrator.add_context("context", source_id)
        lemma_context_id = lex_db_integrator.add_lemma_context(
            lemma_id, context_id, "NOUN", "NNP"
        )
        assert lex_db_integrator.change_lemma_context_upos_tag(
            lemma_context_id, "VERB"
        )
        assert (
            lex_db_integrator.get_lemma_context(lemma_context_id)[3] == "VERB"
        )

    def test_get_lemma_context(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lemma_id = lex_db_integrator.add_lemma("test-lemma", status_id)
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        context_id = lex_db_integrator.add_context("context", source_id)
        lemma_context_id = lex_db_integrator.add_lemma_context(
            lemma_id, context_id, "NOUN", "NNP"
        )
        assert lex_db_integrator.get_lemma_context(lemma_context_id)[1:] == (
            lemma_id,
            context_id,
            "NOUN",
            "NNP",
        )
        assert lex_db_integrator.get_lemma_context(-1) is None

    def test_get_lemma_contexts(self, lex_db_integrator):
        status_id = lex_db_integrator.add_status("pending")
        lemma_id = lex_db_integrator.add_lemma("test-lemma", status_id)
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id = lex_db_integrator.add_source("The Hobbit", source_kind_id)
        context_id = lex_db_integrator.add_context("context", source_id)
        lemma_context_id = lex_db_integrator.add_lemma_context(
            lemma_id, context_id, "NOUN", "NNP"
        )
        assert (
            lex_db_integrator.get_lemma_contexts(lemma_id)[0][0]
            == lemma_context_id
        )

    def test_delete_lemma_invalid_id(self, lex_db_integrator):
        assert lex_db_integrator.delete_lemma(-1) is False
        # set up the test scenario described above
        status_id = lex_db_integrator.add_status("pending")
        lemma_id_delete = lex_db_integrator.add_lemma("test-lemma", status_id)
        lemma_id_remain = lex_db_integrator.add_lemma(
            "remain-lemma", status_id
        )
        source_kind_id = lex_db_integrator.add_source_kind("book")
        source_id_delete = lex_db_integrator.add_source(
            "The Hobbit", source_kind_id
        )
        source_id_remain = lex_db_integrator.add_source(
            "The Lord of the Rings", source_kind_id
        )
        context_id_delete = lex_db_integrator.add_context(
            "context", source_id_delete
        )
        context_id_remain = lex_db_integrator.add_context(
            f"context-remain::{lemma_id_delete}::{lemma_id_remain}",
            source_id_remain,
        )
        lex_db_integrator.add_lemmata_source(lemma_id_delete, source_id_delete)
        lex_db_integrator.add_lemmata_source(lemma_id_delete, source_id_remain)
        lex_db_integrator.add_lemmata_source(lemma_id_remain, source_id_remain)
        lex_db_integrator.add_lemma_context(
            lemma_id_delete, context_id_delete, "NOUN", "NNP"
        )
        lex_db_integrator.add_lemma_context(
            lemma_id_delete, context_id_remain, "NOUN", "NNP"
        )
        lex_db_integrator.add_lemma_context(
            lemma_id_remain, context_id_remain, "NOUN", "NNP"
        )
        assert lex_db_integrator.delete_lemma(lemma_id_delete) is True
        assert len(lex_db_integrator.get_lemma_sources(lemma_id_delete)) == 0
        assert len(lex_db_integrator.get_lemma_contexts(lemma_id_delete)) == 0
        assert str(lemma_id_delete) not in lex_db_integrator.get_context(
            context_id_remain
        )
        assert str(lemma_id_remain) in lex_db_integrator.get_context(
            context_id_remain
        )
        assert lex_db_integrator.get_lemma(lemma_id_delete) is None
