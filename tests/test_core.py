from unittest.mock import MagicMock, patch

import pytest

from rag.core import ask_question, chunk_text, search_documents


def test_chunks_split_on_length():
    chunks = chunk_text("mot " * 300, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk.split()) <= 100 for chunk in chunks)


def test_chunks_overlap_so_a_passage_is_not_cut_in_half():
    words = " ".join(str(n) for n in range(100))

    first, second = chunk_text(words, chunk_size=50, overlap=10)[:2]

    assert second.split()[:10] == first.split()[-10:]


def test_chunks_cover_the_whole_text():
    words = " ".join(str(n) for n in range(250))

    covered = " ".join(chunk_text(words, chunk_size=50, overlap=10)).split()

    assert "0" in covered
    assert "249" in covered


def test_text_shorter_than_a_chunk_gives_one_chunk():
    assert chunk_text("trois petits mots", chunk_size=100) == ["trois petits mots"]


def test_empty_text_gives_no_chunks():
    assert chunk_text("") == []


def test_whitespace_only_text_gives_no_chunks():
    assert chunk_text("   \n  \t ") == []


def _mock_collection(documents, sources, distances):
    collection = MagicMock()
    collection.query.return_value = {
        "documents": [documents],
        "metadatas": [[{"source": source} for source in sources]],
        "distances": [distances],
    }
    return collection


def _mock_llm(content):
    response = MagicMock()
    response.choices[0].message.content = content
    llm = MagicMock()
    llm.chat.completions.create.return_value = response
    return llm


def test_search_turns_distance_into_a_similarity_score():
    collection = _mock_collection(["un passage"], ["guide.pdf"], [0.25])

    with (
        patch("rag.core._get_collection", return_value=collection),
        patch("rag.core._get_embedder", return_value=MagicMock()),
    ):
        results = search_documents("question")

    assert results[0]["score"] == 0.75
    assert results[0]["source"] == "guide.pdf"


def test_answer_lists_each_source_once():
    collection = _mock_collection(
        ["a", "b", "c"],
        ["guide.pdf", "guide.pdf", "contrat.pdf"],
        [0.1, 0.2, 0.3],
    )

    with (
        patch("rag.core._get_collection", return_value=collection),
        patch("rag.core._get_embedder", return_value=MagicMock()),
        patch("rag.core._get_llm", return_value=_mock_llm("La réponse.")),
    ):
        result = ask_question("question")

    assert result["sources"] == ["contrat.pdf", "guide.pdf"]
    assert result["chunks_used"] == 3


def test_the_retrieved_passages_are_put_in_front_of_the_model():
    collection = _mock_collection(["le prix est de 12 euros"], ["tarifs.pdf"], [0.1])
    llm = _mock_llm("12 euros [tarifs.pdf]")

    with (
        patch("rag.core._get_collection", return_value=collection),
        patch("rag.core._get_embedder", return_value=MagicMock()),
        patch("rag.core._get_llm", return_value=llm),
    ):
        ask_question("quel prix ?")

    sent = llm.chat.completions.create.call_args.kwargs["messages"][-1]["content"]
    assert "le prix est de 12 euros" in sent
    assert "tarifs.pdf" in sent


def test_empty_answer_raises():
    collection = _mock_collection(["a"], ["guide.pdf"], [0.1])

    with (
        patch("rag.core._get_collection", return_value=collection),
        patch("rag.core._get_embedder", return_value=MagicMock()),
        patch("rag.core._get_llm", return_value=_mock_llm(None)),
        pytest.raises(ValueError, match="aucune réponse"),
    ):
        ask_question("question")
