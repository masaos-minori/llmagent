"""scripts/rag/stages/augment.py

Augment stage for RAG pipeline."""

from rag.repository import RagHit
from rag.stage import PipelineContext, PipelineStage
from rag.utils import sanitize_document

_RAG_BLOCK_START = "[RAG_CONTEXT_START]"
_RAG_BLOCK_END = "[RAG_CONTEXT_END]"


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__format_chunks__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__format_chunks__mutmut)
def _format_chunks(reranked: list[RagHit]) -> str:
    """Format reranked hits with sanitization and boundary markers."""
    if not reranked:
        return f"{_RAG_BLOCK_START}\n\n{_RAG_BLOCK_END}"
    blocks = [
        f"[Source: {c.title if c.title else c.url} | {c.url}]\n{sanitize_document(c.content)}"
        for c in reranked
    ]
    content = "\n\n---\n\n".join(blocks)
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"


def x__format_chunks__mutmut_orig(reranked: list[RagHit]) -> str:
    """Format reranked hits with sanitization and boundary markers."""
    if not reranked:
        return f"{_RAG_BLOCK_START}\n\n{_RAG_BLOCK_END}"
    blocks = [
        f"[Source: {c.title if c.title else c.url} | {c.url}]\n{sanitize_document(c.content)}"
        for c in reranked
    ]
    content = "\n\n---\n\n".join(blocks)
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"


def x__format_chunks__mutmut_1(reranked: list[RagHit]) -> str:
    """Format reranked hits with sanitization and boundary markers."""
    if reranked:
        return f"{_RAG_BLOCK_START}\n\n{_RAG_BLOCK_END}"
    blocks = [
        f"[Source: {c.title if c.title else c.url} | {c.url}]\n{sanitize_document(c.content)}"
        for c in reranked
    ]
    content = "\n\n---\n\n".join(blocks)
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"


def x__format_chunks__mutmut_2(reranked: list[RagHit]) -> str:
    """Format reranked hits with sanitization and boundary markers."""
    if not reranked:
        return f"{_RAG_BLOCK_START}\n\n{_RAG_BLOCK_END}"
    blocks = None
    content = "\n\n---\n\n".join(blocks)
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"


def x__format_chunks__mutmut_3(reranked: list[RagHit]) -> str:
    """Format reranked hits with sanitization and boundary markers."""
    if not reranked:
        return f"{_RAG_BLOCK_START}\n\n{_RAG_BLOCK_END}"
    blocks = [
        f"[Source: {c.title if c.title else c.url} | {c.url}]\n{sanitize_document(None)}"
        for c in reranked
    ]
    content = "\n\n---\n\n".join(blocks)
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"


def x__format_chunks__mutmut_4(reranked: list[RagHit]) -> str:
    """Format reranked hits with sanitization and boundary markers."""
    if not reranked:
        return f"{_RAG_BLOCK_START}\n\n{_RAG_BLOCK_END}"
    blocks = [
        f"[Source: {c.title if c.title else c.url} | {c.url}]\n{sanitize_document(c.content)}"
        for c in reranked
    ]
    content = None
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"


def x__format_chunks__mutmut_5(reranked: list[RagHit]) -> str:
    """Format reranked hits with sanitization and boundary markers."""
    if not reranked:
        return f"{_RAG_BLOCK_START}\n\n{_RAG_BLOCK_END}"
    blocks = [
        f"[Source: {c.title if c.title else c.url} | {c.url}]\n{sanitize_document(c.content)}"
        for c in reranked
    ]
    content = "\n\n---\n\n".join(None)
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"


def x__format_chunks__mutmut_6(reranked: list[RagHit]) -> str:
    """Format reranked hits with sanitization and boundary markers."""
    if not reranked:
        return f"{_RAG_BLOCK_START}\n\n{_RAG_BLOCK_END}"
    blocks = [
        f"[Source: {c.title if c.title else c.url} | {c.url}]\n{sanitize_document(c.content)}"
        for c in reranked
    ]
    content = "XX\n\n---\n\nXX".join(blocks)
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"

mutants_x__format_chunks__mutmut['_mutmut_orig'] = x__format_chunks__mutmut_orig # type: ignore # mutmut generated
mutants_x__format_chunks__mutmut['x__format_chunks__mutmut_1'] = x__format_chunks__mutmut_1 # type: ignore # mutmut generated
mutants_x__format_chunks__mutmut['x__format_chunks__mutmut_2'] = x__format_chunks__mutmut_2 # type: ignore # mutmut generated
mutants_x__format_chunks__mutmut['x__format_chunks__mutmut_3'] = x__format_chunks__mutmut_3 # type: ignore # mutmut generated
mutants_x__format_chunks__mutmut['x__format_chunks__mutmut_4'] = x__format_chunks__mutmut_4 # type: ignore # mutmut generated
mutants_x__format_chunks__mutmut['x__format_chunks__mutmut_5'] = x__format_chunks__mutmut_5 # type: ignore # mutmut generated
mutants_x__format_chunks__mutmut['x__format_chunks__mutmut_6'] = x__format_chunks__mutmut_6 # type: ignore # mutmut generated
mutants_xǁAugmentStageǁrun__mutmut: MutantDict = {}  # type: ignore


class AugmentStage(PipelineStage):
    """Text augmentation stage that formats reranked chunks into RAG context blocks."""

    @_mutmut_mutated(mutants_xǁAugmentStageǁrun__mutmut)
    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Format reranked chunks into a RAG context block and store in context."""
        ctx.augment_result = _format_chunks(ctx.reranked)

    async def xǁAugmentStageǁrun__mutmut_orig(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Format reranked chunks into a RAG context block and store in context."""
        ctx.augment_result = _format_chunks(ctx.reranked)

    async def xǁAugmentStageǁrun__mutmut_1(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Format reranked chunks into a RAG context block and store in context."""
        ctx.augment_result = None

    async def xǁAugmentStageǁrun__mutmut_2(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Format reranked chunks into a RAG context block and store in context."""
        ctx.augment_result = _format_chunks(None)

mutants_xǁAugmentStageǁrun__mutmut['_mutmut_orig'] = AugmentStage.xǁAugmentStageǁrun__mutmut_orig # type: ignore # mutmut generated
mutants_xǁAugmentStageǁrun__mutmut['xǁAugmentStageǁrun__mutmut_1'] = AugmentStage.xǁAugmentStageǁrun__mutmut_1 # type: ignore # mutmut generated
mutants_xǁAugmentStageǁrun__mutmut['xǁAugmentStageǁrun__mutmut_2'] = AugmentStage.xǁAugmentStageǁrun__mutmut_2 # type: ignore # mutmut generated
