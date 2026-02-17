from __future__ import annotations

"""Prompt templates for RAG"""

RAG_SYSTEM_PROMPT = """You are an AI assistant helping users understand their project documentation.

Your role is to:
- Answer questions based ONLY on the provided context from project documents
- Be accurate and cite specific information from the context
- If the context doesn't contain enough information to answer, say so clearly
- Don't make up information or draw from general knowledge
- Provide clear, concise, and helpful responses

When answering:
1. Focus on the most relevant information from the context
2. Quote specific passages when helpful
3. Explain technical concepts clearly
4. If multiple documents are relevant, synthesize the information
"""


def build_rag_prompt(question: str, context_chunks: list[tuple[str, float]]) -> str:
    """
    Build RAG prompt with question and retrieved context

    Args:
        question: User's question
        context_chunks: List of (content, similarity_score) tuples

    Returns:
        Formatted prompt for LLM
    """
    # Build context section
    context_parts = []
    for i, (content, score) in enumerate(context_chunks, 1):
        context_parts.append(
            f"[Document {i}] (Relevance: {score:.2%})\n{content}\n"
        )

    context = "\n---\n".join(context_parts)

    prompt = f"""{RAG_SYSTEM_PROMPT}

CONTEXT FROM PROJECT DOCUMENTS:
{context}

---

USER QUESTION:
{question}

Please provide a detailed answer based on the context above. If the context doesn't contain enough information to answer the question, clearly state that.
"""

    return prompt


COPILOT_SYSTEM_PROMPT = """You are an AI project management copilot for ProjectForge.

Your role is to:
- Analyze project data and provide insights
- Identify risks and potential issues
- Suggest improvements to project planning
- Help with timeline predictions
- Provide actionable recommendations

Be:
- Data-driven: Base insights on actual project metrics
- Proactive: Identify issues before they become critical
- Practical: Provide actionable suggestions
- Clear: Explain your reasoning
"""


def build_risk_analysis_prompt(project_data: dict) -> str:
    """Build prompt for risk analysis"""
    return f"""{COPILOT_SYSTEM_PROMPT}

Analyze the following project data and identify potential risks:

PROJECT DATA:
{project_data}

Provide a risk analysis with:
1. Identified risks (with severity: high/medium/low)
2. Impact assessment for each risk
3. Recommended mitigation strategies
4. Priority actions

Format your response as a structured analysis.
"""


def build_timeline_prediction_prompt(project_data: dict, historical_data: dict) -> str:
    """Build prompt for timeline prediction"""
    return f"""{COPILOT_SYSTEM_PROMPT}

Predict project timeline based on current progress and historical data:

CURRENT PROJECT:
{project_data}

HISTORICAL DATA:
{historical_data}

Provide:
1. Estimated completion date
2. Confidence level (high/medium/low)
3. Key assumptions
4. Factors that could affect the timeline
5. Recommendations for staying on track

Be realistic and data-driven in your predictions.
"""
