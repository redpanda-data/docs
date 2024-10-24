.PHONY: build venv clean redpanda-git tags
.SILENT: build venv clean redpanda-git tags

TAG ?= dev

build: venv redpanda-git
	mkdir -p gen
	. ./tmp/redpanda-property-extractor-venv/bin/activate; ./property_extractor.py --recursive --path ./tmp/redpanda --output gen/properties-output.json
	@echo "File generated at ./gen/properties-output.json"

venv: requirements.txt
	python3 -m venv ./tmp/redpanda-property-extractor-venv
	. ./tmp/redpanda-property-extractor-venv/bin/activate; pip install --no-cache-dir -r requirements.txt

clean:
	rm -rf ./tmp/redpanda-property-extractor-venv

redpanda-git:
	if [ -d "./tmp/redpanda" ]; then \
		cd ./tmp/redpanda && git fetch --tags -q; \
		if [ -z "$$TAG" ]; then \
			echo "TAG is empty, pulling from dev"; \
			git checkout dev -q && git pull -q; \
		else \
			echo "TAG is set to $$TAG, checking out and pulling"; \
			git checkout $$TAG -q && git pull -q; \
		fi; \
		git reflog -1; \
	else \
		echo "Cloning repository with branch $$TAG"; \
		git clone -q https://github.com/redpanda-data/redpanda.git ./tmp/redpanda --branch $$TAG; \
		git reflog -1; \
	fi