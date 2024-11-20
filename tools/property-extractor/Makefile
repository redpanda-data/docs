.PHONY: build venv clean redpanda-git generate-docs tags
.SILENT: build venv clean redpanda-git generate-docs tags

TAG ?= dev

build: venv redpanda-git
	mkdir -p gen
	. ./tmp/redpanda-property-extractor-venv/bin/activate; ./property_extractor.py --recursive --path ./tmp/redpanda --verbose --output gen/properties-output.json
	@echo "File generated at ./gen/properties-output.json"
	$(MAKE) generate-docs

venv: requirements.txt
	python3 -m venv ./tmp/redpanda-property-extractor-venv
	. ./tmp/redpanda-property-extractor-venv/bin/activate; pip3 install --no-cache-dir -r requirements.txt

clean:
	rm -rf ./tmp/redpanda-property-extractor-venv ./output

redpanda-git:
	if [ -d "./tmp/redpanda" ]; then \
		cd ./tmp/redpanda && git fetch --tags -q; \
		if [ -z "$(TAG)" ]; then \
			echo "TAG is empty, using default branch 'dev'"; \
			git checkout dev -q && git pull -q; \
		else \
			echo "TAG is set to $(TAG), checking out and pulling"; \
			git checkout $(TAG) -q && git pull -q; \
		fi; \
		git reflog -1; \
	else \
		echo "Cloning repository"; \
		mkdir -p ./tmp/redpanda; \
		if [ -z "$(TAG)" ]; then \
			echo "TAG is empty, using default branch 'dev'"; \
			git clone -q https://github.com/redpanda-data/redpanda.git ./tmp/redpanda --branch dev; \
		else \
			echo "Cloning repository with branch $(TAG)"; \
			git clone -q https://github.com/redpanda-data/redpanda.git ./tmp/redpanda --branch $(TAG); \
		fi; \
		git reflog -1; \
	fi

generate-docs:
	@echo "Generating documentation from properties JSON..."
	. ./tmp/redpanda-property-extractor-venv/bin/activate; python3 json-to-asciidoc/generate_docs.py
	@echo "Documentation generated successfully in ./output/pages/"
