.PHONY: features trained-model scores evaluation test clean-pyc clean-env 

# Create a virtual environment named pennylane-env
pennylane-env/bin/activate: requirements.txt
	test -d pennylane-env || virtualenv pennylane-env
	. pennylane-env/bin/activate; pip install -r requirements.txt
	touch pennylane-env/bin/activate

venv: pennylane-env/bin/activate

# Below are for reproducing feature generation, modeling, scoring, evaluation and post-process
data/bank_processed.csv: src/generate_features.py 
	python run.py generate_features --config=config/config.yaml --output=data/bank_processed.csv
features: data/bank_processed.csv


models/bank-prediction.pkl: data/bank_processed.csv src/train_model.py
	python run.py train_model --config=config/config.yaml --input=data/bank_processed.csv --output=models/bank-prediction.pkl
train: models/bank-prediction.pkl


models/bank_test_scores.csv: src/score_model.py
	python run.py score_model --config=config/config.yaml
scores: models/bank_test_scores.csv

models/model_evaluation.csv: src/evaluate_model.py
	python run.py evaluate_model --config=config/config.yaml --output=models/model_evaluation.csv
evaluation: models/model_evaluation.csv



data/sample/bank.csv: src/get_data.py
	python run.py get_data --sourceurl=https://value-chain-project-data.s3.us-east-2.amazonaws.com/bank.csv --filename=bank.csv  --savename=data/sample/bank.csv
get_s3_data: data/sample/bank.csv


# Run all tests
test:
	pytest test/test.py

# Clean up things
clean-tests:
	rm -rf .pytest_cache
	rm -r test/model/test/
	mkdir test/model/test
	touch test/model/test/.gitkeep

clean-env:
	rm -r pennylane-env

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	rm -rf .pytest_cache

clean: clean-tests clean-env clean-pyc

all: features train scores evaluation 
