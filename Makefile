.PHONY: load ratios test report dashboard api clean

load:
python -m src.etl.loader

ratios:
python -m src.analytics.ratios

test:
pytest -v

report:
python -m src.etl.validator

dashboard:
@echo Dashboard task

api:
@echo API task

clean:
@echo Cleaning temporary files
