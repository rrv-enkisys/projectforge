from __future__ import annotations

"""AI Copilot service"""
import json
import logging
from typing import Any
from uuid import UUID

from fastapi import Depends

from ..embeddings.vertex_client import VertexAIClient, get_vertex_client
from ..rag.prompts import build_risk_analysis_prompt, build_timeline_prediction_prompt
from .analyzer import ProjectAnalyzer

logger = logging.getLogger(__name__)


class CopilotService:
    """Service for AI-powered project insights"""

    def __init__(self, vertex_client: VertexAIClient = Depends(get_vertex_client)):
        self.vertex_client = vertex_client
        self.analyzer = ProjectAnalyzer()

    async def analyze_project(self, project_data: dict) -> dict:
        """
        Perform comprehensive project analysis

        Args:
            project_data: Project data including tasks, milestones, etc.

        Returns:
            Complete analysis with health, risks, and predictions
        """
        # Analyze project health
        health = self.analyzer.analyze_project_health(project_data)

        # Detect risks
        risks = self.analyzer.detect_risks(project_data)

        # Predict completion
        prediction = self.analyzer.predict_completion(project_data)

        # Generate AI insights
        insights_prompt = f"""
Analyze this project data and provide actionable insights:

PROJECT DATA:
{json.dumps(project_data, indent=2)}

AUTOMATED ANALYSIS:
- Health Score: {health['score']}/100
- Status: {health['status']}
- Issues: {', '.join(health['issues']) if health['issues'] else 'None'}
- Risks: {len(risks)} detected

Provide:
1. Top 3 priority actions
2. Key observations
3. Recommendations for improvement

Keep it concise and actionable.
"""

        ai_insights = await self.vertex_client.generate_text(
            prompt=insights_prompt,
            temperature=0.5,
            max_output_tokens=512
        )

        return {
            "health": health,
            "risks": risks,
            "completion_prediction": prediction,
            "ai_insights": ai_insights,
            "timestamp": "utcnow"
        }

    async def get_risk_analysis(self, project_data: dict) -> dict:
        """
        Get detailed risk analysis with AI-generated mitigation strategies

        Args:
            project_data: Project data

        Returns:
            Risk analysis with recommendations
        """
        # Detect risks using analyzer
        detected_risks = self.analyzer.detect_risks(project_data)

        # Enhance with AI analysis
        prompt = build_risk_analysis_prompt(project_data)
        ai_analysis = await self.vertex_client.generate_text(
            prompt=prompt,
            temperature=0.4,
            max_output_tokens=1024
        )

        return {
            "detected_risks": detected_risks,
            "ai_analysis": ai_analysis,
            "risk_count": len(detected_risks),
            "severity_breakdown": self._get_severity_breakdown(detected_risks)
        }

    async def get_suggestions(self, project_data: dict) -> list[dict]:
        """
        Get AI-generated suggestions for project improvement

        Args:
            project_data: Project data

        Returns:
            List of actionable suggestions
        """
        prompt = f"""
Based on this project data, suggest specific improvements:

{json.dumps(project_data, indent=2)}

Provide 5 specific, actionable suggestions to improve project outcomes.
Format each as: Category, Action, Expected Impact

Be practical and specific to the project data.
"""

        response = await self.vertex_client.generate_text(
            prompt=prompt,
            temperature=0.6,
            max_output_tokens=800
        )

        # Parse AI response into structured suggestions
        # In a real implementation, you'd use more sophisticated parsing
        suggestions = [
            {
                "category": "General",
                "action": line.strip(),
                "priority": "medium"
            }
            for line in response.split("\n")
            if line.strip() and not line.startswith("#")
        ][:5]

        return suggestions

    async def predict_timeline(
        self,
        project_data: dict,
        historical_data: dict | None = None
    ) -> dict:
        """
        Predict project timeline with AI analysis

        Args:
            project_data: Current project data
            historical_data: Optional historical project data

        Returns:
            Timeline prediction with confidence and factors
        """
        # Get basic prediction from analyzer
        base_prediction = self.analyzer.predict_completion(project_data)

        # Enhance with AI if historical data available
        if historical_data:
            prompt = build_timeline_prediction_prompt(project_data, historical_data)
            ai_prediction = await self.vertex_client.generate_text(
                prompt=prompt,
                temperature=0.3,
                max_output_tokens=512
            )

            return {
                **base_prediction,
                "ai_analysis": ai_prediction,
                "factors": self._extract_timeline_factors(project_data)
            }

        return {
            **base_prediction,
            "factors": self._extract_timeline_factors(project_data)
        }

    def _get_severity_breakdown(self, risks: list[dict]) -> dict:
        """Get count of risks by severity"""
        breakdown = {"high": 0, "medium": 0, "low": 0}
        for risk in risks:
            severity = risk.get("severity", "low")
            breakdown[severity] = breakdown.get(severity, 0) + 1
        return breakdown

    def _extract_timeline_factors(self, project_data: dict) -> list[str]:
        """Extract factors affecting timeline"""
        factors = []

        tasks = project_data.get("tasks", [])
        if tasks:
            blocked_tasks = [t for t in tasks if t.get("status") == "blocked"]
            if blocked_tasks:
                factors.append(f"{len(blocked_tasks)} blocked tasks")

            in_progress = [t for t in tasks if t.get("status") == "in_progress"]
            if len(in_progress) > 10:
                factors.append("High number of concurrent tasks")

        if project_data.get("budget"):
            factors.append("Budget constraints may impact timeline")

        return factors
