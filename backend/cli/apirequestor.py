from typing import Union

import requests

from ..api._const import Const
from ..api._dbtypes import (
    Context,
    ContextId,
    Lemma,
    LemmaContextId,
    LemmaContextRelation,
    LemmaId,
    LemmaList,
    LemmaSourceId,
    LemmaSourceRelation,
    Source,
    SourceId,
    SourceKindId,
    SourceKindVal,
    StatusId,
    StatusVal,
    UposTag,
)
from ..api.index import LemmaValue


class ApiRequestor:
    """
    Encapsulation class for sending HTTP requests to the api.

    Connects with local API.
    """

    def __init__(self) -> None:
        self.api_url = Const.API_LOCAL_URL

    def get_lemma_name(self, lemma_id: LemmaId) -> str:
        r = requests.get(f"{self.api_url}/lemma/{lemma_id}")
        return Lemma(**dict(r.json())).lemma if r.status_code == 200 else ""

    def get_lemma_id(self, lemma: str) -> LemmaId:
        r = requests.get(
            f"{self.api_url}/lemma_id", json=LemmaValue(value=lemma).dict()
        )
        return LemmaId(r.json()) if r.status_code == 200 else LemmaId(-1)

    def get_lemma_status(self, status_val: StatusVal) -> StatusId:
        r = requests.get(f"{self.api_url}/lemma_status/{status_val.value}")
        assert r.status_code == 200
        return StatusId(r.json())

    def get_status_lemmata(
        self,
        status_val: StatusVal,
        page: Union[int, None] = None,
        page_size: Union[int, None] = None,
        table: bool = False,
    ) -> str:
        query_params = {}
        # Add page and page_size query params if provided
        if page:
            query_params["page"] = page
        if page_size:
            query_params["page_size"] = page_size
        query_params["status_val"] = status_val.value
        r = requests.get(
            f"{self.api_url}/status_lemmata{'_table' if table else ''}",
            params=query_params,
        )
        assert r.status_code == 200
        return r.json()

    def post_lemma(
        self, lemma: str, status_id: StatusId, source_id: SourceId
    ) -> LemmaId:
        r = requests.post(
            f"{self.api_url}/lemma",
            json=Lemma(
                lemma=lemma, status_id=status_id, found_in_source=source_id
            ).to_dict(),
        )
        assert r.status_code == 200
        assert (lid := LemmaId(r.json())) != -1
        return lid

    def bulk_post_lemmata(
        self,
        lemmata_values: list[LemmaValue],
        status_id: StatusId,
        source_id: SourceId,
    ) -> dict[LemmaValue, LemmaId]:
        print(
            LemmaList(
                lemmata=[
                    Lemma(
                        lemma=lemma_val,
                        status_id=status_id,
                        found_in_source=source_id,
                    )
                    for lemma_val in lemmata_values
                ]
            ).to_dict()
        )
        r = requests.post(
            f"{self.api_url}/bulk_lemmata",
            json={
                LemmaList(
                    lemmata=[
                        Lemma(
                            lemma=lemma_val,
                            status_id=status_id,
                            found_in_source=source_id,
                        )
                        for lemma_val in lemmata_values
                    ]
                ).to_dict(),
            },
        )
        assert r.status_code == 200
        id_lemma_dict: dict[LemmaValue, LemmaId] = r.json()
        assert set(lemmata_values) == id_lemma_dict.keys()
        return id_lemma_dict

    def post_status(self, status_val: StatusVal) -> StatusId:
        r = requests.post(
            f"{self.api_url}/lemma_status?status_val={status_val.value}",
        )
        assert r.status_code == 200
        assert (sid := StatusId(r.json())) != -1
        return sid

    def post_source_kind(self, source_kind_val: SourceKindVal) -> SourceKindId:
        r = requests.post(
            f"{self.api_url}/source_kind?source_kind_val={source_kind_val.value}",
        )
        assert r.status_code == 200
        assert (skid := SourceKindId(r.json())) != -1
        return skid

    def post_source(
        self, title: str, source_kind_id: SourceKindId, author: str, lang: str
    ) -> SourceId:
        r = requests.post(
            f"{self.api_url}/source",
            json=Source(
                title=title,
                source_kind_id=source_kind_id,
                author=author,
                lang=lang,
            ).to_dict(),
        )
        assert r.status_code == 200
        assert (sid := SourceId(r.json())) != -1
        return sid

    def post_context(
        self, context_value: str, source_id: SourceId
    ) -> ContextId:
        r = requests.post(
            f"{self.api_url}/context",
            json=Context(
                context_value=context_value, source_id=source_id
            ).to_dict(),
        )
        assert r.status_code == 200
        assert (cid := ContextId(r.json())) != -1
        return cid

    def post_lemma_context_relation(
        self,
        lemma_id: LemmaId,
        context_id: ContextId,
        upos_tag: UposTag,
        detailed_tag: str,
    ) -> LemmaContextId:
        r = requests.post(
            f"{self.api_url}/lemma_context",
            json=LemmaContextRelation(
                lemma_id=lemma_id,
                context_id=context_id,
                upos_tag=upos_tag,
                detailed_tag=detailed_tag,
            ).to_dict(),
        )
        assert r.status_code == 200
        assert (lcid := LemmaContextId(r.json())) != -1
        return lcid

    def post_lemma_source_relation(
        self,
        lemma_id: LemmaId,
        source_id: SourceId,
    ) -> LemmaSourceId:
        r = requests.post(
            f"{self.api_url}/lemma_source",
            json=LemmaSourceRelation(
                lemma_id=lemma_id, source_id=source_id
            ).to_dict(),
        )
        assert r.status_code == 200
        assert (lsid := LemmaSourceId(r.json())) != -1
        return lsid

    def delete_lemmata(self, lemma_ids: set[LemmaId]) -> bool:
        r = requests.delete(f"{self.api_url}/lemma", json=list(lemma_ids))
        assert r.status_code == 200
        return r.json()

    def update_multiple_status(
        self, lemma_ids: set[LemmaId], new_status_id: StatusId
    ) -> bool:
        r = requests.patch(
            f"{self.api_url}/status?new_status_id={new_status_id}",
            json=list(lemma_ids),
        )
        assert r.status_code == 200
        return r.json()
