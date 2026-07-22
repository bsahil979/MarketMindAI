from typing import List, Dict, Any

class FinancialPromptBuilder:
    """
    Prompt template builder for Portfolio Advisor AI Financial RAG.
    Enforces strict grounding, citation of financial figures, and zero hallucination.
    """

    SYSTEM_PROMPT = """You are Portfolio Advisor AI, an expert quantitative financial analyst assistant.
Your job is to answer the user's financial question strictly using ONLY the provided financial context snippets below.

Rules:
1. Grounding: Rely strictly on facts, table numbers, and statements in the context. Do not invent or extrapolate figures.
2. Citation: Include relevant table rows or text citations from the context when reporting financial numbers.
3. Unanswered Queries: If the provided context does not contain sufficient evidence to answer the question, respond: "Based on the retrieved financial documents, there is insufficient evidence to answer this question."
4. Formatting: Present key metrics clearly in bold or bulleted format.
"""

    def build_prompt(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Formats system instructions, retrieved context passages, and user query into a grounded prompt string.
        """
        context_blocks = []
        for idx, chunk in enumerate(context_chunks, start=1):
            meta = chunk.get("metadata", {})
            ticker = meta.get("ticker", "N/A")
            doc_type = meta.get("document_type", "N/A")
            c_id = chunk.get("chunk_id", f"chunk_{idx}")

            block = f"[Context #{idx} | {ticker} {doc_type} | ID: {c_id}]\n{chunk['text']}"
            context_blocks.append(block)

        formatted_context = "\n\n-------------------------\n\n".join(context_blocks)

        prompt = f"""{self.SYSTEM_PROMPT}

=== RETRIEVED FINANCIAL CONTEXT ===
{formatted_context}
===================================

USER FINANCIAL QUESTION:
{query}

PORTFOLIO ADVISOR AI RESPONSE:
"""
        return prompt

if __name__ == "__main__":
    pb = FinancialPromptBuilder()
    print("FinancialPromptBuilder ready.")
