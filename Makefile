.PHONY: all data metrics analysis figures

all: analysis figures

data:
	bash data/download.sh

metrics:
	python -m metrics.layer build

analysis:
	python -m analysis.run_all

figures:
	python -m analysis.figures
