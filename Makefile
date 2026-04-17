.PHONY: dev test pipeline seed

dev:
	cmd /c start "FastAPI Server" python -m uvicorn main:app --reload --port 8000
	cmd /c start "Streamlit Dashboard" python -m streamlit run dashboard/app.py

test:
	pytest tests/

pipeline:
	python pipeline/bronze_runner.py
	python pipeline/silver.py
	python pipeline/nlp_enrichment.py
	python pipeline/change_detection.py
	python pipeline/cleanup_guardrail.py

seed:
	python seed/generate_seed.py
