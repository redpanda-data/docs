.PHONY: build venv clean redpanda-git generate-docs tags treesitter
.SILENT: build venv clean redpanda-git generate-docs tags treesitter

# Default TAG if none is provided
TAG ?= dev

# Determine the version number from TAG.
# If TAG matches a version pattern (e.g., v25.1.1 or v25.1.1-rc3), extract the major.minor and optional RC number.
# Otherwise, use TAG as-is.
VERSION := $(shell \
  if echo "$(TAG)" | grep -qE '^v?[0-9]+\.[0-9]+' ; then \
    echo "$(TAG)" | sed -E 's/^v?([0-9]+\.[0-9]+)(\.[0-9]+)?(-rc[0-9]+)?.*/\1\3/' | sed 's/-rc/rc/'; \
  else \
    echo "$(TAG)"; \
  fi)

# Paths
TREESITTER_DIR := tools/property-extractor/tree-sitter/tree-sitter-cpp
TREESITTER_LIB := $(TREESITTER_DIR)/tree-sitter-cpp.so
VENV := ./tmp/redpanda-property-extractor-venv
REPO_ROOT := $(shell git rev-parse --show-toplevel)
OUTPUT_DIR := $(REPO_ROOT)/gen/$(VERSION)/properties


# --- Main Build Target ---
build: venv redpanda-git treesitter
	mkdir -p gen
	. $(VENV)/bin/activate; \
		./property_extractor.py --recursive --path ./tmp/redpanda --verbose --output gen/properties-output.json
	@echo "File generated at ./gen/properties-output.json"
	$(MAKE) generate-docs

# --- Ensure Virtual Environment Exists ---
venv: requirements.txt
	if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV); \
		. $(VENV)/bin/activate; \
		pip install --no-cache-dir -r requirements.txt; \
	else \
		echo "Virtual environment already exists."; \
	fi

# --- Clean Up Temporary Files ---
clean:
	rm -rf $(VENV) ./output ./gen ./output/pages/

# --- Clone & Update Redpanda Repo ---
redpanda-git:
	if [ -d "./tmp/redpanda" ]; then \
		cd ./tmp/redpanda && git fetch --tags -q; \
		if [ -z "$(TAG)" ]; then \
			echo "Using default branch 'dev'"; \
			git checkout dev -q && git pull -q; \
		else \
			echo "Checking out $(TAG)"; \
			git checkout $(TAG) -q 2>/dev/null || git checkout tags/$(TAG) -q; \
			git pull -q || true; \
		fi; \
		git reflog -1; \
	else \
		echo "Cloning Redpanda repository..."; \
		mkdir -p ./tmp/redpanda; \
		git clone -q https://github.com/redpanda-data/redpanda.git ./tmp/redpanda; \
		cd ./tmp/redpanda && git checkout $(TAG) -q 2>/dev/null || git checkout tags/$(TAG) -q; \
		git reflog -1; \
	fi

# --- Initialize and Build Tree-sitter C++ Parser ---
treesitter:
	if [ ! -d "$(TREESITTER_DIR)/src" ]; then \
		echo "Initializing Tree-sitter submodule..."; \
		(cd $(REPO_ROOT) && git submodule update --init --recursive); \
		echo "Tree-sitter C++ parser built successfully."; \
	else \
		echo "Tree-sitter C++ parser already built."; \
	fi

# --- Generate Documentation ---
generate-docs:
	@echo "Generating documentation from properties JSON..."
	mkdir -p $(OUTPUT_DIR)  # Ensure the output directory exists
	. $(VENV)/bin/activate; \
		python3 json-to-asciidoc/generate_docs.py --output-dir $(OUTPUT_DIR)
	@echo "Documentation generated successfully in $(OUTPUT_DIR)"