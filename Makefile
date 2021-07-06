UI_FILES:=$(shell find src -name *.ui)
PY_FILES:=$(UI_FILES:%.ui=%.py)

$(info UI-files: ${UI_FILES})

all: ui
ui: ${PY_FILES}

%.py: %.ui
	pyside6-uic $^ -o $@

clean:
	rm -v ${PY_FILES}

.PHONY: all ui clean
