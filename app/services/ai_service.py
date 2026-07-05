from flask import current_app


class AIService:
    """Talks to Otari for all AI features."""

    @staticmethod
    def chat(system_prompt, user_prompt, temperature=0.3):
        """
        Send a chat request to Otari and return the assistant's text reply.
        """
        api_key = current_app.config.get("OTARI_API_KEY")
        if not api_key:
            raise ValueError(
                "OTARI_API_KEY is not set. "
                "Add it to your .env file (get a free key at otari.ai)."
            )

        model = current_app.config["OTARI_MODEL"]

        try:
            from otari import OtariClient
        except ImportError as exc:
            raise ImportError(
                "Install the Otari SDK: pip install otari"
            ) from exc

        client = OtariClient(platform_token=api_key)

        try:
            response = client.completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
        except Exception as exc:
            raise RuntimeError(
                AIService._format_error(exc, model)
            ) from exc

        return response.choices[0].message.content

    @staticmethod
    def _format_error(exc, model):
        msg = str(exc)

        if "404" in msg or "not found" in msg.lower():
            return (
                f"Otari could not find model '{model}'.\n\n"
                "Fix:\n"
                "1. Open https://otari.ai → your workspace → Models tab\n"
                "2. Pick a model that shows as available (managed models start with mzai:)\n"
                "3. Copy the exact name into .env → OTARI_MODEL=...\n"
                "4. Restart Python and try again\n\n"
                "Example: OTARI_MODEL=mzai:moonshotai/Kimi-K2.6\n\n"
                f"Original error: {msg}"
            )

        if "401" in msg or "403" in msg or "unauthorized" in msg.lower():
            return (
                "Otari rejected your API key.\n\n"
                "Fix:\n"
                "1. Open https://otari.ai → API Keys tab → Generate new key\n"
                "2. Key must start with tk_\n"
                "3. Paste into .env → OTARI_API_KEY=tk_...\n\n"
                f"Original error: {msg}"
            )

        return (
            f"Otari request failed.\n\n"
            f"Model used: {model}\n"
            f"Error: {msg}\n\n"
            "Check your otari.ai dashboard: wallet credits, Models tab, API key."
        )
